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

GITHUB_AUTH_URL  = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_API  = "https://api.github.com/user"


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
            "id":               str(user["_id"]),
            "name":             user.get("name", ""),
            "email":            user["email"],
            "avatar":           user.get("avatar"),
            "github_connected": bool(user.get("github_token")),
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


# ── GitHub OAuth — redirect to GitHub ────────────────────────────────────────
@router.get("/github")
async def github_login():
    if not settings.github_client_id:
        raise HTTPException(501, "GitHub OAuth not configured")
    params = (
        f"?client_id={settings.github_client_id}"
        f"&redirect_uri={settings.frontend_url.rstrip('/')}/api/auth/github/callback"
        f"&scope=repo,user:email"
        f"&response_type=code"
    )
    return RedirectResponse(GITHUB_AUTH_URL + params)


# ── GitHub OAuth — callback ───────────────────────────────────────────────────
@router.get("/github/callback")
async def github_callback(code: str, db=Depends(get_db)):
    async with httpx.AsyncClient() as client:
        # Exchange code for token
        token_resp = await client.post(
            GITHUB_TOKEN_URL,
            headers={"Accept": "application/json"},
            data={
                "client_id":     settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code":          code,
                "redirect_uri":  f"{settings.frontend_url.rstrip('/')}/api/auth/github/callback"
            }
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(400, f"Failed to get access token: {token_data.get('error_description', 'Unknown error')}")

        # Fetch user info
        user_resp = await client.get(
            GITHUB_USER_API,
            headers={"Authorization": f"token {access_token}"}
        )
        user_resp.raise_for_status()
        gh_user = user_resp.json()

        # Fetch email if not public
        email = gh_user.get("email")
        if not email:
            emails_resp = await client.get(
                f"{GITHUB_USER_API}/emails",
                headers={"Authorization": f"token {access_token}"}
            )
            emails_resp.raise_for_status()
            for e in emails_resp.json():
                if e["primary"] and e["verified"]:
                    email = e["email"]
                    break

    if not email:
        raise HTTPException(400, "Could not retrieve email from GitHub")

    name = gh_user.get("name") or gh_user.get("login")
    avatar = gh_user.get("avatar_url")

    user = await db.users.find_one({"email": email})
    if not user:
        result = await db.users.insert_one({
            "name":         name,
            "email":        email,
            "avatar":       avatar,
            "provider":     "github",
            "github_token": access_token,
            "created_at":   datetime.utcnow(),
        })
        user = await db.users.find_one({"_id": result.inserted_id})
    else:
        # Link GitHub if not already linked or refresh token
        await db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"github_token": access_token, "avatar": avatar, "name": name}}
        )
        user["github_token"] = access_token
        user["avatar"] = avatar
        user["name"] = name

    jwt_token = create_token(str(user["_id"]), email)
    return RedirectResponse(f"{settings.frontend_url}/?token={jwt_token}")


# ── GitHub Repos — list user repositories ─────────────────────────────────────
@router.get("/github/repos")
async def list_github_repos(request: Request, db=Depends(get_db)):
    # Simple manual token check since get_current_user might be async/complex here
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Not authenticated")
    token = auth_header.split(" ", 1)[1]
    from auth.utils import decode_token
    payload = decode_token(token)
    user = await db.users.find_one({"_id": ObjectId(payload["sub"])})

    if not user or not user.get("github_token"):
        raise HTTPException(400, "GitHub account not connected")

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{GITHUB_USER_API}/repos?sort=updated&per_page=100",
            headers={"Authorization": f"token {user['github_token']}"}
        )
        if resp.status_code != 200:
            # If token is invalid/expired, clear it
            if resp.status_code == 401:
                await db.users.update_one({"_id": user["_id"]}, {"$unset": {"github_token": ""}})
            raise HTTPException(resp.status_code, "Failed to fetch repositories from GitHub")

        repos = resp.json()
        return [
            {
                "id":        r["id"],
                "name":      r["name"],
                "full_name": r["full_name"],
                "url":       r["clone_url"],
                "private":   r["private"],
                "updated_at": r["updated_at"],
                "language":  r.get("language"),
            }
            for r in repos
        ]


# ── Get current user (me) ─────────────────────────────────────────────────────
@router.get("/me")
async def me(request: Request, db=Depends(get_db)):
    # (Existing /me logic updated to include github_connected)
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
        "id":               str(user["_id"]),
        "name":             user.get("name", ""),
        "email":            user["email"],
        "avatar":           user.get("avatar"),
        "github_connected": bool(user.get("github_token")),
    }
