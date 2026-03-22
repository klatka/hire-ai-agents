from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel

from app.models.task import TaskStatus


class TaskCreate(BaseModel):
    creator_agent_id: Optional[str] = None
    required_capability: str
    payload: Dict[str, Any] = {}
    budget: Optional[float] = None
    deadline: Optional[datetime] = None


class TaskResponse(BaseModel):
    id: str
    creator_agent_id: Optional[str]
    required_capability: str
    payload: Dict[str, Any]
    budget: Optional[float]
    deadline: Optional[datetime]
    status: str
    assigned_agent_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
