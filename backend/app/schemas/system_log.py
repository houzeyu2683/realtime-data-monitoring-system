from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SystemLogResponse(BaseModel):
    id: int
    action: str
    resource: str
    detail: Optional[str]
    ip_address: Optional[str]
    user_id: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class SystemLogListResponse(BaseModel):
    items: list[SystemLogResponse]
    total: int
    page: int
    size: int
