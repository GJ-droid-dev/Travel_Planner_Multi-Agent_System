import json
from typing import List, Optional
from pydantic import BaseModel, Field

from src.agents.base import BaseAgent
from src.models.agent_io import AgentTask, AgentResult, ResultStatus, AgentType
from src.tools.pricing import PricingTool
from src.tools.currency import CurrencyTool

class CategoryBreakdown(BaseModel):
    stay: float
    transport: float
    food: float
    activities: float

class Alternative(BaseModel):
    original: str
    alternative: str

class BudgetBreakdown(BaseModel):
    total_budget_usd: float
    estimated_total_usd: float
    remaining_usd: float
    within_budget: bool
    categories: CategoryBreakdown

class BudgetResponse(BaseModel):
    """Pydantic model matching the budget.md JSON schema exactly."""
    budget_breakdown: BudgetBreakdown
    warnings: List[str] = []
    suggestions: List[str] = []
    cheaper_alternatives: List[Alternative] = []

class BudgetAgent(BaseAgent):
    def __init__(self, llm_client):
        super().__init__(llm_client, "Budget")
        
    def _build_tools(self):
        self.pricing_tool = PricingTool()
        self.currency_tool = CurrencyTool()
        
    async def _do_execute(self, task: AgentTask) -> AgentResult:
        req = task.request
        
        # Use tools to build grounded baseline costs
        price_tier = "mid_range"
        if req.budget_usd > 5000: price_tier = "splurge"
        elif req.budget_usd > 0 and req.budget_usd < 1500: price_tier = "budget"
            
        food_estimate = self.pricing_tool.estimate_food_budget(req.duration_days, req.travelers, price_tier)
        food_estimate_aed = food_estimate.get("total_estimated_aed", 0)
        food_estimate_usd = self.currency_tool.aed_to_usd(food_estimate_aed)
        
        hotels = self.pricing_tool.search_hotels(area=req.areas[0] if req.areas else None, price_tier=price_tier, limit=3)
        
        context_dict = {
            "baseline_food_usd": float(round(food_estimate_usd, 2)),
            "sample_hotel_prices_aed": [h.get("price") for h in hotels.get("records", [])],
            "conversion_rate_aed_to_usd": float(self.currency_tool.rate)
        }
        
        # If Orchestrator passed the Logistics Agent's result, inject it
        logistics_payload = task.context.get("logistics_result", {}).get("payload")
        if logistics_payload:
            context_dict["logistics_plan"] = logistics_payload
            
        context = json.dumps(context_dict, indent=2)
        
        user_prompt = f"User Request Details:\nDuration: {req.duration_days} days\nBudget: ${req.budget_usd}\nTravelers: {req.travelers}\n\nBuild a budget breakdown using the following grounded data:\n{context}"
        
        parsed_data = await self.llm_client.call(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            response_model=BudgetResponse
        )
        
        return AgentResult(
            task_id=task.task_id,
            agent_type=AgentType.BUDGET,
            status=ResultStatus.SUCCESS,
            payload=parsed_data.model_dump(),
            confidence=0.9,
            reasoning="Calculated budget using Pricing and Currency tools.",
            errors=[],
            duration_ms=0
        )
