from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId


class ScanSummary(BaseModel):
    critical: int = 0
    warning: int = 0
    info: int = 0
    total: int = 0


class ScanJob(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    source_type: str          # "github" | "zip"
    source_url: Optional[str] = None
    source_filename: Optional[str] = None
    status: str = "queued"   # queued | running | complete | failed
    languages: List[str] = []
    tools_run: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    summary: ScanSummary = Field(default_factory=ScanSummary)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


class ScanCreate(BaseModel):
    source_type: str          # "github" | "zip"
    source_url: Optional[str] = None


class ScanResponse(BaseModel):
    id: str
    source_type: str
    source_url: Optional[str] = None
    source_filename: Optional[str] = None
    status: str
    languages: List[str]
    tools_run: List[str]
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    summary: ScanSummary
