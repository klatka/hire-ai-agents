from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import api_router
from app.core.config import settings
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="Hire AI Agents — Autonomous Agent Task Marketplace",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}
