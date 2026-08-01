import pytest
from pydantic import ValidationError
from datetime import date
from src.models.request import TravelRequest

def test_travel_request_valid():
    req = TravelRequest(
        raw_query="query",
        destination="Dubai",
        duration_days=3,
        budget_usd=1000,
        travelers=2,
        areas=[],
        preferences=[],
        avoidances=[]
    )
    assert req.destination == "Dubai"
    assert req.budget_usd == 1000

def test_travel_request_invalid_duration_zero():
    with pytest.raises(ValidationError):
        TravelRequest(
            raw_query="query",
            destination="Dubai",
            duration_days=0,  # Invalid
            budget_usd=1000,
            travelers=2,
            areas=[],
            preferences=[],
            avoidances=[]
        )

def test_travel_request_invalid_duration_too_high():
    with pytest.raises(ValidationError):
        TravelRequest(
            raw_query="query",
            destination="Dubai",
            duration_days=31,  # Invalid
            budget_usd=1000,
            travelers=2,
            areas=[],
            preferences=[],
            avoidances=[]
        )

def test_travel_request_invalid_budget():
    with pytest.raises(ValidationError):
        TravelRequest(
            raw_query="query",
            destination="Dubai",
            duration_days=3,
            budget_usd=-50,  # Invalid
            travelers=2,
            areas=[],
            preferences=[],
            avoidances=[]
        )

def test_travel_request_invalid_travelers():
    with pytest.raises(ValidationError):
        TravelRequest(
            raw_query="query",
            destination="Dubai",
            duration_days=3,
            budget_usd=1000,
            travelers=0,  # Invalid
            areas=[],
            preferences=[],
            avoidances=[]
        )
