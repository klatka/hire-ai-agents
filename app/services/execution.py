from typing import Any, Dict, Optional

import httpx

from app.core.config import settings
from app.models.agent import Agent
from app.models.task import Task, TaskStatus
from app.repositories.task_repository import TaskRepository
from app.repositories.task_result_repository import TaskResultRepository
from app.services.reputation import ReputationService


class ExecutionGateway:
    """Calls the assigned agent via HTTP and stores the result."""

    def __init__(
        self,
        task_repo: TaskRepository,
        result_repo: TaskResultRepository,
        reputation_service: ReputationService,
    ) -> None:
        self.task_repo = task_repo
        self.result_repo = result_repo
        self.reputation_service = reputation_service

    async def execute(self, task: Task, agent: Agent) -> Dict[str, Any]:
        await self.task_repo.update_status(task, TaskStatus.running)

        url = f"{agent.endpoint_url.rstrip('/')}/execute"
        request_body = {
            "task_id": task.id,
            "capability": task.required_capability,
            "payload": task.payload,
        }

        success = False
        result_payload: Optional[dict] = None
        error_message: Optional[str] = None
        latency_ms: Optional[float] = None

        try:
            async with httpx.AsyncClient(timeout=settings.EXECUTION_TIMEOUT_SECONDS) as client:
                response = await client.post(url, json=request_body)
                response.raise_for_status()
                data = response.json()

                if not isinstance(data, dict) or "success" not in data:
                    raise ValueError("Invalid response schema from agent")

                success = bool(data.get("success", False))
                result_payload = data.get("result")
                metrics = data.get("metrics", {})
                latency_ms = metrics.get("latency_ms") if isinstance(metrics, dict) else None

                if not success:
                    error_message = data.get("error", "Agent reported failure")

        except httpx.TimeoutException:
            error_message = "Agent request timed out"
        except httpx.ConnectError:
            error_message = "Agent endpoint unreachable"
        except httpx.HTTPStatusError as exc:
            error_message = f"Agent returned HTTP {exc.response.status_code}"
        except ValueError as exc:
            error_message = str(exc)
        except Exception as exc:
            error_message = f"Unexpected error: {exc}"

        await self.result_repo.create(
            task_id=task.id,
            agent_id=agent.id,
            success=success,
            result_payload=result_payload,
            error_message=error_message,
            latency_ms=latency_ms,
        )

        new_status = TaskStatus.completed if success else TaskStatus.failed
        await self.task_repo.update_status(task, new_status)

        await self.reputation_service.update_after_execution(agent, success, latency_ms)

        return {
            "success": success,
            "result": result_payload,
            "error": error_message,
            "latency_ms": latency_ms,
            "task_status": new_status.value,
        }
