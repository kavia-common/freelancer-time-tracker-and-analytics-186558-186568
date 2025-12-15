from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.api.models import Project, ProjectCreate
from src.api.storage import list_projects, save_projects

router = APIRouter(prefix="/projects", tags=["Projects"])


class ProjectListResponse(BaseModel):
    items: List[Project] = Field(..., description="List of projects")


# PUBLIC_INTERFACE
@router.get(
    "",
    response_model=ProjectListResponse,
    summary="List projects",
    description="Returns all projects currently stored.",
)
def list_all_projects() -> ProjectListResponse:
    """List all projects."""
    return ProjectListResponse(items=list_projects())


# PUBLIC_INTERFACE
@router.post(
    "",
    response_model=Project,
    summary="Create project",
    description="Create a new project with an optional default hourly rate.",
)
def create_project(payload: ProjectCreate) -> Project:
    """Create a project and persist to JSON storage."""
    now = datetime.utcnow()
    proj = Project(
        id=str(uuid4()),
        name=payload.name,
        description=payload.description,
        hourly_rate=payload.hourly_rate,
        created_at=now,
        updated_at=now,
    )
    projects = list_projects()
    projects.append(proj)
    save_projects(projects)
    return proj


# PUBLIC_INTERFACE
@router.get(
    "/{project_id}",
    response_model=Project,
    summary="Get project",
    description="Fetch a single project by ID.",
)
def get_project(project_id: str) -> Project:
    """Retrieve a project by ID."""
    for p in list_projects():
        if p.id == project_id:
            return p
    raise HTTPException(status_code=404, detail="Project not found")


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    hourly_rate: Optional[float] = Field(None, description="Default hourly rate")


# PUBLIC_INTERFACE
@router.put(
    "/{project_id}",
    response_model=Project,
    summary="Update project",
    description="Update project fields.",
)
def update_project(project_id: str, payload: ProjectUpdate) -> Project:
    """Update the specified project."""
    projects = list_projects()
    for idx, p in enumerate(projects):
        if p.id == project_id:
            updated = p.model_copy(update={k: v for k, v in payload.model_dump(exclude_unset=True).items()})
            updated.updated_at = datetime.utcnow()
            projects[idx] = updated
            save_projects(projects)
            return updated
    raise HTTPException(status_code=404, detail="Project not found")


# PUBLIC_INTERFACE
@router.delete(
    "/{project_id}",
    summary="Delete project",
    description="Delete a project and cascade delete its tasks and sessions (soft for JSON store not implemented; this will not affect tasks/sessions in this router).",
)
def delete_project(project_id: str):
    """Delete a project by ID. Note: does not cascade in this router."""
    projects = [p for p in list_projects() if p.id != project_id]
    if len(projects) == len(list_projects()):
        raise HTTPException(status_code=404, detail="Project not found")
    save_projects(projects)
    return {"status": "deleted"}


def uuid4():
    import uuid
    return str(uuid.uuid4())
