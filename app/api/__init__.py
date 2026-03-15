from fastapi import APIRouter

from app.api.agents import router as agents_router
from app.api.tasks import router as tasks_router

api_router = APIRouter()
api_router.include_router(agents_router)
api_router.include_router(tasks_router)
