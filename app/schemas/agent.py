from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, HttpUrl, Field


class AgentCreate(BaseModel):
    name: str
    description: str = ""
    endpoint_url: str
    capabilities: List[str] = Field(default_factory=list)
    price_per_request: float = 0.0
    avg_latency_ms: float = 0.0
    success_rate: float = 1.0
    is_active: bool = True


class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    endpoint_url: Optional[str] = None
    capabilities: Optional[List[str]] = None
    price_per_request: Optional[float] = None
    avg_latency_ms: Optional[float] = None
    success_rate: Optional[float] = None
    task_count: Optional[int] = None
    is_active: Optional[bool] = None


class AgentResponse(BaseModel):
    id: str
    name: str
    description: str
    endpoint_url: str
    capabilities: List[str]
    price_per_request: float
    avg_latency_ms: float
    success_rate: float
    task_count: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
