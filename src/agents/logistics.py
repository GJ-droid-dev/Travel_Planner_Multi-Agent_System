import json
from typing import List, Optional
from pydantic import BaseModel, Field

from src.agents.base import BaseAgent
from src.models.agent_io import AgentTask, AgentResult, ResultStatus, AgentType
from src.tools.search import SearchTool
from src.tools.pricing import PricingTool
from src.tools.distance import DistanceTool

class AccommodationPlan(BaseModel):
    nights: int
    area: str
    hotel_suggestion: Optional[str]

class Accommodation(BaseModel):
    plan: List[AccommodationPlan]
    estimated_cost_usd: float

class DailySequence(BaseModel):
    day: int
    base_area: str
    sequence: List[str]
    transport: str

class TransportSummary(BaseModel):
    primary_mode: str
    estimated_transport_cost_usd: float

class LogisticsResponse(BaseModel):
    """Pydantic model matching the logistics.md JSON schema exactly."""
    accommodation: Accommodation
    daily_sequences: List[DailySequence]
    transport_summary: TransportSummary
    warnings: List[str] = []
    assumptions: List[str] = []
    confidence: float

class LogisticsAgent(BaseAgent):
    def __init__(self, llm_client):
        super().__init__(llm_client, "Logistics")
        
    def _build_tools(self):
        self.search_tool = SearchTool()
        self.pricing_tool = PricingTool()
        self.distance_tool = DistanceTool()
        
    async def _do_execute(self, task: AgentTask) -> AgentResult:
        req = task.request
        
        # Guess price tier based on budget for hotels
        price_tier = "mid_range"
        if req.budget_usd > 5000: price_tier = "splurge"
        elif req.budget_usd > 0 and req.budget_usd < 1500: price_tier = "budget"
            
        # Get grounded hotel data
        hotels = self.pricing_tool.search_hotels(
            area=req.areas[0] if req.areas else None, 
            price_tier=price_tier, 
            limit=10
        )
        
        # Build context
        context_dict = {
            "available_hotels": hotels.get("records", []),
            "travel_matrix_notes": "Deira to Marina is ~50 mins. Downtown to Marina is ~25 mins. Downtown to Deira is ~25 mins."
        }
        
        # If Orchestrator passed the Destination Agent's result in the context, inject it so Logistics can sequence it
        dest_payload = task.context.get("destination_result", {}).get("payload")
        if dest_payload:
            context_dict["activities_to_sequence"] = dest_payload
            
        context = json.dumps(context_dict, indent=2)
        
        user_prompt = f"User Request Details:\nDuration: {req.duration_days} days\nAreas: {req.areas}\n\nBuild a logistics and accommodation plan using the following grounded data:\n{context}"
        
        parsed_data = await self.llm_client.call(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            response_model=LogisticsResponse
        )
        
        return AgentResult(
            task_id=task.task_id,
            agent_type=AgentType.LOGISTICS,
            status=ResultStatus.SUCCESS,
            payload=parsed_data.model_dump(),
            confidence=parsed_data.confidence,
            reasoning="Sequenced days and selected accommodation based on constraints.",
            errors=[],
            duration_ms=0
        )
