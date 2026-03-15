from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task_result import TaskResult


class TaskResultRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        task_id: str,
        agent_id: str,
        success: bool,
        result_payload: Optional[dict],
        error_message: Optional[str],
        latency_ms: Optional[float],
    ) -> TaskResult:
        record = TaskResult(
            task_id=task_id,
            agent_id=agent_id,
            success=success,
            result_payload=result_payload,
            error_message=error_message,
            latency_ms=latency_ms,
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def list_by_task(self, task_id: str) -> List[TaskResult]:
        result = await self.db.execute(
            select(TaskResult).where(TaskResult.task_id == task_id)
        )
        return list(result.scalars().all())

    async def list_by_agent(self, agent_id: str) -> List[TaskResult]:
        result = await self.db.execute(
            select(TaskResult).where(TaskResult.agent_id == agent_id)
        )
        return list(result.scalars().all())
