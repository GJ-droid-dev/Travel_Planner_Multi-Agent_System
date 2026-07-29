from pydantic import BaseModel
from typing import Optional
from datetime import date

class DateRange(BaseModel):
    start_date: date
    end_date: date

class TravelRequest(BaseModel):
    """Parsed representation of the user's natural-language request."""
    raw_query: str
    destination: str = "Dubai"
    duration_days: int
    budget_usd: float
    areas: list[str]
    preferences: list[str]
    avoidances: list[str]
    travelers: int = 1
    travel_dates: Optional[DateRange] = None
