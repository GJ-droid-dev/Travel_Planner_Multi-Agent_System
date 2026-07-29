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

class CheckResult(BaseModel):
    passed: bool
    details: Optional[str] = None

class ReviewResult(BaseModel):
    approved: bool
    score: float
    checks: dict[str, CheckResult]
    feedback: list[str]
    revision_needed: bool

class PlanningState(BaseModel):
    request: TravelRequest
    destination_result: Optional[AgentResult] = None
    logistics_result: Optional[AgentResult] = None
    budget_result: Optional[AgentResult] = None
    review_result: Optional[ReviewResult] = None
    draft_itinerary: Optional[Itinerary] = None
    revision_count: int = 0
    status: str = "IN_PROGRESS"
