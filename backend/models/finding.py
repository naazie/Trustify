from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Finding(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    scan_id: str
    tool: str                   # semgrep | gitleaks | pylint
    severity: str               # critical | warning | info
    rule_id: str
    cwe: Optional[str] = None
    title: str
    description: str
    file_path: str
    line_start: int
    line_end: int
    code_snippet: Optional[str] = None
    # AI-enriched fields (populated after Gemini call)
    plain_english: Optional[str] = None
    remediation: Optional[str] = None
    impact_score: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class FindingResponse(BaseModel):
    id: str
    scan_id: str
    tool: str
    severity: str
    rule_id: str
    cwe: Optional[str]
    title: str
    description: str
    file_path: str
    line_start: int
    line_end: int
    code_snippet: Optional[str]
    plain_english: Optional[str]
    remediation: Optional[str]
    impact_score: Optional[float]
    created_at: datetime
