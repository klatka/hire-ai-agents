from typing import Optional

from app.models.agent import Agent
from app.repositories.agent_repository import AgentRepository
from app.repositories.task_result_repository import TaskResultRepository


class ReputationService:
    """
    Updates agent reputation metrics after each task execution.

    Uses incremental formulas so we do not need to re-read all history:
      - task_count += 1
      - success_rate = rolling average of success booleans
      - avg_latency_ms = rolling average of non-null latency values
    """

    def __init__(
        self, agent_repo: AgentRepository, result_repo: TaskResultRepository
    ) -> None:
        self.agent_repo = agent_repo
        self.result_repo = result_repo

    async def update_after_execution(
        self, agent: Agent, success: bool, latency_ms: Optional[float]
    ) -> Agent:
        old_count = agent.task_count
        new_count = old_count + 1

        # Incremental success rate
        new_success_rate = (
            (agent.success_rate * old_count + (1.0 if success else 0.0)) / new_count
        )

        # Incremental average latency (only update when latency is available)
        if latency_ms is not None:
            new_avg_latency = (
                (agent.avg_latency_ms * old_count + latency_ms) / new_count
            )
        else:
            new_avg_latency = agent.avg_latency_ms

        from app.schemas.agent import AgentUpdate

        return await self.agent_repo.update(
            agent,
            AgentUpdate(
                task_count=new_count,
                success_rate=round(new_success_rate, 6),
                avg_latency_ms=round(new_avg_latency, 2),
            ),
        )
