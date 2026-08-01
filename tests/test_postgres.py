import pytest
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.config import settings
from src.models.api import PlanResponse
from src.models.itinerary import Itinerary
from src.utils.store import PostgresPlanStore
from src.models.db import Base

@pytest.fixture(scope="session")
def engine():
    url = settings.database_url
    if "test" not in url:
        pytest.skip("Test database URL must contain 'test' to prevent accidental data loss.")
    
    eng = create_async_engine(url)
    return eng

@pytest.fixture
async def setup_db(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
def store(engine, setup_db):
    session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)
    return PostgresPlanStore(session_maker)

@pytest.mark.asyncio
async def test_save_and_get_plan(store):
    plan_id = uuid.uuid4()
    plan = PlanResponse(
        plan_id=plan_id,
        status="completed",
        itinerary=None,
        errors=["error 1"],
        warnings=[],
        generated_at=datetime.now()
    )
    
    await store.save(plan)
    
    retrieved = await store.get(plan_id)
    assert retrieved is not None
    assert retrieved.plan_id == plan_id
    assert retrieved.status == "completed"
    assert retrieved.errors == ["error 1"]
    
@pytest.mark.asyncio
async def test_get_nonexistent_plan(store):
    retrieved = await store.get(uuid.uuid4())
    assert retrieved is None

@pytest.mark.asyncio
async def test_healthcheck(store):
    is_healthy = await store.healthcheck()
    assert is_healthy is True
