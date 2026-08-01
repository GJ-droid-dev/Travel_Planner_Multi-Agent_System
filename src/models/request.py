from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class DateRange(BaseModel):
    start_date: date
    end_date: date

class TravelRequest(BaseModel):
    """Parsed representation of the user's request."""
    raw_query: str
    destination: str = "Dubai"
    duration_days: int = Field(..., gt=0, le=30)
    budget_usd: float = Field(..., gt=0)
    include_accommodation: bool = True
    areas: list[str]
    preferences: list[str]
    avoidances: list[str]
    travelers: int = Field(default=1, ge=1)
    travel_dates: Optional[str] = None
    extra_notes: Optional[str] = None
