import json
from pydantic import BaseModel, Field

from src.agents.base import BaseAgent
from src.models.agent_io import AgentTask, AgentResult, ResultStatus, AgentType

class OrchestratorResponse(BaseModel):
    """Pydantic model that matches the orchestrator.md JSON schema exactly."""
    destination: str
    duration_days: int
    budget_usd: int = Field(default=0)
    areas: list[str] = []
    preferences: list[str] = []
    avoidances: list[str] = []
    travelers: int = 1

class OrchestratorAgent(BaseAgent):
    def __init__(self, llm_client):
        super().__init__(llm_client, "Orchestrator")
        
    async def _do_execute(self, task: AgentTask) -> AgentResult:
        # In Phase 2, the Orchestrator just parses the raw query into constraints.
        # LangGraph (Phase 3) will handle the actual fan-out and merging.
        
        user_prompt = f"Parse the following travel request:\n\n{task.request.raw_query}"
        
        parsed_data = await self.llm_client.call(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            response_model=OrchestratorResponse
        )
        
        return AgentResult(
            task_id=task.task_id,
            agent_type=AgentType.ORCHESTRATOR,
            status=ResultStatus.SUCCESS,
            payload=parsed_data.model_dump(),
            confidence=1.0,
            reasoning="Extracted constraints successfully.",
            errors=[],
            duration_ms=0
        )
