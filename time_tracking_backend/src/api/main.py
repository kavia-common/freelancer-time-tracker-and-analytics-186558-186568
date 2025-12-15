from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers_projects import router as projects_router
from src.api.routers_tasks import router as tasks_router
from src.api.routers_sessions import router as sessions_router
from src.api.routers_analytics import router as analytics_router
from src.api.routers_reports import router as reports_router

openapi_tags = [
    {"name": "Health", "description": "Service health and metadata"},
    {"name": "Projects", "description": "Project management endpoints"},
    {"name": "Tasks", "description": "Task management endpoints"},
    {"name": "Sessions", "description": "Time tracking session endpoints"},
    {"name": "Analytics", "description": "Aggregations and earnings analytics"},
    {"name": "Reports", "description": "Export and reporting endpoints"},
]

app = FastAPI(
    title="Freelancer Time Tracker API",
    description="REST API for managing projects, tasks, sessions, analytics, and reports for a time tracking application.",
    version="0.1.0",
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, scope to frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# PUBLIC_INTERFACE
@app.get(
    "/",
    tags=["Health"],
    summary="Health Check",
    description="Returns basic service health information.",
)
def health_check():
    """Health check endpoint."""
    return {"message": "Healthy", "service": "time-tracking-backend"}


# Register routers
app.include_router(projects_router)
app.include_router(tasks_router)
app.include_router(sessions_router)
app.include_router(analytics_router)
app.include_router(reports_router)
