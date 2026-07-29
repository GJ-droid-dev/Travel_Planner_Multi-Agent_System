import pytest
from datetime import datetime

from src.models.request import TravelRequest
from src.models.agent_io import AgentTask, AgentType, ResultStatus
from src.utils.llm import LLMClient

from src.agents.orchestrator import OrchestratorAgent, OrchestratorResponse
from src.agents.destination import DestinationAgent, DestinationResponse
from src.agents.logistics import LogisticsAgent, LogisticsResponse
from src.agents.budget import BudgetAgent, BudgetResponse
from src.agents.review import ReviewAgent, ReviewResponse

class MockLLMClient(LLMClient):
    async def call(self, system_prompt: str, user_prompt: str, response_model):
        if response_model == OrchestratorResponse:
            return OrchestratorResponse(destination="Dubai", duration_days=5, budget_usd=3000)
        elif response_model == DestinationResponse:
            return DestinationResponse(
                recommended_activities=[], must_do=[], nice_to_have=[], 
                food_recommendations=[], area_suggestions=[]
            )
        elif response_model == LogisticsResponse:
            return LogisticsResponse(
                accommodation={"plan": [], "estimated_cost_usd": 0},
                daily_sequences=[],
                transport_summary={"primary_mode": "metro", "estimated_transport_cost_usd": 0},
                confidence=0.9
            )
        elif response_model == BudgetResponse:
            return BudgetResponse(
                budget_breakdown={
                    "total_budget_usd": 3000, "estimated_total_usd": 2500,
                    "remaining_usd": 500, "within_budget": True,
                    "categories": {"stay": 1000, "transport": 200, "food": 500, "activities": 800}
                }
            )
        elif response_model == ReviewResponse:
            return ReviewResponse(
                approved=True, score=1.0, checks={}, feedback=[], revision_needed=False
            )
        else:
            raise ValueError(f"Unknown response model: {response_model}")

@pytest.fixture
def mock_task():
    req = TravelRequest(
        raw_query="5 days in Dubai, $3000 budget, prefer downtown",
        destination="Dubai",
        duration_days=5,
        budget_usd=3000,
        areas=["Downtown Dubai"],
        preferences=[],
        avoidances=[],
        travelers=2
    )
    return AgentTask(
        task_id="test-task",
        agent_type=AgentType.ORCHESTRATOR,
        request=req,
        created_at=datetime.utcnow()
    )

@pytest.mark.asyncio
async def test_orchestrator_agent(mock_task):
    mock_task.agent_type = AgentType.ORCHESTRATOR
    agent = OrchestratorAgent(MockLLMClient())
    result = await agent.execute(mock_task)
    assert result.status == ResultStatus.SUCCESS
    assert result.payload["destination"] == "Dubai"

@pytest.mark.asyncio
async def test_destination_agent(mock_task):
    mock_task.agent_type = AgentType.DESTINATION
    agent = DestinationAgent(MockLLMClient())
    result = await agent.execute(mock_task)
    assert result.status == ResultStatus.SUCCESS

@pytest.mark.asyncio
async def test_logistics_agent(mock_task):
    mock_task.agent_type = AgentType.LOGISTICS
    agent = LogisticsAgent(MockLLMClient())
    result = await agent.execute(mock_task)
    assert result.status == ResultStatus.SUCCESS

@pytest.mark.asyncio
async def test_budget_agent(mock_task):
    mock_task.agent_type = AgentType.BUDGET
    agent = BudgetAgent(MockLLMClient())
    result = await agent.execute(mock_task)
    assert result.status == ResultStatus.SUCCESS
    assert result.payload["budget_breakdown"]["within_budget"] is True

@pytest.mark.asyncio
async def test_review_agent(mock_task):
    mock_task.agent_type = AgentType.REVIEW
    agent = ReviewAgent(MockLLMClient())
    result = await agent.execute(mock_task)
    assert result.status == ResultStatus.SUCCESS
    assert result.payload["approved"] is True
