from typing import List

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request

from models.finding import FindingResponse

router = APIRouter()


def get_db(request: Request):
    return request.app.state.db


def _to_response(doc: dict) -> FindingResponse:
    return FindingResponse(
        id=str(doc["_id"]),
        scan_id=doc["scan_id"],
        tool=doc["tool"],
        severity=doc["severity"],
        rule_id=doc["rule_id"],
        cwe=doc.get("cwe"),
        title=doc["title"],
        description=doc["description"],
        file_path=doc["file_path"],
        line_start=doc["line_start"],
        line_end=doc["line_end"],
        code_snippet=doc.get("code_snippet"),
        plain_english=doc.get("plain_english"),
        remediation=doc.get("remediation"),
        impact_score=doc.get("impact_score"),
        created_at=doc["created_at"],
    )


# ── GET /api/findings/:scan_id ────────────────────────────────────────────────
@router.get("/{scan_id}", response_model=List[FindingResponse])
async def get_findings(
    scan_id: str,
    db=Depends(get_db),
    severity: str = None,
    tool: str = None,
    skip: int = 0,
    limit: int = 200,
):
    query: dict = {"scan_id": scan_id}
    if severity:
        query["severity"] = severity
    if tool:
        query["tool"] = tool

    cursor = (
        db.findings.find(query)
        .sort([("severity", 1), ("impact_score", -1)])
        .skip(skip)
        .limit(limit)
    )
    findings = await cursor.to_list(length=limit)
    return [_to_response(f) for f in findings]


# ── GET /api/findings/single/:finding_id ─────────────────────────────────────
@router.get("/single/{finding_id}", response_model=FindingResponse)
async def get_finding(finding_id: str, db=Depends(get_db)):
    doc = await db.findings.find_one({"_id": ObjectId(finding_id)})
    if not doc:
        raise HTTPException(404, "Finding not found")
    return _to_response(doc)
