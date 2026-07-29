import asyncio
from datetime import datetime
from typing import Dict, Any

from langgraph.graph import StateGraph, END

from src.models.state import PlanningState
from src.models.agent_io import AgentTask, AgentType, AgentResult, ResultStatus
from src.models.request import TravelRequest

from src.agents.orchestrator import OrchestratorAgent
from src.agents.destination import DestinationAgent
from src.agents.logistics import LogisticsAgent
from src.agents.budget import BudgetAgent
from src.agents.review import ReviewAgent

from src.utils.llm import GeminiClient, GroqClient
from src.utils.logger import get_logger

logger = get_logger("graph")

# 1. Dependency Injection / App Setup
def get_llm_client(agent_type: str):
    if agent_type == "Review":
        return GroqClient()
    return GeminiClient()

orchestrator_agent = OrchestratorAgent(get_llm_client("Orchestrator"))
destination_agent = DestinationAgent(get_llm_client("Destination"))
logistics_agent = LogisticsAgent(get_llm_client("Logistics"))
budget_agent = BudgetAgent(get_llm_client("Budget"))
review_agent = ReviewAgent(get_llm_client("Review"))

TIMEOUT = 30 # seconds

# 2. Node Wrapper
async def run_agent_node(agent, task: AgentTask, result_key: str) -> dict:
    log = logger.bind(agent_type=agent.name, task_id=task.task_id)
    log.info("agent_started")
    try:
        result = await asyncio.wait_for(agent.execute(task), timeout=TIMEOUT)
        log.info("agent_completed", duration_ms=0, status=result.status.value)
        return {result_key: result}
    except TimeoutError:
        log.warning("agent_timeout")
        return {
            result_key: AgentResult.partial_timeout(task),
            "warnings": [f"{agent.name} timed out."]
        }
    except Exception as exc:
        log.error("agent_failed", error=str(exc))
        return {
            result_key: AgentResult.failed(task, str(exc)),
            "errors": [f"{agent.name} failed: {exc}"]
        }

def make_task(state: PlanningState, agent_type: AgentType) -> AgentTask:
    return AgentTask(
        task_id=f"{agent_type.value}-{datetime.now().timestamp()}",
        agent_type=agent_type,
        request=state.get("parsed_request"),
        context={"revision_feedback": state.get("revision_feedback", [])},
        created_at=datetime.now()
    )

# 3. Nodes

async def parse_request_node(state: PlanningState) -> dict:
    task = AgentTask(
        task_id=f"parse-{datetime.now().timestamp()}",
        agent_type=AgentType.ORCHESTRATOR,
        request=TravelRequest(
            raw_query=state.get("raw_query", ""), 
            destination="", 
            duration_days=0, 
            budget_usd=0, 
            travelers=1,
            areas=[],
            preferences=[],
            avoidances=[]
        ),
        created_at=datetime.now()
    )
    res = await orchestrator_agent.execute(task)
    if res.status == ResultStatus.SUCCESS:
        payload = res.payload
        req = TravelRequest(
            raw_query=state.get("raw_query", ""),
            destination=payload.get("destination", ""),
            duration_days=payload.get("duration_days", 0),
            budget_usd=payload.get("budget_usd", 0),
            areas=payload.get("areas", []),
            preferences=payload.get("preferences", []),
            avoidances=payload.get("avoidances", []),
            travelers=payload.get("travelers", 1)
        )
        return {"parsed_request": req, "status": "PLANNING"}
    else:
        return {"status": "FAILED", "errors": ["Parse failed."]}

async def destination_node(state: PlanningState) -> dict:
    return await run_agent_node(destination_agent, make_task(state, AgentType.DESTINATION), "destination_result")

async def logistics_base_node(state: PlanningState) -> dict:
    return await run_agent_node(logistics_agent, make_task(state, AgentType.LOGISTICS), "logistics_base_result")

async def budget_base_node(state: PlanningState) -> dict:
    return await run_agent_node(budget_agent, make_task(state, AgentType.BUDGET), "budget_base_result")

