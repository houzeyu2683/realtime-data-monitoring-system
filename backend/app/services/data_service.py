import math
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_record import DataRecord
from app.schemas.data_record import DataRecordCreate, DataRecordUpdate


def _check_anomaly(value: float, threshold: Optional[float]) -> bool:
    return threshold is not None and value > threshold


async def create_record(
    db: AsyncSession, payload: DataRecordCreate, creator_id: int, source: str = "manual"
) -> DataRecord:
    timestamp = payload.timestamp or datetime.now(timezone.utc)
    record = DataRecord(
        title=payload.title,
        value=payload.value,
        category=payload.category,
        description=payload.description,
        threshold=payload.threshold,
        is_anomaly=_check_anomaly(payload.value, payload.threshold),
        source=source,
        creator_id=creator_id,
        timestamp=timestamp,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def get_record(db: AsyncSession, record_id: int) -> Optional[DataRecord]:
    result = await db.execute(select(DataRecord).where(DataRecord.id == record_id))
    return result.scalar_one_or_none()


async def list_records(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    category: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    sort_by: str = "timestamp",
    sort_order: str = "desc",
) -> tuple[list[DataRecord], int]:
    filters = []
    if category:
        filters.append(DataRecord.category == category)
    if start_time:
        filters.append(DataRecord.timestamp >= start_time)
    if end_time:
        filters.append(DataRecord.timestamp <= end_time)

    where_clause = and_(*filters) if filters else True

    total_result = await db.execute(select(func.count()).select_from(DataRecord).where(where_clause))
    total = total_result.scalar_one()

    order_col = getattr(DataRecord, sort_by, DataRecord.timestamp)
    order = order_col.desc() if sort_order == "desc" else order_col.asc()

    result = await db.execute(
        select(DataRecord).where(where_clause).order_by(order).offset((page - 1) * size).limit(size)
    )
    return list(result.scalars().all()), total


async def update_record(db: AsyncSession, record: DataRecord, payload: DataRecordUpdate) -> DataRecord:
    if payload.title is not None:
        record.title = payload.title
    if payload.value is not None:
        record.value = payload.value
    if payload.category is not None:
        record.category = payload.category
    if payload.description is not None:
        record.description = payload.description
    if payload.threshold is not None:
        record.threshold = payload.threshold
    record.is_anomaly = _check_anomaly(record.value, record.threshold)
    await db.commit()
    await db.refresh(record)
    return record


async def delete_record(db: AsyncSession, record: DataRecord) -> None:
    await db.delete(record)
    await db.commit()


async def bulk_create_records(
    db: AsyncSession, records_data: list[dict], creator_id: int, source: str = "import"
) -> int:
    records = [
        DataRecord(
            title=r.get("title", ""),
            value=float(r.get("value", 0)),
            category=r.get("category", "default"),
            description=r.get("description"),
            threshold=float(r["threshold"]) if r.get("threshold") else None,
            is_anomaly=_check_anomaly(float(r.get("value", 0)), float(r["threshold"]) if r.get("threshold") else None),
            source=source,
            creator_id=creator_id,
            timestamp=datetime.fromisoformat(r["timestamp"]) if r.get("timestamp") else datetime.now(timezone.utc),
        )
        for r in records_data
    ]
    db.add_all(records)
    await db.commit()
    return len(records)
