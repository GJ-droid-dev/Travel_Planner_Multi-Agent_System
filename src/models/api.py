from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from src.models.itinerary import Itinerary
from src.models.agent_io import ReviewResult

class PlanRequest(BaseModel):
    query: str

class PlanResponse(BaseModel):
    plan_id: str
    status: Literal["completed", "partial", "failed"]
    itinerary: Optional[Itinerary] = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    generated_at: datetime

PlanResponse.model_rebuild()
