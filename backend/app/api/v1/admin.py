from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.data_record import DataRecord
from app.models.system_log import SystemLog
from app.models.user import User
from app.schemas.system_log import SystemLogListResponse, SystemLogResponse
from app.services import log_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/logs", response_model=SystemLogListResponse)
async def get_logs(
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
) -> SystemLogListResponse:
    logs, total = await log_service.list_logs(db, page=page, size=size)
    return SystemLogListResponse(
        items=[SystemLogResponse.model_validate(log) for log in logs],
        total=total,
        page=page,
        size=size,
    )


@router.get("/db-status")
async def db_status(
    _: Annotated[User, Depends(require_admin)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    version = (await db.execute(select(func.version()))).scalar_one()

    tables = []
    for model, name in [
        (User, "users"),
        (DataRecord, "data_records"),
        (SystemLog, "system_logs"),
    ]:
        count = (await db.execute(select(func.count()).select_from(model))).scalar_one()
        tables.append({"table": name, "rows": count})

    return {"db_version": version, "tables": tables}
