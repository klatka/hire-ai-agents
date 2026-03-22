from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate


class TaskRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, data: TaskCreate) -> Task:
        task = Task(**data.model_dump())
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def get(self, task_id: str) -> Optional[Task]:
        result = await self.db.execute(select(Task).where(Task.id == task_id))
        return result.scalar_one_or_none()

    async def list_all(self) -> List[Task]:
        result = await self.db.execute(select(Task))
        return list(result.scalars().all())

    async def update_status(
        self,
        task: Task,
        status: TaskStatus,
        assigned_agent_id: Optional[str] = None,
    ) -> Task:
        task.status = status.value
        task.updated_at = datetime.now(timezone.utc)
        if assigned_agent_id is not None:
            task.assigned_agent_id = assigned_agent_id
        await self.db.commit()
        await self.db.refresh(task)
        return task
