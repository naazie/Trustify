from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class Finding(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    scan_id: str
    tool: str                   # semgrep | gitleaks | pylint | eslint
    # ── Unified schema fields ──────────────────────────────────────────────
    type: Optional[str] = None          # SECURITY | CODE_QUALITY | SECRET | DEPENDENCY
    subcategory: Optional[str] = None   # e.g. SQL_INJECTION, HARDCODED_SECRET
    confidence: Optional[float] = None  # 0.0–1.0
    # ── Standard fields ───────────────────────────────────────────────────
    severity: str               # critical | warning | info
    rule_id: str
    cwe: Optional[str] = None
    title: str
    description: str
    file_path: str
    line_start: int
    line_end: int
    code_snippet: Optional[str] = None
    # ── Gitleaks-specific ─────────────────────────────────────────────────
    commit_history: Optional[List[str]] = None
    found_in_history: Optional[bool] = None
    # ── AI-enriched fields ────────────────────────────────────────────────
    plain_english: Optional[str] = None
    what_it_means: Optional[List[str]] = None   # structured bullet points
    how_to_fix: Optional[List[str]] = None       # numbered remediation steps
    why_it_matters: Optional[str] = None
    remediation: Optional[str] = None           # legacy/backwards-compat
    impact_score: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class FindingResponse(BaseModel):
    id: str
    scan_id: str
    tool: str
    type: Optional[str] = None
    subcategory: Optional[str] = None
    confidence: Optional[float] = None
    severity: str
    rule_id: str
    cwe: Optional[str]
    title: str
    description: str
    file_path: str
    line_start: int
    line_end: int
    code_snippet: Optional[str]
    commit_history: Optional[List[str]] = None
    found_in_history: Optional[bool] = None
    plain_english: Optional[str]
    what_it_means: Optional[List[str]] = None
    how_to_fix: Optional[List[str]] = None
    why_it_matters: Optional[str] = None
    remediation: Optional[str]
    impact_score: Optional[float]
    created_at: datetime
