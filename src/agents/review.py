import json
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

from src.agents.base import BaseAgent
from src.models.agent_io import AgentTask, AgentResult, ResultStatus, AgentType
from src.tools.distance import DistanceTool
from src.tools.pricing import PricingTool

class CheckResultModel(BaseModel):
    passed: bool
    details: str

class ReviewResponse(BaseModel):
    """Pydantic model matching the review.md JSON schema exactly."""
    approved: bool
    score: float
    checks: Dict[str, CheckResultModel]
    feedback: List[str]
    revision_needed: bool

class ReviewAgent(BaseAgent):
    def __init__(self, llm_client):
        super().__init__(llm_client, "Review")
        
    def _build_tools(self):
        # Tools are read-only for the Review agent to independently validate claims
        self.distance_tool = DistanceTool()
        self.pricing_tool = PricingTool()
        
    async def _do_execute(self, task: AgentTask) -> AgentResult:
        req = task.request
        draft_itinerary = task.context.get("draft_itinerary", {})
        
        # Build context for review
        context_dict = {
            "original_request": req.model_dump() if hasattr(req, "model_dump") else req,
            "draft_itinerary": draft_itinerary
        }
        
        # We could potentially inject some random sampling from pricing/distance tools 
        # here if we wanted to enforce tool use before calling the LLM, but for now 
        # Groq LLaMA 3.3 will perform logical consistency checks on the payload.
        
        user_prompt = f"Perform a strict QA review of the following draft itinerary against the original request constraints:\n\n{json.dumps(context_dict, indent=2)}"
        
        parsed_data = await self.llm_client.call(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            response_model=ReviewResponse
        )
        
        return AgentResult(
            task_id=task.task_id,
            agent_type=AgentType.REVIEW,
            status=ResultStatus.SUCCESS,
            payload=parsed_data.model_dump(),
            confidence=1.0,
            reasoning="Performed comprehensive QA review.",
            errors=[],
            duration_ms=0
        )
