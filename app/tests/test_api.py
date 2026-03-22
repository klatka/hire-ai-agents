"""
API tests for agents and tasks endpoints.
"""
import pytest


@pytest.mark.asyncio
async def test_create_agent(client):
    resp = await client.post("/agents", json={
        "name": "TestAgent",
        "description": "A test agent",
        "endpoint_url": "http://localhost:9000",
        "capabilities": ["test_cap"],
        "price_per_request": 0.05,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "TestAgent"
    assert data["capabilities"] == ["test_cap"]
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_list_agents(client):
    await client.post("/agents", json={
        "name": "Agent1",
        "endpoint_url": "http://localhost:9001",
        "capabilities": ["cap_a"],
    })
    resp = await client.get("/agents")
    assert resp.status_code == 200
    agents = resp.json()
    assert len(agents) >= 1


@pytest.mark.asyncio
async def test_get_agent(client):
    create_resp = await client.post("/agents", json={
        "name": "Agent2",
        "endpoint_url": "http://localhost:9002",
        "capabilities": ["cap_b"],
    })
    agent_id = create_resp.json()["id"]
    resp = await client.get(f"/agents/{agent_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == agent_id


@pytest.mark.asyncio
async def test_get_agent_not_found(client):
    resp = await client.get("/agents/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_agent(client):
    create_resp = await client.post("/agents", json={
        "name": "Agent3",
        "endpoint_url": "http://localhost:9003",
        "capabilities": ["cap_c"],
    })
    agent_id = create_resp.json()["id"]
    resp = await client.patch(f"/agents/{agent_id}", json={"name": "UpdatedAgent"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "UpdatedAgent"


@pytest.mark.asyncio
async def test_delete_agent(client):
    create_resp = await client.post("/agents", json={
        "name": "Agent4",
        "endpoint_url": "http://localhost:9004",
        "capabilities": ["cap_d"],
    })
    agent_id = create_resp.json()["id"]
    resp = await client.delete(f"/agents/{agent_id}")
    assert resp.status_code == 204
    # Agent should be soft-disabled, still readable but is_active=False
    get_resp = await client.get(f"/agents/{agent_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["is_active"] is False


@pytest.mark.asyncio
async def test_create_task(client):
    resp = await client.post("/tasks", json={
        "required_capability": "translate_text",
        "payload": {"text": "Hello"},
        "budget": 1.0,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "open"
    assert data["required_capability"] == "translate_text"


@pytest.mark.asyncio
async def test_list_tasks(client):
    await client.post("/tasks", json={"required_capability": "test_cap"})
    resp = await client.get("/tasks")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_get_task_not_found(client):
    resp = await client.get("/tasks/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_match_task_no_agent(client):
    task_resp = await client.post("/tasks", json={
        "required_capability": "unknown_capability",
    })
    task_id = task_resp.json()["id"]
    resp = await client.post(f"/tasks/{task_id}/match")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_match_task_success(client):
    # Create an agent
    agent_resp = await client.post("/agents", json={
        "name": "MatchAgent",
        "endpoint_url": "http://localhost:9999",
        "capabilities": ["match_cap"],
        "price_per_request": 0.10,
    })
    assert agent_resp.status_code == 201

    # Create task
    task_resp = await client.post("/tasks", json={
        "required_capability": "match_cap",
        "budget": 1.0,
    })
    task_id = task_resp.json()["id"]

    # Match
    match_resp = await client.post(f"/tasks/{task_id}/match")
    assert match_resp.status_code == 200
    data = match_resp.json()
    assert data["status"] == "matched"
    assert data["assigned_agent_id"] == agent_resp.json()["id"]


@pytest.mark.asyncio
async def test_match_already_matched_task(client):
    agent_resp = await client.post("/agents", json={
        "name": "MatchAgent2",
        "endpoint_url": "http://localhost:9998",
        "capabilities": ["match_cap2"],
    })
    task_resp = await client.post("/tasks", json={"required_capability": "match_cap2"})
    task_id = task_resp.json()["id"]
    await client.post(f"/tasks/{task_id}/match")
    resp = await client.post(f"/tasks/{task_id}/match")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_get_task_results_empty(client):
    task_resp = await client.post("/tasks", json={"required_capability": "some_cap"})
    task_id = task_resp.json()["id"]
    resp = await client.get(f"/tasks/{task_id}/results")
    assert resp.status_code == 200
    assert resp.json() == []
