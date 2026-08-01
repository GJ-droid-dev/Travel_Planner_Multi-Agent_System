import pytest
from pydantic import ValidationError
from src.agents.orchestrator import OrchestratorResponse
from src.agents.destination import DestinationResponse
from src.agents.logistics import LogisticsResponse
from src.agents.budget import BudgetResponse
from src.agents.review import ReviewResponse

def test_orchestrator_response_contract():
    res = OrchestratorResponse(
        destination="Dubai",
        duration_days=5,
        budget_usd=3000.0,
        areas=["Downtown"],
        preferences=[],
        avoidances=[],
        travelers=2,
        validation_warnings=["Warning 1"]
    )
    assert res.destination == "Dubai"
    
    # Missing required field
    with pytest.raises(ValidationError):
        OrchestratorResponse(duration_days=5)

def test_destination_response_contract():
    res = DestinationResponse(
        recommended_activities=[
            {
                "name": "Burj Khalifa", 
                "category": "see", 
                "area": "Downtown Dubai",
                "time_slot": "morning",
                "duration_hours": 2.0,
                "estimated_cost_usd": 40.0,
                "crowd_level": "high",
                "description": "Tallest building",
                "tips": "Book ahead"
            }
        ],
        must_do=["Burj Khalifa"],
        nice_to_have=[],
        food_recommendations=[],
        area_suggestions=[]
    )
    assert len(res.recommended_activities) == 1
    assert res.recommended_activities[0].name == "Burj Khalifa"
    
def test_logistics_response_contract():
    res = LogisticsResponse(
        accommodation={"plan": [], "estimated_cost_usd": 100.0},
        daily_sequences=[],
        transport_summary={"primary_mode": "metro", "estimated_transport_cost_usd": 50.0},
        confidence=0.9,
        warnings=[]
    )
    assert res.confidence == 0.9
    
def test_budget_response_contract():
    res = BudgetResponse(
        budget_breakdown={
            "total_budget_usd": 3000, 
            "estimated_total_usd": 2500,
            "remaining_usd": 500, 
            "within_budget": True,
            "categories": {"stay": 1000, "transport": 200, "food": 500, "activities": 800}
        },
        warnings=[],
        suggestions=["Eat cheaper"]
    )
    assert res.budget_breakdown.within_budget is True

def test_review_response_contract():
    res = ReviewResponse(
        approved=True, 
        score=1.0, 
        checks=[
            {"name": "budget", "status": "PASSED", "score": 1.0, "evidence": [], "issues": []}
        ], 
        feedback=["Good"], 
        revision_needed=False
    )
    assert res.approved is True
