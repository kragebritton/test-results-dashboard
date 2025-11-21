from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class HistoryEntry(BaseModel):
    build_id: str
    uploaded_at: datetime


class ProjectMetadata(BaseModel):
    project: str
    latest: Optional[str] = None
    history: List[HistoryEntry] = Field(default_factory=list)
    retention_runs: Optional[int] = Field(None, ge=1)
    retention_days: Optional[int] = Field(None, ge=1)


class ProjectRetentionSettings(BaseModel):
    retention_runs: Optional[int] = Field(None, ge=1)
    retention_days: Optional[int] = Field(None, ge=1)
