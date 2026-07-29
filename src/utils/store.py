from typing import Optional
from uuid import uuid4
from src.models.api import PlanResponse

class InMemoryPlanStore:
    def __init__(self):
        self._store: dict[str, PlanResponse] = {}

    def new_id(self) -> str:
        return uuid4().hex[:8]

    def save(self, plan: PlanResponse) -> None:
        self._store[plan.plan_id] = plan

    def get(self, plan_id: str) -> Optional[PlanResponse]:
        return self._store.get(plan_id)
