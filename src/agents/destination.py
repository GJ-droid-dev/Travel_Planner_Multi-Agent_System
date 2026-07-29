import json
from typing import List, Optional
from pydantic import BaseModel

from src.agents.base import BaseAgent
from src.models.agent_io import AgentTask, AgentResult, ResultStatus, AgentType
from src.tools.search import SearchTool

class ActivityModel(BaseModel):
    name: str
    area: str
    category: str
    time_slot: str
    duration_hours: int
    estimated_cost_usd: float
    crowd_level: str
    description: str
    tips: str

class DestinationResponse(BaseModel):
    """Pydantic model that matches the destination.md JSON schema exactly."""
    recommended_activities: List[ActivityModel]
    must_do: List[str]
    nice_to_have: List[str]
    food_recommendations: List[ActivityModel]
    area_suggestions: List[str]

class DestinationAgent(BaseAgent):
    def __init__(self, llm_client):
        super().__init__(llm_client, "Destination")
        
    def _build_tools(self):
        self.search_tool = SearchTool()
        
    async def _do_execute(self, task: AgentTask) -> AgentResult:
        req = task.request
        
        # Use SearchTool to gather contextual grounding data based on the request
        attractions = self.search_tool.find_attractions(preferences=req.preferences, areas=req.areas, limit=15)
        restaurants = self.search_tool.find_restaurants(area=req.areas[0] if req.areas else None, limit=10)
        districts = self.search_tool.find_districts()
        
        # Format the context for the LLM
        context = json.dumps({
            "available_attractions": attractions.get("records", []),
            "available_restaurants": restaurants.get("records", []),
            "districts_info": districts.get("records", [])
        }, indent=2)
        
        user_prompt = f"User Request Details:\nDuration: {req.duration_days} days\nBudget: ${req.budget_usd}\nAreas: {req.areas}\nPreferences: {req.preferences}\nAvoidances: {req.avoidances}\n\nHere is the verified local knowledge you MUST use to build your recommendations:\n{context}"
        
        parsed_data = await self.llm_client.call(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            response_model=DestinationResponse
        )
        
        return AgentResult(
            task_id=task.task_id,
            agent_type=AgentType.DESTINATION,
            status=ResultStatus.SUCCESS,
            payload=parsed_data.model_dump(),
            confidence=0.9,
            reasoning="Generated grounded recommendations using local knowledge.",
            errors=[],
            duration_ms=0
        )
