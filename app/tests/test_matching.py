"""
Unit tests for the matching engine.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.matching import MatchingService


def make_agent(**kwargs) -> MagicMock:
    """Create a lightweight agent mock without touching SQLAlchemy ORM machinery."""
    defaults = dict(
        id="agent-1",
        name="TestAgent",
        description="",
        endpoint_url="http://localhost:8001",
        capabilities=["translate_text"],
        price_per_request=0.05,
        avg_latency_ms=500.0,
        success_rate=0.95,
        task_count=0,
        is_active=True,
    )
    defaults.update(kwargs)
    agent = MagicMock()
    for k, v in defaults.items():
        setattr(agent, k, v)
    return agent


@pytest.mark.asyncio
async def test_find_best_agent_returns_none_when_no_candidates():
    repo = AsyncMock()
    repo.list_active_with_capability.return_value = []
    svc = MatchingService(repo)
    result = await svc.find_best_agent("translate_text")
    assert result is None


@pytest.mark.asyncio
async def test_find_best_agent_returns_agent_matching_capability():
    agent = make_agent()
    repo = AsyncMock()
    repo.list_active_with_capability.return_value = [agent]
    svc = MatchingService(repo)
    result = await svc.find_best_agent("translate_text")
    assert result is agent


@pytest.mark.asyncio
async def test_find_best_agent_filters_by_budget():
    cheap = make_agent(id="cheap", price_per_request=0.02)
    expensive = make_agent(id="expensive", price_per_request=0.99)
    repo = AsyncMock()
    repo.list_active_with_capability.return_value = [cheap, expensive]
    svc = MatchingService(repo)
    result = await svc.find_best_agent("translate_text", budget=0.05)
    assert result is cheap


@pytest.mark.asyncio
async def test_find_best_agent_budget_excludes_all():
    expensive = make_agent(id="expensive", price_per_request=0.99)
    repo = AsyncMock()
    repo.list_active_with_capability.return_value = [expensive]
    svc = MatchingService(repo)
    result = await svc.find_best_agent("translate_text", budget=0.01)
    assert result is None


@pytest.mark.asyncio
async def test_find_best_agent_ranks_by_success_rate_first():
    low = make_agent(id="low", success_rate=0.80, price_per_request=0.01, avg_latency_ms=10.0)
    high = make_agent(id="high", success_rate=0.99, price_per_request=0.99, avg_latency_ms=999.0)
    repo = AsyncMock()
    repo.list_active_with_capability.return_value = [low, high]
    svc = MatchingService(repo)
    result = await svc.find_best_agent("translate_text")
    assert result is high


@pytest.mark.asyncio
async def test_find_best_agent_ranks_by_price_second():
    a1 = make_agent(id="a1", success_rate=0.95, price_per_request=0.10, avg_latency_ms=100.0)
    a2 = make_agent(id="a2", success_rate=0.95, price_per_request=0.02, avg_latency_ms=500.0)
    repo = AsyncMock()
    repo.list_active_with_capability.return_value = [a1, a2]
    svc = MatchingService(repo)
    result = await svc.find_best_agent("translate_text")
    assert result is a2


@pytest.mark.asyncio
async def test_find_best_agent_ranks_by_latency_third():
    a1 = make_agent(id="a1", success_rate=0.95, price_per_request=0.05, avg_latency_ms=1000.0)
    a2 = make_agent(id="a2", success_rate=0.95, price_per_request=0.05, avg_latency_ms=100.0)
    repo = AsyncMock()
    repo.list_active_with_capability.return_value = [a1, a2]
    svc = MatchingService(repo)
    result = await svc.find_best_agent("translate_text")
    assert result is a2
