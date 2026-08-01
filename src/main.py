from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from asyncio import TimeoutError as AsyncioTimeoutError, timeout
from datetime import datetime
from pydantic import ValidationError
from tenacity import RetryError
from src.utils.llm import TransientLLMError
from uuid import uuid4, UUID

from src.config import settings
from src.utils.logger import setup_logging, get_logger
from src.utils.db import engine, AsyncSessionLocal
from src.utils.store import PostgresPlanStore
from src.models.api import PlanRequest, PlanResponse
# Import the compiled graph
from src.graph import app as graph_app

logger = get_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize logging
    setup_logging()
    
    # Initialize store and graph
    app.state.store = PostgresPlanStore(AsyncSessionLocal)
    app.state.graph = graph_app
    
    logger.info("app_startup", version="0.1.0", env=settings.app_env)
    yield
    logger.info("app_shutdown")
    await engine.dispose()

def create_app() -> FastAPI:
    app = FastAPI(
        title="Dubai AI Travel Planner",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Error Handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request parameters.",
                    "details": exc.errors()
                }
            }
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail if isinstance(exc.detail, dict) else {
                    "code": "HTTP_ERROR",
                    "message": exc.detail,
                    "details": []
                }
            }
        )

    @app.exception_handler(TransientLLMError)
    async def transient_llm_exception_handler(request: Request, exc: TransientLLMError):
        logger.error("llm_service_unavailable", error=str(exc))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "The backend AI service is temporarily unavailable. Please try again later.",
                    "details": []
                }
            }
        )

    @app.exception_handler(RetryError)
    async def retry_exception_handler(request: Request, exc: RetryError):
        # Unwrap the RetryError to see if it's a TransientLLMError
        original_exc = exc.last_attempt.exception() if exc.last_attempt else None
        if isinstance(original_exc, TransientLLMError):
            return await transient_llm_exception_handler(request, original_exc)
        
        logger.error("internal_error", error=str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred.",
                    "details": []
                }
            }
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("internal_error", error=str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred.",
                    "details": []
                }
            }
        )
        
    @app.get("/api/v1/health")
    async def health():
        return {
            "status": "healthy",
            "service": "dubai-ai-travel-planner",
            "version": "0.1.0"
        }

    @app.post("/api/v1/plan", response_model=PlanResponse)
    async def create_plan(request: PlanRequest, app_request: Request) -> PlanResponse:
        base_budget = request.budget_amount
        if request.budget_scope == "Per traveler":
            base_budget = base_budget * request.travelers
            
        if request.budget_currency == "AED":
            budget_usd = base_budget / settings.exchange_rate_usd_aed
        else:
            budget_usd = base_budget

        from src.models.request import TravelRequest
        travel_request = TravelRequest(
            raw_query="", # Deprecated
            destination=request.destination,
            duration_days=request.duration_days,
            budget_usd=budget_usd,
            include_accommodation=request.include_accommodation,
            areas=[],
            preferences=request.interests,
            avoidances=request.avoidances,
            travelers=request.travelers,
            travel_dates=request.travel_dates,
            extra_notes=request.extra_notes
        )
            
        request_id = uuid4().hex[:8]
        plan_id = uuid4()
        
        log = logger.bind(request_id=request_id, plan_id=str(plan_id))
        log.info("request_started", path="/api/v1/plan")
        log.info("graph_started")
        
        try:
            async with timeout(settings.request_timeout_seconds):
                final_state = await app_request.app.state.graph.ainvoke({"parsed_request": travel_request})
        except AsyncioTimeoutError:
            log.error("planning_timeout")
            return JSONResponse(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                content={
                    "error": {
                        "code": "PLANNING_TIMEOUT",
                        "message": "Trip planning exceeded the request time limit.",
                        "details": []
                    }
                }
            )
        except TransientLLMError as e:
            log.error("llm_service_unavailable", error=str(e))
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "error": {
                        "code": "SERVICE_UNAVAILABLE",
                        "message": "The underlying LLM service is temporarily unavailable.",
                        "details": [str(e)]
                    }
                }
            )
            
        # Build PlanResponse based on the final_state
        graph_status = final_state.get("status", "FAILED")
        
        if graph_status == "COMPLETE":
            response_status = "completed"
        elif graph_status in ("PARTIAL", "REVIEWING", "VALIDATING"):
            response_status = "partial"
        else:
            response_status = "failed"
            
        try:
            response = PlanResponse(
                plan_id=plan_id,
                status=response_status,
                itinerary=final_state.get("itinerary"),
                errors=final_state.get("errors", []),
                warnings=final_state.get("warnings", []),
                generated_at=datetime.now()
            )
        except ValidationError as e:
            log.warning("itinerary_validation_failed", error=str(e))
            errors = final_state.get("errors", [])
            errors.append("Draft itinerary failed schema validation.")
            response = PlanResponse(
                plan_id=plan_id,
                status="failed",
                itinerary=None,
                errors=errors,
                warnings=final_state.get("warnings", []),
                generated_at=datetime.now()
            )
        
        await app_request.app.state.store.save(response)
        log.info("request_completed", status_code=200)
        
        return response

    @app.post("/api/v1/plan/stream")
    async def stream_plan(request: PlanRequest, app_request: Request):
        import json
        from fastapi.responses import StreamingResponse
        from src.models.request import TravelRequest
        
        base_budget = request.budget_amount
        if request.budget_scope == "Per traveler":
            base_budget = base_budget * request.travelers
            
        if request.budget_currency == "AED":
            budget_usd = base_budget / settings.exchange_rate_usd_aed
        else:
            budget_usd = base_budget

        travel_request = TravelRequest(
            raw_query="", 
            destination=request.destination,
            duration_days=request.duration_days,
            budget_usd=budget_usd,
            include_accommodation=request.include_accommodation,
            areas=[],
            preferences=request.interests,
            avoidances=request.avoidances,
            travelers=request.travelers,
            travel_dates=request.travel_dates,
            extra_notes=request.extra_notes
        )
            
        request_id = uuid4().hex[:8]
        plan_id = uuid4()
        
        log = logger.bind(request_id=request_id, plan_id=str(plan_id))
        log.info("stream_request_started", path="/api/v1/plan/stream")
        
        async def event_generator():
            final_state = {}
            try:
                async for chunk in app_request.app.state.graph.astream({"parsed_request": travel_request}, stream_mode="updates"):
                    node_name = list(chunk.keys())[0] if chunk else ""
                    yield f"data: {json.dumps({'node': node_name})}\n\n"
                    
                    if chunk and isinstance(chunk, dict):
                        for v in chunk.values():
                            if isinstance(v, dict):
                                for key, val in v.items():
                                    if key in ("errors", "warnings", "revision_feedback"):
                                        final_state.setdefault(key, []).extend(val)
                                    else:
                                        final_state[key] = val
            except Exception as e:
                log.error("stream_error", error=str(e))
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                return
                
            graph_status = final_state.get("status", "FAILED")
            if graph_status == "COMPLETE":
                response_status = "completed"
            elif graph_status in ("PARTIAL", "REVIEWING", "VALIDATING"):
                response_status = "partial"
            else:
                response_status = "failed"
                
            try:
                response = PlanResponse(
                    plan_id=plan_id,
                    status=response_status,
                    itinerary=final_state.get("itinerary"),
                    errors=final_state.get("errors", []),
                    warnings=final_state.get("warnings", []),
                    generated_at=datetime.now()
                )
            except ValidationError as e:
                errors = final_state.get("errors", [])
                errors.append("Draft itinerary failed schema validation.")
                response = PlanResponse(
                    plan_id=plan_id,
                    status="failed",
                    itinerary=None,
                    errors=errors,
                    warnings=final_state.get("warnings", []),
                    generated_at=datetime.now()
                )
                
            await app_request.app.state.store.save(response)
            yield f"data: {json.dumps({'done': True, 'plan_id': str(plan_id)})}\n\n"
            
        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @app.get("/api/v1/plan/{plan_id}", response_model=PlanResponse)
    async def get_plan(plan_id: UUID, app_request: Request) -> PlanResponse:
        plan = await app_request.app.state.store.get(plan_id)
        if not plan:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": {
                        "code": "PLAN_NOT_FOUND",
                        "message": f"Plan {plan_id} not found.",
                        "details": []
                    }
                }
            )
        return plan

    return app

app = create_app()
