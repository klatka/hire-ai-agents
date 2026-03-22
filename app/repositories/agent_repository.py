from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentUpdate


class AgentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, data: AgentCreate) -> Agent:
        agent = Agent(**data.model_dump())
        self.db.add(agent)
        await self.db.commit()
        await self.db.refresh(agent)
        return agent

    async def get(self, agent_id: str) -> Optional[Agent]:
        result = await self.db.execute(select(Agent).where(Agent.id == agent_id))
        return result.scalar_one_or_none()

    async def list_all(self) -> List[Agent]:
        result = await self.db.execute(select(Agent))
        return list(result.scalars().all())

    async def update(self, agent: Agent, data: AgentUpdate) -> Agent:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(agent, field, value)
        await self.db.commit()
        await self.db.refresh(agent)
        return agent

    async def delete(self, agent: Agent) -> None:
        await self.db.delete(agent)
        await self.db.commit()

    async def list_active_with_capability(self, capability: str) -> List[Agent]:
        result = await self.db.execute(select(Agent).where(Agent.is_active))
        agents = result.scalars().all()
        return [a for a in agents if capability in (a.capabilities or [])]
