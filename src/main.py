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
from uuid import uuid4

from src.config import settings
from src.utils.logger import setup_logging, get_logger
from src.utils.store import InMemoryPlanStore
from src.models.api import PlanRequest, PlanResponse
# Import the compiled graph
from src.graph import app as graph_app

logger = get_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize logging
    setup_logging()
    
    # Initialize store and graph
    app.state.store = InMemoryPlanStore()
    app.state.graph = graph_app
    
    logger.info("app_startup", version="0.1.0", env=settings.app_env)
    yield
    logger.info("app_shutdown")

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
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Request-ID"],
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
        if not request.query.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "VALIDATION_ERROR", "message": "Query cannot be empty."}
            )
        if len(request.query) > 1000:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "QUERY_TOO_LONG", "message": "Query exceeds 1000 characters."}
            )
            
        request_id = uuid4().hex[:8]
        plan_id = app_request.app.state.store.new_id()
        
        log = logger.bind(request_id=request_id, plan_id=plan_id)
        log.info("request_started", path="/api/v1/plan")
        log.info("graph_started")
        
        try:
            async with timeout(settings.request_timeout_seconds):
                final_state = await app_request.app.state.graph.ainvoke({"raw_query": request.query})
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
        
        app_request.app.state.store.save(response)
        log.info("request_completed", status_code=200)
        
        return response

    @app.get("/api/v1/plan/{plan_id}", response_model=PlanResponse)
    async def get_plan(plan_id: str, app_request: Request) -> PlanResponse:
        plan = app_request.app.state.store.get(plan_id)
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
