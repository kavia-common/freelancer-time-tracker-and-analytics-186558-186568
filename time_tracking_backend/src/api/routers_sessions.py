from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.api.models import Session, SessionCreate, SessionUpdate
from src.api.storage import list_sessions, save_sessions, list_projects

router = APIRouter(prefix="/sessions", tags=["Sessions"])


class SessionListResponse(BaseModel):
    items: List[Session] = Field(..., description="List of sessions")


# PUBLIC_INTERFACE
@router.get(
    "",
    response_model=SessionListResponse,
    summary="List sessions",
    description="List sessions with optional filters by project_id, task_id and active (in-progress).",
)
def list_all_sessions(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    active: Optional[bool] = Query(None, description="If true, returns only sessions without an end_time"),
) -> SessionListResponse:
    """List sessions."""
    sessions = list_sessions()
    if project_id:
        sessions = [s for s in sessions if s.project_id == project_id]
    if task_id:
        sessions = [s for s in sessions if s.task_id == task_id]
    if active is True:
        sessions = [s for s in sessions if s.end_time is None]
    if active is False:
        sessions = [s for s in sessions if s.end_time is not None]
    return SessionListResponse(items=sessions)


# PUBLIC_INTERFACE
@router.post(
    "",
    response_model=Session,
    summary="Create session",
    description="Create a new time tracking session. If end_time is omitted, session is marked in-progress.",
)
def create_session(payload: SessionCreate) -> Session:
    """Create a new session."""
    if not any(p.id == payload.project_id for p in list_projects()):
        raise HTTPException(status_code=400, detail="Invalid project_id")
    now = datetime.utcnow()
    s = Session(
        id=_uuid(),
        project_id=payload.project_id,
        task_id=payload.task_id,
        start_time=payload.start_time,
        end_time=payload.end_time,
        description=payload.description,
        billable=payload.billable,
        hourly_rate=payload.hourly_rate,
        created_at=now,
        updated_at=now,
        duration_minutes=None,
        earnings=None,
    )
    sessions = list_sessions()
    sessions.append(s)
    save_sessions(sessions)
    # re-fetch to ensure computed fields are included
    for sess in list_sessions():
        if sess.id == s.id:
            return sess
    return s


# PUBLIC_INTERFACE
@router.get(
    "/{session_id}",
    response_model=Session,
    summary="Get session",
    description="Fetch a session by ID.",
)
def get_session(session_id: str) -> Session:
    """Get session by ID."""
    for s in list_sessions():
        if s.id == session_id:
            return s
    raise HTTPException(status_code=404, detail="Session not found")


# PUBLIC_INTERFACE
@router.put(
    "/{session_id}",
    response_model=Session,
    summary="Update session",
    description="Update a session's times, description, billable flag, or hourly rate.",
)
def update_session(session_id: str, payload: SessionUpdate) -> Session:
    """Update a session."""
    sessions = list_sessions()
    for i, s in enumerate(sessions):
        if s.id == session_id:
            updated = s.model_copy(update={k: v for k, v in payload.model_dump(exclude_unset=True).items()})
            updated.updated_at = datetime.utcnow()
            sessions[i] = updated
            save_sessions(sessions)
            # re-fetch computed
            for sess in list_sessions():
                if sess.id == session_id:
                    return sess
            return updated
    raise HTTPException(status_code=404, detail="Session not found")


# PUBLIC_INTERFACE
@router.delete(
    "/{session_id}",
    summary="Delete session",
    description="Delete a session by ID.",
)
def delete_session(session_id: str):
    """Delete a session by ID."""
    sessions = list_sessions()
    new_sessions = [s for s in sessions if s.id != session_id]
    if len(new_sessions) == len(sessions):
        raise HTTPException(status_code=404, detail="Session not found")
    save_sessions(new_sessions)
    return {"status": "deleted"}


def _uuid():
    import uuid
    return str(uuid.uuid4())
