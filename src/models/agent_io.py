from __future__ import annotations
from pydantic import BaseModel
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from enum import Enum
from src.models.request import TravelRequest

if TYPE_CHECKING:
    from src.models.itinerary import Itinerary

class AgentType(str, Enum):
    ORCHESTRATOR = "ORCHESTRATOR"
    DESTINATION = "DESTINATION"
    LOGISTICS = "LOGISTICS"
    BUDGET = "BUDGET"
    REVIEW = "REVIEW"

class ResultStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"

class AgentTask(BaseModel):
    task_id: str
    agent_type: AgentType
    request: TravelRequest
    context: dict = {}
    created_at: datetime

class AgentResult(BaseModel):
    task_id: str
    agent_type: AgentType
    status: ResultStatus
    payload: dict
    confidence: float
    reasoning: str
    errors: list[str] = []
    duration_ms: int

    @classmethod
    def failed(cls, task: AgentTask, error_msg: str) -> 'AgentResult':
        return cls(
            task_id=task.task_id,
            agent_type=task.agent_type,
            status=ResultStatus.FAILED,
            payload={},
            confidence=0.0,
            reasoning="Execution failed.",
            errors=[error_msg],
            duration_ms=0
        )

    @classmethod
    def partial_timeout(cls, task: AgentTask) -> 'AgentResult':
        return cls(
            task_id=task.task_id,
            agent_type=task.agent_type,
            status=ResultStatus.PARTIAL,
            payload={},
            confidence=0.0,
            reasoning="Execution timed out.",
            errors=["Timeout exceeded."],
            duration_ms=0
        )

class CheckResult(BaseModel):
    name: str
    status: str
    score: float
    evidence: list[str]
    issues: list[str]

class ReviewResult(BaseModel):
    approved: bool
    score: float
    checks: list[CheckResult]
    feedback: list[str]
    critical_issues: list[str] = []
    revision_needed: bool
    confidence: float = 0.0
