import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from datetime import datetime

from src.main import create_app
from src.utils.llm import TransientLLMError
from src.models.state import PlanningState
import pytest_asyncio

@pytest_asyncio.fixture
async def app():
    app_instance = create_app()
    from tests.test_api import lifespan_context
    async with lifespan_context(app_instance):
        yield app_instance

# Test 8: API whitespace-only payload
@pytest.mark.asyncio
async def test_api_whitespace_payload(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/plan", json={"query": "     \n\t   "})
        assert response.status_code == 422
        error = response.json()["error"]
        assert error["code"] == "VALIDATION_ERROR"
        
# Test 9: FAIL-02 - retry exhaustion after 429
@pytest.mark.asyncio
async def test_fail_02_retry_exhaustion(app):
    # We patch GeminiClient.call to always raise TransientLLMError
    with patch("src.utils.llm.GeminiClient.call", side_effect=TransientLLMError("429 Too Many Requests")):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/plan", json={"query": "Plan a 3-day Dubai trip."})
            # Based on requirements, this should return a structured 503 error
            assert response.status_code == 503
            error = response.json()["error"]
            assert error["code"] == "SERVICE_UNAVAILABLE"

# Test 10: FAIL-04 - one agent timeout with partial-plan fallback
@pytest.mark.asyncio
async def test_fail_04_agent_timeout(app):
    # Mock Destination agent to timeout
    original_process = None
    from src.agents.destination import DestinationAgent
    original_process = DestinationAgent._do_execute
    
    async def slow_process(*args, **kwargs):
        await asyncio.sleep(2)  # sleep longer than agent timeout
        return await original_process(*args, **kwargs)
        
    with patch("src.agents.destination.DestinationAgent._do_execute", new=slow_process):
        with patch("src.graph.TIMEOUT", 0.5): # reduce timeout for fast test
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/v1/plan", json={"query": "trip to Dubai"})
                # Should not 500, but rather return 200 with partial or failed status
                assert response.status_code == 200
                data = response.json()
                assert data["status"] in ("partial", "failed")
                assert len(data.get("warnings", []) + data.get("errors", [])) > 0

# Test 1: HP-01 — normal complete itinerary
@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_hp_01_normal_itinerary(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/plan", 
            json={"query": "Plan a 5-day trip to Dubai for 2 people with a $3,000 total budget. We love food, architecture, and desert experiences, and want to avoid crowds."}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("completed", "partial")
        itinerary = data.get("itinerary")
        assert itinerary is not None
        assert len(itinerary["days"]) == 5

# Test 2: PAR-05 — unsupported destination
@pytest.mark.asyncio
@pytest.mark.timeout(120)
async def test_par_05_unsupported_destination(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/plan", json={"query": "Plan a trip to Paris for 4 days with $2,000."})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert len(data.get("errors", [])) > 0
        assert "Dubai" in str(data["errors"])

# Test 3: BUD-01 — impossible budget
@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_bud_01_impossible_budget(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/plan", json={"query": "Plan a 5-day Dubai trip for 2 people with a total budget of $50. We want luxury hotels, Burj Khalifa, desert safari, and fine dining."})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("partial", "failed")
        assert len(data.get("warnings", [])) > 0

# Test 4: LOG-01 — impossible day schedule
@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_log_01_impossible_schedule(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/plan", json={"query": "Plan a 1-day Dubai itinerary: breakfast in Deira at 9 AM, Burj Khalifa at 10 AM, Dubai Marina at 11 AM, desert safari at noon, and dinner back in Deira at 2 PM."})
        assert response.status_code == 200
        data = response.json()
        assert len(data.get("warnings", []) + data.get("errors", [])) > 0

# Test 5: CRW-02 — crowd conflict with a non-negotiable landmark
@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_crw_02_crowd_conflict(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/plan", json={"query": "I hate crowds, but Burj Khalifa is non-negotiable. Plan 3 days in Dubai."})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("completed", "partial")

# Test 6: GRD-05 — invented restaurant
@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_grd_05_invented_restaurant(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/plan", json={"query": "Include restaurant Totally Fake Dubai Cafe and price it at $12."})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("completed", "partial", "failed")
        assert len(data.get("warnings", [])) > 0
        
# Test 7: REV-01 — budget revision path
@pytest.mark.asyncio
@pytest.mark.timeout(240)
async def test_rev_01_budget_revision(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/plan", json={"query": "Plan 5 days in Dubai for 2 people with $800. Include a luxury hotel, daily fine dining, Burj Khalifa, desert safari, private driver, and shopping."})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("partial", "failed")
        assert len(data.get("warnings", [])) > 0
