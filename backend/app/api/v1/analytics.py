import io
from datetime import datetime
from typing import Annotated, Optional

import pandas as pd
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.analytics import AnalyticsResponse
from app.services import analytics_service, data_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/",
    response_model=AnalyticsResponse,
    responses={
        401: {"description": "Invalid or expired token"},
    },
)
async def get_analytics(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    category: Optional[str] = None,
    trend_interval: str = Query("hour", pattern="^(minute|hour|day)$"),
) -> AnalyticsResponse:
    summary = await analytics_service.get_summary(db, start_time, end_time, category)
    categories = await analytics_service.get_category_aggregation(db, start_time, end_time)
    trend = await analytics_service.get_trend(db, start_time, end_time, category, trend_interval)
    return AnalyticsResponse(summary=summary, categories=categories, trend=trend)


@router.get(
    "/export/excel",
    responses={
        401: {"description": "Invalid or expired token"},
    },
)
async def export_excel(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    category: Optional[str] = None,
) -> StreamingResponse:
    records, _ = await data_service.list_records(
        db, page=1, size=10000,
        category=category, start_time=start_time, end_time=end_time,
    )

    data = [
        {
            "ID": r.id,
            "Title": r.title,
            "Value": r.value,
            "Category": r.category,
            "Description": r.description,
            "Is Anomaly": r.is_anomaly,
            "Threshold": r.threshold,
            "Source": r.source,
            "Timestamp": r.timestamp,
        }
        for r in records
    ]

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=data_export.xlsx"},
    )
