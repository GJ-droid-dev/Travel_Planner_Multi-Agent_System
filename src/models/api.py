from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from src.models.itinerary import Itinerary
from src.models.agent_io import ReviewResult

class PlanRequest(BaseModel):
    destination: Literal["Dubai, UAE"] = "Dubai, UAE"
    duration_days: int = Field(..., ge=1, le=14)
    travelers: int = Field(..., ge=1, le=20)
    budget_amount: float = Field(..., gt=0)
    budget_currency: Literal["USD", "AED"]
    budget_scope: Literal["Total trip", "Per traveler"]
    include_accommodation: bool
    interests: list[str] = Field(default_factory=list, max_length=5)
    avoidances: list[str] = Field(default_factory=list, max_length=10)
    travel_dates: Optional[str] = None
    extra_notes: Optional[str] = Field(None, max_length=1000)

class PlanResponse(BaseModel):
    plan_id: UUID
    status: Literal["completed", "partial", "failed"]
    itinerary: Optional[Itinerary] = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    generated_at: datetime

PlanResponse.model_rebuild()
