"""Integration Tests for FastAPI Endpoints."""
import pytest
from httpx import ASGITransport, AsyncClient
from app.database.session import init_db
from app.main import app


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_task_submission_and_retrieval():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Submit task
        create_resp = await ac.post(
            "/api/tasks",
            json={
                "prompt": "Analyze sales.csv and produce sales_chart.png",
                "max_retries": 3,
            },
        )
        assert create_resp.status_code == 202
        task_id = create_resp.json()["task_id"]
        assert task_id is not None

        # 2. Get task status
        get_resp = await ac.get(f"/api/tasks/{task_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["task_id"] == task_id
        assert data["prompt"] == "Analyze sales.csv and produce sales_chart.png"

        # 3. List tasks
        list_resp = await ac.get("/api/tasks")
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert len(list_data["tasks"]) >= 1
        assert "stats" in list_data
