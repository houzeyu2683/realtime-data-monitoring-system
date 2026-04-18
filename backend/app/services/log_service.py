from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_log import SystemLog


async def create_log(
    db: AsyncSession,
    action: str,
    resource: str,
    user_id: Optional[int] = None,
    detail: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> SystemLog:
    log = SystemLog(
        action=action,
        resource=resource,
        user_id=user_id,
        detail=detail,
        ip_address=ip_address,
    )
    db.add(log)
    await db.commit()
    return log


async def list_logs(db: AsyncSession, page: int = 1, size: int = 50) -> tuple[list[SystemLog], int]:
    total_result = await db.execute(select(func.count()).select_from(SystemLog))
    total = total_result.scalar_one()

    result = await db.execute(
        select(SystemLog).order_by(SystemLog.created_at.desc()).offset((page - 1) * size).limit(size)
    )
    return list(result.scalars().all()), total
