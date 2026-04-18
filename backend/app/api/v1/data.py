import io
import json
import math
from datetime import datetime
from typing import Annotated, Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_editor
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.data_record import DataRecordCreate, DataRecordListResponse, DataRecordResponse, DataRecordUpdate
from app.services import data_service

router = APIRouter(prefix="/data", tags=["data"])


@router.post("/", response_model=DataRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_record(
    payload: DataRecordCreate,
    current_user: Annotated[User, Depends(require_editor)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DataRecordResponse:
    record = await data_service.create_record(db, payload, current_user.id)
    return DataRecordResponse.model_validate(record)


@router.get("/", response_model=DataRecordListResponse)
async def list_records(
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    sort_by: str = Query("timestamp", pattern="^(timestamp|value|category|title)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
) -> DataRecordListResponse:
    records, total = await data_service.list_records(
        db, page=page, size=size, category=category,
        start_time=start_time, end_time=end_time,
        sort_by=sort_by, sort_order=sort_order,
    )
    return DataRecordListResponse(
        items=[DataRecordResponse.model_validate(r) for r in records],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
    )


@router.get("/{record_id}", response_model=DataRecordResponse)
async def get_record(
    record_id: int,
    _: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DataRecordResponse:
    record = await data_service.get_record(db, record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return DataRecordResponse.model_validate(record)


@router.patch("/{record_id}", response_model=DataRecordResponse)
async def update_record(
    record_id: int,
    payload: DataRecordUpdate,
    current_user: Annotated[User, Depends(require_editor)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DataRecordResponse:
    record = await data_service.get_record(db, record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    if record.creator_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the owner")
    updated = await data_service.update_record(db, record, payload)
    return DataRecordResponse.model_validate(updated)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_record(
    record_id: int,
    current_user: Annotated[User, Depends(require_editor)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    record = await data_service.get_record(db, record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    if record.creator_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the owner")
    await data_service.delete_record(db, record)


@router.post("/import/csv", status_code=status.HTTP_201_CREATED)
async def import_csv(
    file: Annotated[UploadFile, File()],
    current_user: Annotated[User, Depends(require_editor)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    content = await file.read()
    df = pd.read_csv(io.BytesIO(content), keep_default_na=False)
    records_data = df.to_dict(orient="records")
    count = await data_service.bulk_create_records(db, records_data, current_user.id, source="csv")
    return {"imported": count}


@router.post("/import/json", status_code=status.HTTP_201_CREATED)
async def import_json(
    file: Annotated[UploadFile, File()],
    current_user: Annotated[User, Depends(require_editor)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    content = await file.read()
    records_data = json.loads(content)
    if isinstance(records_data, dict):
        records_data = [records_data]
    count = await data_service.bulk_create_records(db, records_data, current_user.id, source="json")
    return {"imported": count}
