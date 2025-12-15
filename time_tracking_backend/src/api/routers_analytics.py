from collections import defaultdict
from datetime import datetime
from typing import List

from fastapi import APIRouter

from src.api.models import (
    AnalyticsQuery,
    AnalyticsResponse,
    AggregatedBucket,
    Timeframe,
)
from src.api.storage import list_sessions

router = APIRouter(prefix="/analytics", tags=["Analytics"])


# PUBLIC_INTERFACE
@router.post(
    "",
    response_model=AnalyticsResponse,
    summary="Compute analytics",
    description="Aggregate totals by timeframe (daily/weekly/monthly) and compute total earnings.",
)
def compute_analytics(query: AnalyticsQuery) -> AnalyticsResponse:
    """Compute analytics with optional filters."""
    sessions = list_sessions()
    # Filter
    if query.project_id:
        sessions = [s for s in sessions if s.project_id == query.project_id]
    if query.task_id:
        sessions = [s for s in sessions if s.task_id == query.task_id]
    if query.from_date:
        sessions = [s for s in sessions if s.start_time >= query.from_date]
    if query.to_date:
        sessions = [s for s in sessions if (s.end_time or s.start_time) <= query.to_date]
    # Aggregate
    buckets = defaultdict(lambda: {"minutes": 0.0, "earnings": 0.0})
    total_minutes = 0.0
    total_earnings = 0.0
    for s in sessions:
        if s.duration_minutes is None:
            # ignore in-progress sessions for aggregation
            continue
        key = _bucket_key(s.start_time, query.timeframe)
        buckets[key]["minutes"] += float(s.duration_minutes or 0.0)
        total_minutes += float(s.duration_minutes or 0.0)
        if s.earnings is not None:
            buckets[key]["earnings"] += float(s.earnings)
            total_earnings += float(s.earnings)
    result_buckets: List[AggregatedBucket] = [
        AggregatedBucket(key=k, total_minutes=v["minutes"], total_earnings=v["earnings"])
        for k, v in sorted(buckets.items())
    ]
    return AnalyticsResponse(total_minutes=total_minutes, total_earnings=total_earnings, buckets=result_buckets)


def _bucket_key(dt: datetime, timeframe: Timeframe) -> str:
    if timeframe == Timeframe.daily:
        return dt.strftime("%Y-%m-%d")
    if timeframe == Timeframe.weekly:
        # ISO week: YYYY-Www
        year, week, _ = dt.isocalendar()
        return f"{year}-W{week:02d}"
    # monthly
    return dt.strftime("%Y-%m")
