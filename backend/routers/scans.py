from __future__ import annotations

import asyncio
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile

from models.scan import ScanCreate, ScanResponse, ScanSummary
from services.orchestrator import JobOrchestrator
from auth.utils import get_current_user, get_db

router = APIRouter()


# ── POST /api/scans  (GitHub URL) ────────────────────────────────────────────
@router.post("", response_model=ScanResponse, status_code=202)
async def create_scan(
    payload: ScanCreate,
    background_tasks: BackgroundTasks,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    if payload.source_type == "github" and not payload.source_url:
        raise HTTPException(400, "source_url is required for github scans")

    doc = {
        "user_id": str(current_user["_id"]),
        "source_type": payload.source_type,
        "source_url": payload.source_url,
        "source_filename": None,
        "status": "queued",
        "languages": [],
        "tools_run": [],
        "created_at": __import__("datetime").datetime.utcnow(),
        "completed_at": None,
        "error_message": None,
        "summary": {"critical": 0, "warning": 0, "info": 0, "total": 0},
    }
    result = await db.scans.insert_one(doc)
    scan_id = str(result.inserted_id)

    orchestrator = JobOrchestrator(db)
    github_token = current_user.get("github_token") if payload.source_type == "github" else None

    background_tasks.add_task(
        orchestrator.run_scan,
        scan_id=scan_id,
        source_type=payload.source_type,
        source_url=payload.source_url,
        file_bytes=None,
        filename=None,
        github_token=github_token,
    )

    doc["_id"] = scan_id
    return _to_response(doc)


# ── POST /api/scans/upload  (ZIP file) ───────────────────────────────────────
@router.post("/upload", response_model=ScanResponse, status_code=202)
async def upload_scan(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    if not file.filename.endswith(".zip"):
        raise HTTPException(400, "Only .zip files are supported")

    file_bytes = await file.read()
    doc = {
        "user_id": str(current_user["_id"]),
        "source_type": "zip",
        "source_url": None,
        "source_filename": file.filename,
        "status": "queued",
        "languages": [],
        "tools_run": [],
        "created_at": __import__("datetime").datetime.utcnow(),
        "completed_at": None,
        "error_message": None,
        "summary": {"critical": 0, "warning": 0, "info": 0, "total": 0},
    }
    result = await db.scans.insert_one(doc)
    scan_id = str(result.inserted_id)

    orchestrator = JobOrchestrator(db)
    background_tasks.add_task(
        orchestrator.run_scan,
        scan_id=scan_id,
        source_type="zip",
        source_url=None,
        file_bytes=file_bytes,
        filename=file.filename,
    )

    doc["_id"] = scan_id
    return _to_response(doc)


# ── GET /api/scans ────────────────────────────────────────────────────────────
@router.get("", response_model=List[ScanResponse])
async def list_scans(
    db=Depends(get_db),
    current_user=Depends(get_current_user),
    skip: int = 0,
    limit: int = 20,
    source_url: Optional[str] = None,
):
    query = {"user_id": str(current_user["_id"])}
    if source_url:
        query["source_url"] = source_url
        
    cursor = (
        db.scans.find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    scans = await cursor.to_list(length=limit)
    return [_to_response(s) for s in scans]


# ── GET /api/scans/:id ────────────────────────────────────────────────────────
@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(scan_id: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    scan = await db.scans.find_one({"_id": ObjectId(scan_id)})
    if not scan:
        raise HTTPException(404, "Scan not found")
    if scan.get("user_id") and scan["user_id"] != str(current_user["_id"]):
        raise HTTPException(403, "Access denied")
    return _to_response(scan)


# ── DELETE /api/scans/:id ─────────────────────────────────────────────────────
@router.delete("/{scan_id}", status_code=204)
async def delete_scan(scan_id: str, db=Depends(get_db), current_user=Depends(get_current_user)):
    scan = await db.scans.find_one({"_id": ObjectId(scan_id)})
    if scan and scan.get("user_id") and scan["user_id"] != str(current_user["_id"]):
        raise HTTPException(403, "Access denied")
    await db.scans.delete_one({"_id": ObjectId(scan_id)})
    await db.findings.delete_many({"scan_id": scan_id})


# ── Helper ────────────────────────────────────────────────────────────────────
def _to_response(doc: dict) -> ScanResponse:
    summary = doc.get("summary", {})
    return ScanResponse(
        id=str(doc["_id"]),
        source_type=doc["source_type"],
        source_url=doc.get("source_url"),
        source_filename=doc.get("source_filename"),
        status=doc["status"],
        languages=doc.get("languages", []),
        tools_run=doc.get("tools_run", []),
        created_at=doc["created_at"],
        completed_at=doc.get("completed_at"),
        error_message=doc.get("error_message"),
        summary=ScanSummary(
            critical=summary.get("critical", 0),
            warning=summary.get("warning", 0),
            info=summary.get("info", 0),
            total=summary.get("total", 0),
        ),
    )
