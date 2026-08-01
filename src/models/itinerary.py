from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, TYPE_CHECKING
from datetime import date, datetime
from src.models.request import TravelRequest
from src.models.budget import BudgetBreakdown
from src.models.agent_io import ReviewResult

class Activity(BaseModel):
    name: str
    area: str
    category: str
    time_slot: str
    duration_hours: float
    estimated_cost_usd: float
    crowd_level: str
    description: str
    tips: Optional[str] = None

class DayPlan(BaseModel):
    day_number: int
    date: Optional[date] = None
    theme: str
    base_area: str
    activities: list[Activity]
    transport_notes: str
    meals: list[Activity]
    estimated_day_cost_usd: float

class AccommodationPlan(BaseModel):
    hotel_name: str
    area: str
    star_rating: int
    total_cost_usd: float
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None

class Itinerary(BaseModel):
    request: TravelRequest
    days: list[DayPlan]
    accommodation: AccommodationPlan
    budget_breakdown: BudgetBreakdown
    review_result: ReviewResult
    extra_activities: list[Activity] = []
    generated_at: datetime

Itinerary.model_rebuild()
