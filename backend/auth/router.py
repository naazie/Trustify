from datetime import datetime

import httpx
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr

from auth.utils import hash_password, verify_password, create_token, get_db
from config import settings

router = APIRouter()

GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO  = "https://www.googleapis.com/oauth2/v3/userinfo"


# ── Pydantic schemas ──────────────────────────────────────────────────────────
class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def _user_response(user: dict, token: str) -> dict:
    return {
        "token": token,
        "user": {
            "id":     str(user["_id"]),
            "name":   user.get("name", ""),
            "email":  user["email"],
            "avatar": user.get("avatar"),
        },
    }


# ── Email / password signup ───────────────────────────────────────────────────
@router.post("/signup")
async def signup(body: SignupRequest, db=Depends(get_db)):
    if await db.users.find_one({"email": body.email}):
        raise HTTPException(400, "Email already registered")
    result = await db.users.insert_one({
        "name":       body.name,
        "email":      body.email,
        "password":   hash_password(body.password),
        "provider":   "email",
        "created_at": datetime.utcnow(),
    })
    user = await db.users.find_one({"_id": result.inserted_id})
    return _user_response(user, create_token(str(result.inserted_id), body.email))


# ── Email / password login ────────────────────────────────────────────────────
@router.post("/login")
async def login(body: LoginRequest, db=Depends(get_db)):
    user = await db.users.find_one({"email": body.email})
    if not user or not verify_password(body.password, user.get("password", "")):
        raise HTTPException(401, "Invalid email or password")
    return _user_response(user, create_token(str(user["_id"]), body.email))


# ── Google OAuth — redirect to Google ────────────────────────────────────────
@router.get("/google")
async def google_login():
    if not settings.google_client_id:
        raise HTTPException(501, "Google OAuth not configured")
    params = (
        f"?client_id={settings.google_client_id}"
        f"&redirect_uri={settings.frontend_url.rstrip('/')}/api/auth/google/callback"
        f"&response_type=code&scope=openid%20email%20profile&access_type=offline"
    )
    return RedirectResponse(GOOGLE_AUTH_URL + params)


# ── Google OAuth — callback ───────────────────────────────────────────────────
@router.get("/google/callback")
async def google_callback(code: str, db=Depends(get_db)):
    redirect_uri = f"{settings.frontend_url.rstrip('/')}/api/auth/google/callback"
    async with httpx.AsyncClient() as client:
        # Exchange code for tokens
        token_resp = await client.post(GOOGLE_TOKEN_URL, data={
            "code":          code,
            "client_id":     settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri":  redirect_uri,
            "grant_type":    "authorization_code",
        })
        token_resp.raise_for_status()
        access_token = token_resp.json()["access_token"]

        # Fetch user info
        info_resp = await client.get(GOOGLE_USERINFO, headers={"Authorization": f"Bearer {access_token}"})
        info_resp.raise_for_status()
        info = info_resp.json()

    email  = info["email"]
    name   = info.get("name", email.split("@")[0])
    avatar = info.get("picture")

    user = await db.users.find_one({"email": email})
    if not user:
        result = await db.users.insert_one({
            "name":       name,
            "email":      email,
            "avatar":     avatar,
            "provider":   "google",
            "created_at": datetime.utcnow(),
        })
        user = await db.users.find_one({"_id": result.inserted_id})
    else:
        await db.users.update_one({"_id": user["_id"]}, {"$set": {"avatar": avatar, "name": name}})
        user["avatar"] = avatar

    jwt_token = create_token(str(user["_id"]), email)
    # Redirect to frontend with token in query param (frontend stores it)
    return RedirectResponse(f"{settings.frontend_url}/?token={jwt_token}")


# ── Get current user (me) ─────────────────────────────────────────────────────
@router.get("/me")
async def me(request: Request, db=Depends(get_db)):
    from auth.utils import get_current_user, bearer
    from fastapi.security import HTTPAuthorizationCredentials
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Not authenticated")
    token = auth_header.split(" ", 1)[1]
    from auth.utils import decode_token
    payload = decode_token(token)
    user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
    if not user:
        raise HTTPException(401, "User not found")
    return {
        "id":     str(user["_id"]),
        "name":   user.get("name", ""),
        "email":  user["email"],
        "avatar": user.get("avatar"),
    }
