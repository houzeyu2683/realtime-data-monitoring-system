from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DataRecordCreate(BaseModel):
    title: str
    value: float
    category: str
    description: Optional[str] = None
    threshold: Optional[float] = None
    timestamp: Optional[datetime] = None


class DataRecordUpdate(BaseModel):
    title: Optional[str] = None
    value: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None
    threshold: Optional[float] = None


class DataRecordResponse(BaseModel):
    id: int
    title: str
    value: float
    category: str
    description: Optional[str]
    is_anomaly: bool
    threshold: Optional[float]
    source: str
    creator_id: int
    timestamp: datetime
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DataRecordListResponse(BaseModel):
    items: list[DataRecordResponse]
    total: int
    page: int
    size: int
    pages: int
