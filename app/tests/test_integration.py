"""
Integration test for the full end-to-end flow:
register agent → create task → match → execute → verify result
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import httpx


def _make_mock_http_client(response_json: dict) -> tuple:
    """Return (mock_cls, mock_instance) with properly wired async context manager."""
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()  # no-op for 200
    mock_response.json = MagicMock(return_value=response_json)

    mock_instance = MagicMock()
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock(return_value=False)
    mock_instance.post = AsyncMock(return_value=mock_response)

    mock_cls = MagicMock(return_value=mock_instance)
    return mock_cls, mock_instance


@pytest.mark.asyncio
async def test_end_to_end_flow(client):
    # 1. Register a TranslationAgent
    agent_resp = await client.post("/agents", json={
        "name": "TranslationAgent",
        "description": "Translates text",
        "endpoint_url": "http://mock-agent:8001",
        "capabilities": ["translate_text"],
        "price_per_request": 0.05,
        "avg_latency_ms": 500.0,
        "success_rate": 0.98,
    })
    assert agent_resp.status_code == 201
    agent = agent_resp.json()
    agent_id = agent["id"]

    # 2. Create a task
    task_resp = await client.post("/tasks", json={
        "required_capability": "translate_text",
        "payload": {"text": "Hello world", "source_language": "en", "target_language": "de"},
        "budget": 1.0,
    })
    assert task_resp.status_code == 201
    task = task_resp.json()
    task_id = task["id"]
    assert task["status"] == "open"

    # 3. Match the task
    match_resp = await client.post(f"/tasks/{task_id}/match")
    assert match_resp.status_code == 200
    matched = match_resp.json()
    assert matched["status"] == "matched"
    assert matched["assigned_agent_id"] == agent_id

    # 4. Execute via mocked HTTP call to the agent
    mock_cls, _ = _make_mock_http_client({
        "success": True,
        "result": {"translated_text": "Hallo Welt"},
        "metrics": {"latency_ms": 820},
    })

    with patch("app.services.execution.httpx.AsyncClient", mock_cls):
        execute_resp = await client.post(f"/tasks/{task_id}/execute")

    assert execute_resp.status_code == 200
    exec_data = execute_resp.json()
    assert exec_data["success"] is True
    assert exec_data["task_status"] == "completed"

    # 5. Task status should be completed
    task_resp2 = await client.get(f"/tasks/{task_id}")
    assert task_resp2.status_code == 200
    assert task_resp2.json()["status"] == "completed"

    # 6. Result should be stored
    results_resp = await client.get(f"/tasks/{task_id}/results")
    assert results_resp.status_code == 200
    results = results_resp.json()
    assert len(results) == 1
    assert results[0]["success"] is True
    assert results[0]["latency_ms"] == 820

    # 7. Reputation metrics should be updated
    agent_resp2 = await client.get(f"/agents/{agent_id}")
    assert agent_resp2.status_code == 200
    updated_agent = agent_resp2.json()
    assert updated_agent["task_count"] == 1
    # success_rate should remain ~0.98 after one successful task from 0.98 baseline * 0 + 1 / 1
    # initial task_count was 0, so new success_rate = (0.98 * 0 + 1) / 1 = 1.0
    assert updated_agent["success_rate"] == 1.0
    assert updated_agent["avg_latency_ms"] == 820.0
