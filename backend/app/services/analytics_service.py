from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_record import DataRecord
from app.schemas.analytics import AnalyticsSummary, CategoryAggregation, TrendPoint


async def get_summary(
    db: AsyncSession,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    category: Optional[str] = None,
) -> AnalyticsSummary:
    filters = _build_filters(start_time, end_time, category)
    where_clause = and_(*filters) if filters else True

    result = await db.execute(
        select(
            func.count().label("total"),
            func.sum(DataRecord.value).label("total_value"),
            func.avg(DataRecord.value).label("avg_value"),
            func.max(DataRecord.value).label("max_value"),
            func.min(DataRecord.value).label("min_value"),
        ).where(where_clause)
    )
    row = result.one()

    anomaly_result = await db.execute(
        select(func.count()).select_from(DataRecord).where(
            and_(DataRecord.is_anomaly == True, where_clause)  # noqa: E712
        )
    )
    anomaly_count = anomaly_result.scalar_one()

    return AnalyticsSummary(
        total=row.total or 0,
        total_value=float(row.total_value or 0),
        avg_value=float(row.avg_value or 0),
        max_value=float(row.max_value or 0),
        min_value=float(row.min_value or 0),
        anomaly_count=anomaly_count,
    )


async def get_category_aggregation(
    db: AsyncSession,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> list[CategoryAggregation]:
    filters = _build_filters(start_time, end_time)
    where_clause = and_(*filters) if filters else True

    result = await db.execute(
        select(
            DataRecord.category,
            func.count().label("count"),
            func.avg(DataRecord.value).label("avg_value"),
            func.sum(DataRecord.value).label("total_value"),
        )
        .where(where_clause)
        .group_by(DataRecord.category)
        .order_by(func.count().desc())
    )
    return [
        CategoryAggregation(
            category=row.category,
            count=row.count,
            avg_value=float(row.avg_value or 0),
            total_value=float(row.total_value or 0),
        )
        for row in result.all()
    ]


async def get_trend(
    db: AsyncSession,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    category: Optional[str] = None,
    interval: str = "hour",
) -> list[TrendPoint]:
    filters = _build_filters(start_time, end_time, category)
    where_clause = and_(*filters) if filters else True

    if interval == "minute":
        trunc_expr = func.date_format(DataRecord.timestamp, "%Y-%m-%d %H:%i:00")
    elif interval == "hour":
        trunc_expr = func.date_format(DataRecord.timestamp, "%Y-%m-%d %H:00:00")
    elif interval == "day":
        trunc_expr = func.date_format(DataRecord.timestamp, "%Y-%m-%d 00:00:00")
    else:
        trunc_expr = func.date_format(DataRecord.timestamp, "%Y-%m-%d %H:00:00")

    result = await db.execute(
        select(
            trunc_expr.label("period"),
            DataRecord.category,
            func.avg(DataRecord.value).label("avg_value"),
            func.count().label("count"),
            func.sum(DataRecord.is_anomaly.cast(Integer)).label("anomaly_count"),
        )
        .where(where_clause)
        .group_by("period", DataRecord.category)
        .order_by("period", DataRecord.category)
    )
    return [
        TrendPoint(
            timestamp=datetime.fromisoformat(row.period),
            category=row.category,
            avg_value=float(row.avg_value or 0),
            count=row.count,
            anomaly_count=int(row.anomaly_count or 0),
        )
        for row in result.all()
    ]


def _build_filters(
    start_time: Optional[datetime],
    end_time: Optional[datetime],
    category: Optional[str] = None,
) -> list:
    filters = []
    if start_time:
        filters.append(DataRecord.timestamp >= start_time)
    if end_time:
        filters.append(DataRecord.timestamp <= end_time)
    if category:
        filters.append(DataRecord.category == category)
    return filters
