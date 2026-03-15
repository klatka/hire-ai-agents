import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy import String, Boolean, Float, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    endpoint_url: Mapped[str] = mapped_column(String(512), nullable=False)
    capabilities: Mapped[List[str]] = mapped_column(JSON, nullable=False, default=list)
    price_per_request: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_latency_ms: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    success_rate: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    task_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)
