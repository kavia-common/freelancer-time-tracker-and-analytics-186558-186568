from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.api.models import Task, TaskCreate
from src.api.storage import list_tasks, save_tasks, list_projects

router = APIRouter(prefix="/tasks", tags=["Tasks"])


class TaskListResponse(BaseModel):
    items: List[Task] = Field(..., description="List of tasks")


# PUBLIC_INTERFACE
@router.get(
    "",
    response_model=TaskListResponse,
    summary="List tasks",
    description="List all tasks. Optional filtering by project_id.",
)
def list_all_tasks(project_id: Optional[str] = Query(None, description="Filter by project ID")) -> TaskListResponse:
    """List all tasks with optional project filter."""
    tasks = list_tasks()
    if project_id:
        tasks = [t for t in tasks if t.project_id == project_id]
    return TaskListResponse(items=tasks)


# PUBLIC_INTERFACE
@router.post(
    "",
    response_model=Task,
    summary="Create task",
    description="Create a task under a project.",
)
def create_task(payload: TaskCreate) -> Task:
    """Create a task."""
    if not any(p.id == payload.project_id for p in list_projects()):
        raise HTTPException(status_code=400, detail="Invalid project_id")
    now = datetime.utcnow()
    t = Task(
        id=_uuid(),
        project_id=payload.project_id,
        name=payload.name,
        description=payload.description,
        created_at=now,
        updated_at=now,
    )
    tasks = list_tasks()
    tasks.append(t)
    save_tasks(tasks)
    return t


# PUBLIC_INTERFACE
@router.get(
    "/{task_id}",
    response_model=Task,
    summary="Get task",
    description="Fetch a single task by ID.",
)
def get_task(task_id: str) -> Task:
    """Get a single task."""
    for t in list_tasks():
        if t.id == task_id:
            return t
    raise HTTPException(status_code=404, detail="Task not found")


class TaskUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Task name")
    description: Optional[str] = Field(None, description="Task description")


# PUBLIC_INTERFACE
@router.put(
    "/{task_id}",
    response_model=Task,
    summary="Update task",
    description="Update name/description of a task.",
)
def update_task(task_id: str, payload: TaskUpdate) -> Task:
    """Update a task."""
    tasks = list_tasks()
    for i, t in enumerate(tasks):
        if t.id == task_id:
            updated = t.model_copy(update={k: v for k, v in payload.model_dump(exclude_unset=True).items()})
            updated.updated_at = datetime.utcnow()
            tasks[i] = updated
            save_tasks(tasks)
            return updated
    raise HTTPException(status_code=404, detail="Task not found")


# PUBLIC_INTERFACE
@router.delete(
    "/{task_id}",
    summary="Delete task",
    description="Delete a task by ID.",
)
def delete_task(task_id: str):
    """Delete a task."""
    tasks = list_tasks()
    new_tasks = [t for t in tasks if t.id != task_id]
    if len(new_tasks) == len(tasks):
        raise HTTPException(status_code=404, detail="Task not found")
    save_tasks(new_tasks)
    return {"status": "deleted"}


def _uuid():
    import uuid
    return str(uuid.uuid4())
