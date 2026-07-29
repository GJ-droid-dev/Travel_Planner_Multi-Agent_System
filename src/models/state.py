from typing import Annotated, Literal, TypedDict
from operator import add
from pydantic import BaseModel

from src.models.request import TravelRequest
from src.models.agent_io import AgentResult
from src.models.itinerary import Itinerary

class PlanningState(TypedDict, total=False):
    raw_query: str
    parsed_request: TravelRequest

    destination_result: AgentResult | None
    logistics_base_result: AgentResult | None
    budget_base_result: AgentResult | None

    itinerary: Itinerary | None
    logistics_validation: AgentResult | None
    budget_validation: AgentResult | None
    review_result: AgentResult | None

    revision_feedback: list[str]
    revision_count: int
    status: Literal[
        "PARSING",
        "PLANNING",
        "MERGING",
        "VALIDATING",
        "REVIEWING",
        "REVISING",
        "COMPLETE",
        "PARTIAL",
        "FAILED",
    ]

    errors: Annotated[list[str], add]
    warnings: Annotated[list[str], add]
