from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict

from pydantic import BaseModel, Field, validator


class Timeframe(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


# PUBLIC_INTERFACE
class ProjectCreate(BaseModel):
    """Payload to create a project."""
    name: str = Field(..., description="Human friendly name for the project")
    description: Optional[str] = Field(None, description="Description of the project")
    hourly_rate: Optional[float] = Field(None, description="Default hourly rate used if session is billable and no rate provided")


# PUBLIC_INTERFACE
class Project(ProjectCreate):
    """Project representation with identifier and timestamps."""
    id: str = Field(..., description="Unique project ID (UUID)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# PUBLIC_INTERFACE
class TaskCreate(BaseModel):
    """Payload to create a task under a project."""
    project_id: str = Field(..., description="Parent project ID")
    name: str = Field(..., description="Task name")
    description: Optional[str] = Field(None, description="Task details")


# PUBLIC_INTERFACE
class Task(TaskCreate):
    """Task representation with identifier and timestamps."""
    id: str = Field(..., description="Unique task ID (UUID)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# PUBLIC_INTERFACE
class SessionCreate(BaseModel):
    """Create a time tracking session."""
    project_id: str = Field(..., description="Project ID")
    task_id: Optional[str] = Field(None, description="Optional task ID")
    start_time: datetime = Field(..., description="Start time (ISO 8601)")
    end_time: Optional[datetime] = Field(None, description="End time (ISO 8601). If omitted, session is in-progress")
    description: Optional[str] = Field(None, description="Notes for this session")
    billable: bool = Field(True, description="Whether this session is billable")
    hourly_rate: Optional[float] = Field(None, description="Hourly rate for this session. Falls back to project hourly_rate if not provided")

    @validator("end_time")
    def end_after_start(cls, v, values):
        start = values.get("start_time")
        if v is not None and start is not None and v < start:
            raise ValueError("end_time must be after start_time")
        return v


# PUBLIC_INTERFACE
class SessionUpdate(BaseModel):
    """Update fields for a session."""
    start_time: Optional[datetime] = Field(None, description="Start time")
    end_time: Optional[datetime] = Field(None, description="End time")
    description: Optional[str] = Field(None, description="Notes")
    billable: Optional[bool] = Field(None, description="Whether this session is billable")
    hourly_rate: Optional[float] = Field(None, description="Hourly rate override")

    @validator("end_time")
    def end_after_start(cls, v, values):
        start = values.get("start_time")
        if v is not None and start is not None and v < start:
            raise ValueError("end_time must be after start_time")
        return v


# PUBLIC_INTERFACE
class Session(SessionCreate):
    """Session representation with computed duration and identifiers."""
    id: str = Field(..., description="Unique session ID (UUID)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last updated timestamp")
    duration_minutes: Optional[float] = Field(None, description="Computed duration in minutes (if end_time is set)")
    earnings: Optional[float] = Field(None, description="Computed earnings if billable and rate is available")


# PUBLIC_INTERFACE
class AnalyticsQuery(BaseModel):
    """Query parameters for analytics aggregation."""
    timeframe: Timeframe = Field(..., description="Aggregation period: daily, weekly, monthly")
    project_id: Optional[str] = Field(None, description="Filter by project ID")
    task_id: Optional[str] = Field(None, description="Filter by task ID")
    from_date: Optional[datetime] = Field(None, description="Start of date range")
    to_date: Optional[datetime] = Field(None, description="End of date range")


# PUBLIC_INTERFACE
class AggregatedBucket(BaseModel):
    """Aggregated totals for a bucket (day/week/month)."""
    key: str = Field(..., description="Bucket key like 2025-01-31 (daily), 2025-W05 (weekly), 2025-01 (monthly)")
    total_minutes: float = Field(..., description="Total minutes in bucket")
    total_earnings: float = Field(..., description="Total earnings for bucket")


# PUBLIC_INTERFACE
class AnalyticsResponse(BaseModel):
    """Analytics response with totals and buckets."""
    total_minutes: float = Field(..., description="Total minutes across the result set")
    total_earnings: float = Field(..., description="Total earnings across the result set")
    buckets: List[AggregatedBucket] = Field(..., description="Buckets by timeframe")


def _now() -> datetime:
    return datetime.utcnow()


def _uuid() -> str:
    return str(uuid.uuid4())


# PUBLIC_INTERFACE
def compute_session_fields(
    session: Dict,
    project_lookup: Dict[str, Project]
) -> Dict:
    """Compute duration_minutes and earnings for a session dict."""
    start = session.get("start_time")
    end = session.get("end_time")
    duration_minutes = None
    if start and end:
        duration_minutes = (end - start).total_seconds() / 60.0
    earnings = None
    if duration_minutes and session.get("billable"):
        rate = session.get("hourly_rate")
        if rate is None:
            proj = project_lookup.get(session.get("project_id"))
            rate = proj.hourly_rate if proj and proj.hourly_rate is not None else None
        if rate is not None:
            earnings = (duration_minutes / 60.0) * float(rate)
    session["duration_minutes"] = duration_minutes
    session["earnings"] = earnings
    return session
