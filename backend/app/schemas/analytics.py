from datetime import datetime

from pydantic import BaseModel


class AnalyticsSummary(BaseModel):
    total: int
    total_value: float
    avg_value: float
    max_value: float
    min_value: float
    anomaly_count: int


class CategoryAggregation(BaseModel):
    category: str
    count: int
    avg_value: float
    total_value: float


class TrendPoint(BaseModel):
    timestamp: datetime
    category: str
    avg_value: float
    count: int
    anomaly_count: int


class AnalyticsResponse(BaseModel):
    summary: AnalyticsSummary
    categories: list[CategoryAggregation]
    trend: list[TrendPoint]
