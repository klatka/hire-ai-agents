from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.task import TaskStatus
from app.repositories.agent_repository import AgentRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.task_result_repository import TaskResultRepository
from app.schemas.task import TaskCreate, TaskResponse
from app.schemas.task_result import TaskResultResponse
from app.services.execution import ExecutionGateway
from app.services.matching import MatchingService
from app.services.reputation import ReputationService

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _task_repo(db: AsyncSession = Depends(get_db)) -> TaskRepository:
    return TaskRepository(db)


def _agent_repo(db: AsyncSession = Depends(get_db)) -> AgentRepository:
    return AgentRepository(db)


def _result_repo(db: AsyncSession = Depends(get_db)) -> TaskResultRepository:
    return TaskResultRepository(db)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(data: TaskCreate, repo: TaskRepository = Depends(_task_repo)):
    return await repo.create(data)


@router.get("", response_model=List[TaskResponse])
async def list_tasks(repo: TaskRepository = Depends(_task_repo)):
    return await repo.list_all()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, repo: TaskRepository = Depends(_task_repo)):
    task = await repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/match", response_model=TaskResponse)
async def match_task(
    task_id: str,
    task_repo: TaskRepository = Depends(_task_repo),
    agent_repo: AgentRepository = Depends(_agent_repo),
):
    task = await task_repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != TaskStatus.open.value:
        raise HTTPException(status_code=400, detail=f"Task status is '{task.status}', expected 'open'")

    matcher = MatchingService(agent_repo)
    agent = await matcher.find_best_agent(task.required_capability, task.budget)

    if not agent:
        raise HTTPException(
            status_code=404,
            detail="No suitable agent found for this task",
        )

    updated = await task_repo.update_status(task, TaskStatus.matched, agent.id)
    return updated


@router.post("/{task_id}/execute")
async def execute_task(
    task_id: str,
    task_repo: TaskRepository = Depends(_task_repo),
    agent_repo: AgentRepository = Depends(_agent_repo),
    result_repo: TaskResultRepository = Depends(_result_repo),
):
    task = await task_repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != TaskStatus.matched.value:
        raise HTTPException(
            status_code=400,
            detail=f"Task status is '{task.status}', expected 'matched'",
        )
    if not task.assigned_agent_id:
        raise HTTPException(status_code=400, detail="Task has no assigned agent")

    agent = await agent_repo.get(task.assigned_agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Assigned agent not found")

    reputation_svc = ReputationService(agent_repo, result_repo)
    gateway = ExecutionGateway(task_repo, result_repo, reputation_svc)
    result = await gateway.execute(task, agent)
    return result


@router.get("/{task_id}/results", response_model=List[TaskResultResponse])
async def get_task_results(
    task_id: str,
    task_repo: TaskRepository = Depends(_task_repo),
    result_repo: TaskResultRepository = Depends(_result_repo),
):
    task = await task_repo.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return await result_repo.list_by_task(task_id)
