import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

from src.main import create_app
from src.models.state import PlanningState
from src.utils.store import InMemoryPlanStore

import pytest_asyncio

# Helper to mock graph output
async def mock_graph_ainvoke(initial_state: dict, final_state: dict):
    return final_state

@pytest_asyncio.fixture
async def app():
    app_instance = create_app()
    async with lifespan_context(app_instance):
        app_instance.state.store = InMemoryPlanStore()
        yield app_instance

@pytest.mark.asyncio
async def test_health_endpoint(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_valid_plan_creates_200(app):
    mock_final_state: PlanningState = {
        "raw_query": "trip to Dubai",
        "status": "COMPLETE",
        "errors": [],
        "warnings": []
    }
    
    with patch("src.main.graph_app.ainvoke", new_callable=AsyncMock) as mock_ainvoke:
        mock_ainvoke.return_value = mock_final_state
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/plan", json={"query": "trip to Dubai"})
            assert response.status_code == 200
            data = response.json()
            assert "plan_id" in data
            assert data["status"] == "completed"
            
            # Verify it's retrievable
            plan_id = data["plan_id"]
            get_response = await client.get(f"/api/v1/plan/{plan_id}")
            assert get_response.status_code == 200
            assert get_response.json()["plan_id"] == plan_id

@pytest.mark.asyncio
async def test_empty_query_422(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/plan", json={"query": "   "})
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"

@pytest.mark.asyncio
async def test_long_query_422(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/plan", json={"query": "a" * 1001})
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "QUERY_TOO_LONG"

@pytest.mark.asyncio
async def test_unknown_plan_404(app):
    import uuid
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(f"/api/v1/plan/{uuid.uuid4()}")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "PLAN_NOT_FOUND"

@pytest.mark.asyncio
async def test_partial_plan(app):
    mock_final_state: PlanningState = {
        "raw_query": "trip",
        "status": "PARTIAL",
        "warnings": ["Logistics failed"]
    }
    with patch("src.main.graph_app.ainvoke", new_callable=AsyncMock) as mock_ainvoke:
        mock_ainvoke.return_value = mock_final_state
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/plan", json={"query": "trip to Dubai"})
            assert response.status_code == 200
            assert response.json()["status"] == "partial"
            assert "Logistics failed" in response.json()["warnings"]

@pytest.mark.asyncio
async def test_timeout_504(app):
    async def slow_invoke(*args, **kwargs):
        await asyncio.sleep(0.5)
        return {}
        
    with patch("src.main.graph_app.ainvoke", new=slow_invoke):
        with patch("src.main.settings.request_timeout_seconds", 0.1): # very short timeout
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/v1/plan", json={"query": "trip to Dubai"})
                assert response.status_code == 504
                assert response.json()["error"]["code"] == "PLANNING_TIMEOUT"

@pytest.mark.asyncio
async def test_two_apps_dont_share_store():
    app1 = create_app()
    app2 = create_app()
    
    async with AsyncClient(transport=ASGITransport(app=app1), base_url="http://test") as client1:
        # We can check directly
        async with lifespan_context(app1):
            async with lifespan_context(app2):
                assert app1.state.store is not app2.state.store

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan_context(app):
    async with app.router.lifespan_context(app):
        yield
