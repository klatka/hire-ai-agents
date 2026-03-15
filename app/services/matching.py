from typing import List, Optional

from app.models.agent import Agent
from app.repositories.agent_repository import AgentRepository


class MatchingService:
    """
    Deterministic rule-based matching engine.

    Ranking priority:
      1. highest success_rate
      2. lowest price_per_request
      3. lowest avg_latency_ms
    """

    def __init__(self, agent_repo: AgentRepository) -> None:
        self.agent_repo = agent_repo

    async def find_best_agent(
        self, required_capability: str, budget: Optional[float] = None
    ) -> Optional[Agent]:
        candidates = await self.agent_repo.list_active_with_capability(required_capability)

        if budget is not None:
            candidates = [a for a in candidates if a.price_per_request <= budget]

        if not candidates:
            return None

        candidates.sort(
            key=lambda a: (-a.success_rate, a.price_per_request, a.avg_latency_ms)
        )
        return candidates[0]
