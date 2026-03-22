from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.repositories.agent_repository import AgentRepository
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse

router = APIRouter(prefix="/agents", tags=["agents"])


def _repo(db: AsyncSession = Depends(get_db)) -> AgentRepository:
    return AgentRepository(db)


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(data: AgentCreate, repo: AgentRepository = Depends(_repo)):
    return await repo.create(data)


@router.get("", response_model=List[AgentResponse])
async def list_agents(repo: AgentRepository = Depends(_repo)):
    return await repo.list_all()


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, repo: AgentRepository = Depends(_repo)):
    agent = await repo.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str, data: AgentUpdate, repo: AgentRepository = Depends(_repo)
):
    agent = await repo.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return await repo.update(agent, data)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(agent_id: str, repo: AgentRepository = Depends(_repo)):
    agent = await repo.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    # Soft-disable first; hard-delete is also fine for MVP
    await repo.update(agent, AgentUpdate(is_active=False))
