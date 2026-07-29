from pydantic import BaseModel
from typing import Optional

class BudgetBreakdown(BaseModel):
    total_budget_usd: float
    estimated_total_usd: float
    remaining_usd: float
    within_budget: bool
    categories: dict[str, float]
    warnings: list[str]
    suggestions: list[str]
