"""
Analytics and statistics routes.

Provides aggregated test metrics, trends, and insights.
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import TestDefinitionModel, TestRunModel, get_db
from ..schemas import AnalyticsSummaryResponse, AnalyticsTrendsResponse, TrendDataPoint


router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary", response_model=AnalyticsSummaryResponse)
async def get_analytics_summary(
    db: AsyncSession = Depends(get_db),
):
    """
    Get overall analytics summary.

    Args:
        db: Database session

    Returns:
        Analytics summary with key metrics
    """
    # For now, get data from all orgs since auth is not set up
    # TODO: Add proper authentication and filter by org_id
    org_id = None  # Get all data

    # Total tests
    query = select(func.count()).select_from(TestDefinitionModel)
    if org_id:
        query = query.where(TestDefinitionModel.org_id == org_id)
    total_tests_result = await db.execute(query)
    total_tests = total_tests_result.scalar_one()

    # Total runs
    query = select(func.count()).select_from(TestRunModel)
    if org_id:
        query = query.where(TestRunModel.org_id == org_id)
    total_runs_result = await db.execute(query)
    total_runs = total_runs_result.scalar_one()

    # Runs in last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    query = (
        select(func.count())
        .select_from(TestRunModel)
        .where(TestRunModel.created_at >= seven_days_ago)
    )
    runs_7d_result = await db.execute(query)
    total_runs_last_7_days = runs_7d_result.scalar_one()

    # Runs in last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    query = (
        select(func.count())
        .select_from(TestRunModel)
        .where(TestRunModel.created_at >= thirty_days_ago)
    )
    runs_30d_result = await db.execute(query)
    total_runs_last_30_days = runs_30d_result.scalar_one()

    # Pass rate last 7 days
    query = (
        select(func.count())
        .select_from(TestRunModel)
        .where(
            TestRunModel.created_at >= seven_days_ago,
            TestRunModel.status == "completed",
        )
    )
    passed_7d_result = await db.execute(query)
    passed_7d = passed_7d_result.scalar_one()
    pass_rate_7_days = (
        (passed_7d / total_runs_last_7_days * 100) if total_runs_last_7_days > 0 else 0.0
    )

    # Pass rate last 30 days
    query = (
        select(func.count())
        .select_from(TestRunModel)
        .where(
            TestRunModel.created_at >= thirty_days_ago,
            TestRunModel.status == "completed",
        )
    )
    passed_30d_result = await db.execute(query)
    passed_30d = passed_30d_result.scalar_one()
    pass_rate_30_days = (
        (passed_30d / total_runs_last_30_days * 100) if total_runs_last_30_days > 0 else 0.0
    )

    # Average duration
    query = select(func.avg(TestRunModel.duration_ms)).where(TestRunModel.duration_ms.isnot(None))
    avg_duration_result = await db.execute(query)
    avg_duration_ms = avg_duration_result.scalar_one() or 0.0

    # Most run tests
    query = (
        select(
            TestRunModel.test_id,
            TestRunModel.test_name,
            func.count(TestRunModel.id).label("run_count"),
        )
        .group_by(TestRunModel.test_id, TestRunModel.test_name)
        .order_by(func.count(TestRunModel.id).desc())
        .limit(5)
    )
    most_run_result = await db.execute(query)
    most_run_tests = [
        {
            "test_id": str(row.test_id),
            "test_name": row.test_name,
            "run_count": row.run_count,
        }
        for row in most_run_result
    ]

    # Recent failures
    query = (
        select(TestRunModel)
        .where(TestRunModel.status == "failed")
        .order_by(TestRunModel.created_at.desc())
        .limit(5)
    )
    recent_failures_result = await db.execute(query)
    recent_failures = [
        {
            "run_id": str(run.id),
            "test_name": run.test_name,
            "failed_at": run.completed_at.isoformat() if run.completed_at else None,
            "error": run.result.get("error_message") if run.result else None,
        }
        for run in recent_failures_result.scalars()
    ]

    # Flaky tests (tests with inconsistent pass/fail)
    # For now, return empty list - this would require more complex analysis
    flaky_tests = []

    return AnalyticsSummaryResponse(
        total_tests=total_tests,
        total_runs=total_runs,
        total_runs_last_7_days=total_runs_last_7_days,
        total_runs_last_30_days=total_runs_last_30_days,
        pass_rate_7_days=pass_rate_7_days,
        pass_rate_30_days=pass_rate_30_days,
        avg_duration_ms=float(avg_duration_ms),
        most_run_tests=most_run_tests,
        recent_failures=recent_failures,
        flaky_tests=flaky_tests,
    )


@router.get("/trends", response_model=AnalyticsTrendsResponse)
async def get_analytics_trends(
    period: str = Query("7d", regex="^(7d|30d|90d)$", description="Time period"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get test run trends over time.

    Args:
        period: Time period (7d, 30d, 90d)
        db: Database session

    Returns:
        Trend data points over the specified period
    """
    # Calculate date range
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map[period]
    start_date = datetime.utcnow() - timedelta(days=days)

    # Get runs grouped by date
    from sqlalchemy import Date, cast

    result = await db.execute(
        select(
            cast(TestRunModel.created_at, Date).label("date"),
            func.count(TestRunModel.id).label("total"),
            func.sum(func.cast((TestRunModel.status == "completed"), func.Integer())).label(
                "passed"
            ),
            func.sum(func.cast((TestRunModel.status == "failed"), func.Integer())).label("failed"),
            func.avg(TestRunModel.duration_ms).label("avg_duration"),
        )
        .where(TestRunModel.created_at >= start_date)
        .group_by(cast(TestRunModel.created_at, Date))
        .order_by(cast(TestRunModel.created_at, Date))
    )

    trends = [
        TrendDataPoint(
            date=row.date.isoformat(),
            total=row.total,
            passed=row.passed or 0,
            failed=row.failed or 0,
            avg_duration_ms=float(row.avg_duration) if row.avg_duration else 0.0,
        )
        for row in result
    ]

    return AnalyticsTrendsResponse(
        trends=trends,
        period=period,
    )
