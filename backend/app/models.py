from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class HistoryEntry(BaseModel):
    build_id: str
    uploaded_at: datetime
    environment: str = Field("prod", min_length=1)


class ProjectMetadata(BaseModel):
    project: str
    latest: Optional[str] = None
    latest_by_environment: dict[str, str] = Field(default_factory=dict)
    history: List[HistoryEntry] = Field(default_factory=list)
    retention_runs: Optional[int] = Field(None, ge=1)
    retention_days: Optional[int] = Field(None, ge=1)


class ProjectRetentionSettings(BaseModel):
    retention_runs: Optional[int] = Field(None, ge=1)
    retention_days: Optional[int] = Field(None, ge=1)
