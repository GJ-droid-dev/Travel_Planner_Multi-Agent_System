from typing import Optional, Protocol
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from src.models.api import PlanResponse
from src.models.db import PlanRecord
from src.models.itinerary import Itinerary

class PlanStore(Protocol):
    async def save(self, plan: PlanResponse) -> PlanResponse:
        ...

    async def get(self, plan_id: UUID) -> Optional[PlanResponse]:
        ...

    async def healthcheck(self) -> bool:
        ...

class InMemoryPlanStore:
    def __init__(self):
        self._store: dict[UUID, PlanResponse] = {}

    def new_id(self) -> UUID:
        return uuid4()

    async def save(self, plan: PlanResponse) -> PlanResponse:
        self._store[plan.plan_id] = plan
        return plan

    async def get(self, plan_id: UUID) -> Optional[PlanResponse]:
        return self._store.get(plan_id)
        
    async def healthcheck(self) -> bool:
        return True

class PostgresPlanStore:
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        self.session_maker = session_maker

    def new_id(self) -> UUID:
        return uuid4()

    async def save(self, plan: PlanResponse) -> PlanResponse:
        async with self.session_maker() as session:
            try:
                record = PlanRecord(
                    id=plan.plan_id,
                    status=plan.status,
                    itinerary=plan.itinerary.model_dump(mode="json") if plan.itinerary else None,
                    errors=plan.errors,
                    warnings=plan.warnings,
                    generated_at=plan.generated_at,
                )
                await session.merge(record)
                await session.commit()
            except SQLAlchemyError:
                await session.rollback()
                raise
        return plan

    async def get(self, plan_id: UUID) -> Optional[PlanResponse]:
        async with self.session_maker() as session:
            result = await session.execute(select(PlanRecord).where(PlanRecord.id == plan_id))
            record = result.scalar_one_or_none()
            
            if not record:
                return None
                
            return PlanResponse(
                plan_id=record.id,
                status=record.status,
                itinerary=Itinerary.model_validate(record.itinerary) if record.itinerary else None,
                errors=record.errors or [],
                warnings=record.warnings or [],
                generated_at=record.generated_at,
            )

    async def healthcheck(self) -> bool:
        from sqlalchemy import text
        try:
            async with self.session_maker() as session:
                await session.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
