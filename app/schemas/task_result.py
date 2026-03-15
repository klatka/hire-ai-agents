from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel


class TaskResultResponse(BaseModel):
    id: str
    task_id: str
    agent_id: str
    success: bool
    result_payload: Optional[Dict[str, Any]]
    error_message: Optional[str]
    latency_ms: Optional[float]
    created_at: datetime

    model_config = {"from_attributes": True}
