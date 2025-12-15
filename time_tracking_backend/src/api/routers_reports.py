from datetime import datetime

from fastapi import APIRouter, Response
from pydantic import BaseModel, Field

from src.api.models import AnalyticsQuery
from src.api.routers_analytics import compute_analytics

router = APIRouter(prefix="/reports", tags=["Reports"])


class TimesheetExportRequest(BaseModel):
    query: AnalyticsQuery = Field(..., description="Analytics filter used for the report")
    title: str = Field("Timesheet", description="Report title")
    prepared_by: str = Field("Freelancer", description="Prepared by field for the report")


# PUBLIC_INTERFACE
@router.post(
    "/timesheet.pdf",
    summary="Export timesheet PDF (scaffold)",
    description="Generates a simple PDF bytes placeholder for the timesheet based on analytics. Replace with real PDF library in future.",
    responses={
        200: {"content": {"application/pdf": {"schema": {"type": "string", "format": "binary"}}}, "description": "PDF bytes"},
    },
)
def export_timesheet_pdf(req: TimesheetExportRequest):
    """Generate a placeholder PDF file using analytics results."""
    analytics = compute_analytics(req.query)
    # Placeholder PDF content; for future replace with a real library like reportlab or WeasyPrint
    content = f"""{req.title}
Prepared By: {req.prepared_by}
Generated At: {datetime.utcnow().isoformat()}Z

Total Minutes: {analytics.total_minutes}
Total Earnings: {analytics.total_earnings:.2f}

Buckets:
"""
    for b in analytics.buckets:
        content += f"- {b.key}: {b.total_minutes} min, ${b.total_earnings:.2f}\n"
    # Wrap in a minimal PDF-like content. Not a spec-compliant PDF, but keeps the endpoint functional.
    pseudo_pdf = f"%PDF-1.1\n% Timesheet Placeholder\n{content}\n%%EOF"
    return Response(content=pseudo_pdf.encode("utf-8"), media_type="application/pdf")