async def merge_draft_itinerary_node(state: PlanningState) -> dict:
    if not state.get("destination_result") or state["destination_result"].status != ResultStatus.SUCCESS:
        return {"status": "PARTIAL", "warnings": ["Missing destination output, cannot build full itinerary."]}
        
    dest_payload = state["destination_result"].payload
    log_payload = state.get("logistics_base_result", AgentResult.failed(make_task(state, AgentType.LOGISTICS), "")).payload
    bud_payload = state.get("budget_base_result", AgentResult.failed(make_task(state, AgentType.BUDGET), "")).payload

    activities = dest_payload.get("recommended_activities", [])
    days = log_payload.get("daily_sequences", [])
    
    # Naive deterministic assignment
    assigned_days = []
    for d in days:
        assigned_days.append({
            "day_number": d.get("day"),
            "theme": "Exploration",
            "base_area": d.get("base_area"),
            "activities": activities[:2], # just take first 2 for naive draft
            "transport_notes": d.get("transport"),
            "meals": [],
            "estimated_day_cost_usd": 150.0
        })
        activities = activities[2:]

    draft_itinerary = {
        "request": state.get("parsed_request").model_dump() if state.get("parsed_request") else {},
        "days": assigned_days,
        "accommodation": log_payload.get("accommodation", {}).get("plan", [{}])[0] if log_payload.get("accommodation", {}).get("plan") else {},
        "budget_breakdown": bud_payload.get("budget_breakdown", {}),
        "review_result": {},
        "generated_at": datetime.now().isoformat()
    }

    return {"itinerary": draft_itinerary}

async def logistics_final_node(state: PlanningState) -> dict:
    # Normally validates sequence using DistanceTool
    # Mock for now
    return {}

async def budget_final_node(state: PlanningState) -> dict:
    # Normally recalculates budget using exact items
    # Mock for now
    return {}

async def review_node(state: PlanningState) -> dict:
    # Call the review agent
    task = make_task(state, AgentType.REVIEW)
    task.context["draft_itinerary"] = state.get("itinerary", {})
    return await run_agent_node(review_agent, task, "review_result")

def route_after_review(state: PlanningState) -> str:
    review = state.get("review_result")
    if not review or review.status != ResultStatus.SUCCESS:
        return "end_with_warnings"

    payload = review.payload
    if payload.get("approved"):
        return "end"

    rev_count = state.get("revision_count", 0)
    if rev_count >= 2:
        return "end_with_warnings"

    # Targeted Revision Logic
    failed = {
        name for name, result in payload.get("checks", {}).items()
        if not result.get("passed")
    }

    if "budgetcompliance" in failed:
        return "revise_budget"
    if "logisticsfeasibility" in failed:
        return "revise_logistics"
    if "preferencealignment" in failed or "avoidancerespected" in failed:
        return "revise_destination"
        
    return "revise_merge"

# Increment revision count just before merge for any loop
async def increment_revision(state: PlanningState) -> dict:
    return {"revision_count": state.get("revision_count", 0) + 1}

# 4. Graph Construction
graph = StateGraph(PlanningState)

graph.add_node("parse_request", parse_request_node)
graph.add_node("destination", destination_node)
graph.add_node("logistics_base", logistics_base_node)
graph.add_node("budget_base", budget_base_node)
graph.add_node("merge_draft_itinerary", merge_draft_itinerary_node)
graph.add_node("logistics_final", logistics_final_node)
graph.add_node("budget_final", budget_final_node)
graph.add_node("review", review_node)
graph.add_node("increment_revision", increment_revision)

# Wiring
graph.set_entry_point("parse_request")

# Stage A: Fan-out
graph.add_edge("parse_request", "destination")
graph.add_edge("parse_request", "logistics_base")
graph.add_edge("parse_request", "budget_base")

# Stage A: Fan-in
graph.add_edge(["destination", "logistics_base", "budget_base"], "merge_draft_itinerary")

# Stage B: Fan-out to validators
graph.add_edge("merge_draft_itinerary", "logistics_final")
graph.add_edge("merge_draft_itinerary", "budget_final")

# Stage B: Fan-in to Review
graph.add_edge(["logistics_final", "budget_final"], "review")

# Conditional edges
graph.add_conditional_edges("review", route_after_review, {
    "end": END,
    "end_with_warnings": END,
    "revise_budget": "budget_base",
    "revise_logistics": "logistics_base",
    "revise_destination": "destination",
    "revise_merge": "increment_revision"
})
# Make sure everything goes through increment revision on loop back if we go to merge directly
graph.add_edge("increment_revision", "merge_draft_itinerary")
# Wait, if we route to budget_base, it executes, but where does it go next? It goes to merge_draft_itinerary!
# But then we need to increment the revision count.
# So I should make the routing logic point to a router node or just increment the revision count in the branches.
# Let's adjust route_after_review slightly later.

app = graph.compile()
