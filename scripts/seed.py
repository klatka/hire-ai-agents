"""
Seed the database with example agents.

Usage:
    python -m scripts.seed
"""
import asyncio

from app.db.session import init_db, AsyncSessionLocal
from app.repositories.agent_repository import AgentRepository
from app.schemas.agent import AgentCreate

SEED_AGENTS = [
    AgentCreate(
        name="TranslationAgent",
        description="Translates text between languages.",
        endpoint_url="http://mock-agent:8001",
        capabilities=["translate_text"],
        price_per_request=0.05,
        avg_latency_ms=500.0,
        success_rate=0.98,
    ),
    AgentCreate(
        name="SummarizationAgent",
        description="Summarizes long documents.",
        endpoint_url="http://mock-agent:8001",
        capabilities=["summarize_text"],
        price_per_request=0.10,
        avg_latency_ms=800.0,
        success_rate=0.95,
    ),
    AgentCreate(
        name="ClassificationAgent",
        description="Classifies text into categories.",
        endpoint_url="http://mock-agent:8001",
        capabilities=["classify_text"],
        price_per_request=0.03,
        avg_latency_ms=200.0,
        success_rate=0.99,
    ),
]


async def seed() -> None:
    await init_db()
    async with AsyncSessionLocal() as db:
        repo = AgentRepository(db)
        existing = await repo.list_all()
        existing_names = {a.name for a in existing}
        for agent_data in SEED_AGENTS:
            if agent_data.name not in existing_names:
                created = await repo.create(agent_data)
                print(f"Created agent: {created.name} (id={created.id})")
            else:
                print(f"Agent already exists: {agent_data.name}")
    print("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())
