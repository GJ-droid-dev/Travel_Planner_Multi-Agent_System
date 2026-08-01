# Actual Architecture — AI Travel Planner (Dubai)

> This document describes the **as-built** system, based on the current codebase. It supersedes [architecture.md](architecture.md) (the original design plan) wherever the two differ. Differences from the plan are called out explicitly in [§12](#12-deviations-from-the-original-plan).

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Technology Stack](#2-technology-stack)
3. [Project Structure](#3-project-structure)
4. [Core Data Models](#4-core-data-models)
5. [Agent Architecture](#5-agent-architecture)
6. [Orchestration Graph (LangGraph)](#6-orchestration-graph-langgraph)
7. [API Layer](#7-api-layer)
8. [Persistence Layer](#8-persistence-layer)
9. [Frontend](#9-frontend)
10. [Configuration & Environment](#10-configuration--environment)
11. [Deployment](#11-deployment)
12. [Deviations from the Original Plan](#12-deviations-from-the-original-plan)
13. [Testing](#13-testing)

---

## 1. System Overview

The backend is a **FastAPI** service that wraps a **LangGraph** state machine. A single HTTP request triggers a graph run in which four LLM-backed agents (Destination, Logistics, Budget, Review) collaborate — three in parallel, one as a final QA gate — to turn a structured travel request into a full Dubai itinerary. Results are persisted to Postgres and can be re-fetched by plan ID. A separate React SPA (deployed independently) calls the API and streams progress to the user.

```
┌────────────────────────────────────────────────────────────────────┐
│  React SPA (Vite)  →  POST /api/v1/plan/stream (SSE)                │
└───────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   FastAPI (src/main.py)│
                     │  builds TravelRequest   │
                     │  invokes compiled graph │
                     └───────────┬────────────┘
                                 ▼
                     ┌───────────────────────┐
                     │  LangGraph StateGraph  │
                     │      (src/graph.py)    │
                     └───────────┬────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                         ▼
 ┌─────────────┐        ┌────────────────┐         ┌───────────────┐
 │ Destination │        │ Logistics(base) │         │ Budget (base) │
 │   Agent     │        │     Agent       │         │    Agent      │
 └──────┬──────┘        └────────┬───────┘         └───────┬───────┘
        └────────────────────────┼─────────────────────────┘
                                 ▼
                     merge_draft_itinerary (deterministic Python)
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
        logistics_final (no-op)          budget_final (no-op)
                 └───────────────┬───────────────┘
                                 ▼
                          review (Review Agent)
                                 │
                  conditional routing (approve / revise / give up)
                                 ▼
                        Final PlanResponse
                                 │
                                 ▼
                    PostgresPlanStore.save() (JSONB)
```

Both agents and the graph run **inside a single FastAPI process** — there is no separate worker/queue; everything happens synchronously (from the client's perspective, via SSE) within one request lifecycle, bounded by a 90s overall timeout.

---

## 2. Technology Stack

| Layer | Technology (actual) | Notes |
|---|---|---|
| **Language** | Python 3.12+ | Per `pyproject.toml` |
| **LLM Provider** | Google Gemini (`gemini-3.6-flash`) for **all** agents | Groq client still exists but is currently unused — see [§12](#12-deviations-from-the-original-plan) |
| **Agent/Graph Framework** | LangGraph `StateGraph` (`langgraph>=1.2.10`) | LangChain is a dependency but not directly used in agent code |
| **Web Framework** | FastAPI + Uvicorn | Single router defined inline in `create_app()` |
| **Data Validation** | Pydantic v2 | Used for request/response schemas and structured LLM output (`response_schema`) |
| **Database** | PostgreSQL via SQLAlchemy 2.0 async + `asyncpg` | Single `plans` table, JSONB itinerary storage |
| **Migrations** | Alembic | One migration: `1a88292faa71_create_plans_table.py` |
| **Retry/Resilience** | `tenacity` | Exponential-jitter retry around LLM calls; custom `TransientLLMError` |
| **Structured Logging** | `structlog` | Console renderer in dev, JSON renderer in prod |
| **HTML Scraping** | `beautifulsoup4` + `httpx` | One-time/offline Wikivoyage scraper, output cached to JSON |
| **Frontend** | React 19 + Vite 8 + React Router 7 + Tailwind CSS 4 | SPA, deployed separately (Vercel) |
| **Package Manager** | `uv` | Used in Dockerfile (`uv sync --frozen`) |
| **Containerization** | Docker (`python:3.12-slim`) | Deployed to Railway |
| **Testing** | `pytest` + `pytest-asyncio` | See [§13](#13-testing) |

---

## 3. Project Structure (actual)

```
Travel Planner/
├── main.py                        # Trivial placeholder entry point ("Hello from travel-planner!") — NOT the real app
├── alembic.ini / alembic/         # DB migrations (plans table)
├── Dockerfile                     # Backend container (uv-based)
├── railway.toml                   # Railway deploy config (Dockerfile builder)
├── query.py                       # Ad-hoc script (not part of the app)
├── test_live.py                   # Standalone live/manual test script
│
├── src/
│   ├── main.py                    # Actual FastAPI app: create_app(), routes, lifespan, error handlers
│   ├── config.py                  # pydantic-settings Settings (env-driven)
│   ├── graph.py                   # LangGraph StateGraph wiring + node functions
│   │
│   ├── models/
│   │   ├── request.py             # TravelRequest (internal, validated)
│   │   ├── api.py                 # PlanRequest / PlanResponse (public API contract)
│   │   ├── itinerary.py           # Itinerary, DayPlan, Activity, AccommodationPlan
│   │   ├── budget.py              # BudgetBreakdown
│   │   ├── agent_io.py            # AgentTask, AgentResult, ReviewResult, CheckResult, enums
│   │   ├── state.py               # PlanningState (TypedDict — LangGraph state schema)
│   │   └── db.py                  # SQLAlchemy PlanRecord ORM model
│   │
│   ├── agents/
│   │   ├── base.py                # BaseAgent: prompt loading, timing, error wrapping
│   │   ├── orchestrator.py        # Present but NOT used in the live graph (see §12)
│   │   ├── destination.py         # Grounded recommendations via SearchTool
│   │   ├── logistics.py           # Accommodation + daily sequencing via PricingTool/DistanceTool
│   │   ├── budget.py               # Budget breakdown via PricingTool/CurrencyTool
│   │   └── review.py              # LLM-based QA gate producing ReviewResult
│   │
│   ├── tools/
│   │   ├── repository.py          # DubaiRepository: singleton loader over static JSON data
│   │   ├── search.py               # Read-only attraction/restaurant/district lookups
│   │   ├── pricing.py               # Hotel/attraction/food cost lookups (grounded)
│   │   ├── currency.py             # Deterministic AED↔USD conversion (config-based rate)
│   │   ├── distance.py             # Hardcoded travel-time heuristic matrix between districts
│   │   └── scraper.py               # Offline Wikivoyage HTML scraper → JSON cache (not called at runtime)
│   │
│   ├── data/
│   │   ├── dubai_wikivoyage.json   # Scraped base dataset (see/do/buy/eat/sleep)
│   │   └── dubai_luxury.json       # Supplemental luxury-tier data, merged in at load time
│   │
│   ├── prompts/                   # System prompts (Markdown) — one per agent, loaded by BaseAgent
│   │   ├── orchestrator.md
│   │   ├── destination.md
│   │   ├── logistics.md
│   │   ├── budget.md
│   │   └── review.md
│   │
│   └── utils/
│       ├── llm.py                 # LLMClient ABC; GeminiClient + GroqClient; TransientLLMError; retry logic
│       ├── db.py                  # Async SQLAlchemy engine + sessionmaker
│       ├── store.py               # PlanStore protocol; InMemoryPlanStore + PostgresPlanStore
│       └── logger.py              # structlog configuration
│
├── frontend/                       # Independent React SPA (Vite), deployed to Vercel
│   └── src/
│       ├── api.js                  # fetch wrappers: createPlan (SSE), getPlan, getHealth
│       ├── App.jsx                 # Router: /, /status/:planId, /itinerary/:planId, /retrieve, /error
│       ├── components/Layout.jsx
│       └── pages/                  # LandingPage, StatusPage, ItineraryPage, RetrievePage, ErrorPage
│
├── scripts/
│   ├── demo.py                     # Manual demo runner
│   └── test_structured_api.py      # Manual API exercise script
│
└── tests/
    ├── test_agents.py, test_api.py, test_contracts.py, test_e2e.py,
    ├── test_llm_client.py, test_models.py, test_postgres.py,
    ├── test_scraper.py, test_smoke.py, test_tools.py
```

**Note:** Top-level `main.py` is a leftover `uv init` placeholder — it just prints a string and is not used by the running application. The real ASGI app is `src.main:app`, referenced directly in the Dockerfile's `uvicorn` command.

---

## 4. Core Data Models

### 4.1 Internal Travel Request — `src/models/request.py`

```python
class TravelRequest(BaseModel):
    raw_query: str                       # kept for compatibility, no longer used to drive parsing
    destination: str = "Dubai"
    duration_days: int                   # 1–30
    budget_usd: float                    # > 0, always normalized to USD before this point
    include_accommodation: bool = True
    areas: list[str]
    preferences: list[str]
    avoidances: list[str]
    travelers: int = 1
    travel_dates: Optional[str] = None
    extra_notes: Optional[str] = None
```

### 4.2 Public API Contract — `src/models/api.py`

```python
class PlanRequest(BaseModel):
    destination: Literal["Dubai, UAE"] = "Dubai, UAE"   # v1 hard-locked to Dubai
    duration_days: int                  # 1–14
    travelers: int                      # 1–20
    budget_amount: float
    budget_currency: Literal["USD", "AED"]
    budget_scope: Literal["Total trip", "Per traveler"]
    include_accommodation: bool
    interests: list[str]                # max 5
    avoidances: list[str]               # max 10
    travel_dates: Optional[str] = None
    extra_notes: Optional[str] = None   # max 1000 chars

class PlanResponse(BaseModel):
    plan_id: UUID
    status: Literal["completed", "partial", "failed"]
    itinerary: Optional[Itinerary] = None
    errors: list[str]
    warnings: list[str]
    generated_at: datetime
```

`create_plan` / `stream_plan` in `src/main.py` convert `PlanRequest` → `TravelRequest`, applying currency normalization (AED→USD via `settings.exchange_rate_usd_aed`) and per-traveler budget scaling **before** the graph ever runs. The Orchestrator agent's original job (parsing raw text and doing currency math) has effectively moved into the API layer.

### 4.3 Itinerary Output — `src/models/itinerary.py`

```python
class Activity(BaseModel):
    name: str; area: str; category: str; time_slot: str
    duration_hours: float; estimated_cost_usd: float
    crowd_level: str; description: str; tips: Optional[str] = None

class DayPlan(BaseModel):
    day_number: int; date: Optional[date] = None
    theme: str; base_area: str
    activities: list[Activity]; transport_notes: str
    meals: list[Activity]; estimated_day_cost_usd: float

class AccommodationPlan(BaseModel):
    hotel_name: str; area: str; star_rating: int
    total_cost_usd: float
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None

class Itinerary(BaseModel):
    request: TravelRequest
    days: list[DayPlan]
    accommodation: AccommodationPlan
    budget_breakdown: BudgetBreakdown
    review_result: ReviewResult
    extra_activities: list[Activity] = []   # added: surplus-budget "bonus" activities
    generated_at: datetime
```

`extra_activities` is a real addition not in the original plan: when the budget agent's allocated categories leave unspent surplus, `merge_draft_itinerary_node` greedily fills that surplus with the highest-cost unused attractions from `DubaiRepository`.

### 4.4 Agent I/O — `src/models/agent_io.py`

```python
class AgentTask(BaseModel):
    task_id: str; agent_type: AgentType; request: TravelRequest
    context: dict = {}; created_at: datetime

class AgentResult(BaseModel):
    task_id: str; agent_type: AgentType; status: ResultStatus
    payload: dict; confidence: float; reasoning: str
    errors: list[str] = []; duration_ms: int
    # classmethods: AgentResult.failed(...), AgentResult.partial_timeout(...)

class ReviewResult(BaseModel):
    approved: bool; score: float; checks: list[CheckResult]
    feedback: list[str]; critical_issues: list[str] = []
    revision_needed: bool; confidence: float = 0.0
```

### 4.5 Graph State — `src/models/state.py`

`PlanningState` is a `TypedDict` (not a Pydantic model, as the original plan assumed), matching LangGraph's preferred state shape:

```python
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
    status: Literal["PARSING","PLANNING","MERGING","VALIDATING",
                     "REVIEWING","REVISING","COMPLETE","PARTIAL","FAILED"]
    errors: Annotated[list[str], add]      # reducer: concatenated across nodes
    warnings: Annotated[list[str], add]    # reducer: concatenated across nodes
```

---

## 5. Agent Architecture

### 5.1 `BaseAgent` contract (`src/agents/base.py`)

```python
class BaseAgent(ABC):
    def __init__(self, llm_client: LLMClient, agent_name: str):
        self.system_prompt = self._load_prompt()   # reads src/prompts/{name}.md
        self._build_tools()

    @abstractmethod
    async def _do_execute(self, task: AgentTask) -> AgentResult: ...

    async def execute(self, task: AgentTask) -> AgentResult:
        # times the call, catches exceptions -> AgentResult(status=FAILED, ...)
        # re-raises TransientLLMError so the API layer can return 503
```

### 5.2 Agents actually in the live graph

| Agent | Runs? | Tools | LLM output schema | Behavior |
|---|---|---|---|---|
| **Orchestrator** | Defined, instantiated in `graph.py`, **but never invoked as a graph node** | none | `OrchestratorResponse` | Dead code path — see §12 |
| **Destination** | ✅ Fan-out node | `SearchTool` | `DestinationResponse` (activities, must_do, food, area suggestions) | Pulls filtered attractions/restaurants/districts from `DubaiRepository` as grounding context, then asks Gemini to recommend |
| **Logistics** | ✅ Fan-out node (`logistics_base`) | `SearchTool`, `PricingTool`, `DistanceTool` | `LogisticsResponse` (accommodation, daily sequences, transport summary) | Picks a price tier from budget, fetches candidate hotels, asks Gemini to sequence days |
| **Budget** | ✅ Fan-out node (`budget_base`) | `PricingTool`, `CurrencyTool` | `BudgetResponse` (breakdown, warnings, suggestions, alternatives) | Computes heuristic food/hotel baselines, asks Gemini to produce final breakdown |
| **Review** | ✅ Final gate node | `DistanceTool`, `PricingTool` (instantiated but not actively called — read-only/available) | `ReviewResponse` (approved, score, checks[], feedback, critical_issues) | Receives the full draft itinerary + original request, does LLM-based QA; drives revision routing |

All active agents currently use **`GeminiClient`** exclusively (`get_llm_client()` in `graph.py` returns `GeminiClient()` regardless of agent type), with a comment noting Groq's free-tier daily token limit was exhausted. `GroqClient` remains implemented and tested but unused in production wiring.

### 5.3 Prompts

Prompts are plain Markdown files in `src/prompts/`, loaded by filename matching the agent's `agent_name.lower()` (e.g. `Destination` → `destination.md`). They are not templated at runtime beyond string concatenation of the user prompt; structured output is enforced via Gemini's `response_schema` / Groq's `response_format={"type": "json_object"}`, not by prompt instruction alone.

---

## 6. Orchestration Graph (LangGraph)

The compiled graph in `src/graph.py` is the **actual orchestrator** — there is no separate orchestrator "agent node" managing the flow; LangGraph's `StateGraph` edges encode the fan-out/fan-in/review/revise logic directly.

### 6.1 Nodes

| Node | Type | Behavior |
|---|---|---|
| `parse_request` | Deterministic | Validates `parsed_request` exists and destination is Dubai/UAE (v1 constraint); sets `status=PLANNING` or `FAILED` |
| `destination` | Agent wrapper | Runs `DestinationAgent` with 30s timeout |
| `logistics_base` | Agent wrapper | Runs `LogisticsAgent` with 30s timeout |
| `budget_base` | Agent wrapper | Runs `BudgetAgent` with 30s timeout |
| `merge_draft_itinerary` | Deterministic | Combines the three agent payloads into a draft `Itinerary` dict; naively assigns 2 activities per day (cycling through the pool); maps logistics accommodation → `AccommodationPlan`; fills `extra_activities` from budget surplus using `DubaiRepository` |
| `logistics_final` | **No-op placeholder** | Comment: "Normally validates sequence using DistanceTool. Mock for now." Returns `{}` |
| `budget_final` | **No-op placeholder** | Comment: "Normally recalculates budget using exact items. Mock for now." Returns `{}` |
| `review` | Agent wrapper | Runs `ReviewAgent` against the merged draft; merges `review_result` back into `itinerary`; sets `status` to `COMPLETE`/`PARTIAL` |
| `increment_revision` | Deterministic | Bumps `revision_count` before looping back into `merge_draft_itinerary` |

### 6.2 Edges

```
parse_request → {destination, logistics_base, budget_base}      (fan-out)
{destination, logistics_base, budget_base} → merge_draft_itinerary  (fan-in, join)
merge_draft_itinerary → {logistics_final, budget_final}          (fan-out, currently no-ops)
{logistics_final, budget_final} → review                          (fan-in, join)
review → conditional_routing:
    approved                      → END
    revision_count >= 2           → END (end_with_warnings)
    failed check "BudgetCompliance"        → budget_base       (re-run + loop back through merge)
    failed check "LogisticsFeasibility"    → logistics_base
    failed check "PreferenceAlignment"/
               "AvoidanceRespected"        → destination
    otherwise                              → increment_revision → merge_draft_itinerary
```

Node execution timeout is 30s per agent (`TIMEOUT` in `graph.py`); the overall request has a 90s ceiling enforced by `asyncio.timeout()` in `src/main.py`. Timeouts produce `AgentResult.partial_timeout(...)` and a warning rather than failing the whole run outright.

### 6.3 Known rough edge

The code comments in `graph.py` itself flag that the `revise_*` routes (which go directly to `budget_base`/`logistics_base`/`destination`) skip `increment_revision`, so `revision_count` is only incremented on the `revise_merge` path. This means the "give up after 2 revisions" cap is not perfectly enforced across all revision types — a known, self-documented gap in the current implementation.

---

## 7. API Layer

`src/main.py` — `create_app()` builds a single FastAPI app (no APIRouter modules; everything is defined inline):

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/v1/health` | GET | Liveness check, used by Railway health checks |
| `/api/v1/plan` | POST | Synchronous plan generation; invokes `graph.ainvoke(...)`, returns full `PlanResponse` |
| `/api/v1/plan/stream` | POST | Same planning flow via `graph.astream(..., stream_mode="updates")`; emits SSE events per node completion, then a final `done` event with `plan_id` |
| `/api/v1/plan/{plan_id}` | GET | Fetches a previously generated plan from Postgres |

Cross-cutting concerns:
- **CORS**: configured from `settings.cors_origins` (parsed from env, supports JSON array or comma-separated string, auto-normalizes bare hostnames to `https://`).
- **Error handling**: dedicated exception handlers for `RequestValidationError` (422), generic `HTTPException`, `TransientLLMError` (503), `RetryError` (unwraps to check for `TransientLLMError`), and a catch-all `Exception` handler (500) — all returning a consistent `{"error": {"code", "message", "details"}}` shape.
- **Itinerary validation failure handling**: if the merged draft fails `PlanResponse` schema validation, the endpoint degrades gracefully to `status="failed"` with detailed field errors appended to `errors`, instead of raising a 500.
- Every plan (successful or not) is persisted via `app.state.store.save(response)`.

---

## 8. Persistence Layer

- **Engine**: `src/utils/db.py` — async SQLAlchemy engine (`asyncpg` driver), pool size 5 / max overflow 5.
- **Schema**: `src/models/db.py` — single `plans` table (`PlanRecord`): `id (UUID pk)`, `status`, `itinerary (JSONB, nullable)`, `errors (JSONB)`, `warnings (JSONB)`, `request_summary (JSONB, nullable — currently unpopulated)`, `generated_at`, `updated_at`, `expires_at (nullable, unused — no TTL/cleanup job exists yet)`.
- **Store abstraction**: `src/utils/store.py` defines a `PlanStore` protocol with two implementations:
  - `InMemoryPlanStore` — dict-backed, used in tests.
  - `PostgresPlanStore` — used in production; `save()` does an upsert via `session.merge()`; `get()` reconstructs a full `PlanResponse` including re-validating the stored JSONB back into an `Itinerary` model.
- **Migrations**: Alembic, one revision (`1a88292faa71_create_plans_table.py`) creating the `plans` table. `settings.database_url` validator normalizes `postgres://`/`postgresql://` to `postgresql+asyncpg://` and strips Neon-style `channel_binding`/`sslmode` query params that asyncpg doesn't accept directly.

---

## 9. Frontend

Independent Vite + React 19 SPA in `frontend/`, deployed separately to Vercel (`vercel.json` rewrites all paths to `index.html` for client-side routing).

- **Routing** (`App.jsx`, React Router 7): `/` (LandingPage — trip form), `/status/:planId` (progress while streaming), `/itinerary/:planId` (final result), `/retrieve` (look up a plan by ID), `/error`, and a catch-all → `ErrorPage`.
- **API client** (`src/api.js`):
  - `createPlan(payload, onProgress)` — POSTs to `/api/v1/plan/stream`, manually parses the `text/event-stream` body (reads the fetch stream, splits on `data: ` lines), calls `onProgress(nodeName)` per SSE event, and resolves with `{plan_id}` on `done`.
  - `getPlan(planId)` — GET `/api/v1/plan/{id}`.
  - `getHealth()` — GET `/api/v1/health`.
  - `API_BASE` is read from `VITE_API_URL` and auto-prefixed with `https://` if no scheme is given (supports bare Railway hostnames).
- **Styling**: Tailwind CSS 4 via the `@tailwindcss/vite` plugin.
- **Linting**: `oxlint` (not ESLint).

There is no server-side rendering, and no shared code/package between `frontend/` and the Python backend — communication is entirely over the HTTP/SSE API contract in `src/models/api.py`.

---

## 10. Configuration & Environment

`src/config.py` — `pydantic-settings` `Settings`, loaded from `.env`:

| Setting | Default | Notes |
|---|---|---|
| `gemini_api_key`, `gemini_model` | — / `gemini-3.6-flash` | Required; used by all live agents |
| `groq_api_key`, `groq_model` | — / `llama-3.3-70b-versatile` | Required by settings schema but currently unused at runtime |
| `llm_temperature` / `llm_max_tokens` | 0.7 / 8192 | Shared across all LLM calls |
| `max_revision_loops` | 2 | Referenced conceptually; graph's actual cap is hardcoded as `rev_count >= 2` in `route_after_review`, not read from this setting |
| `agent_timeout_seconds` / `request_timeout_seconds` | 30 / 90 | `graph.py` hardcodes its own `TIMEOUT = 30` rather than reading `agent_timeout_seconds` |
| `cors_origins` | localhost:3000/5173 | Custom parser supports JSON array, CSV, or bare hostnames |
| `exchange_rate_usd_aed` | 3.67 | Static rate, not fetched from a live FX API |
| `database_url` | local Postgres | Validator normalizes scheme and strips Neon-specific query params |
| `app_env`, `app_port`, `log_level` | development / 8000 / INFO | Standard app metadata |

**Deviation from plan**: `parallel_agent_execution` setting exists but the LangGraph fan-out edges provide parallelism structurally — the flag isn't read anywhere in `graph.py`.

---

## 11. Deployment

- **Backend**: Dockerized (`python:3.12-slim`, `uv sync --frozen --no-dev`), deployed to **Railway** (`railway.toml`, Dockerfile builder, health check on `/api/v1/health`, restart-on-failure with 3 retries).
- **Frontend**: Deployed to **Vercel** as a static Vite build, independent of the backend's release cycle. Talks to the backend exclusively via `VITE_API_URL`.
- **Database**: External managed Postgres (URL format compatible with Neon, given the `channel_binding`/`sslmode` normalization logic in `config.py`).

---

## 12. Deviations from the Original Plan

The original [architecture.md](architecture.md) described a design with an active Orchestrator agent doing NLP parsing, dual-LLM-provider usage, and a strict destination/logistics/budget/review pipeline with real revalidation stages. The actual implementation differs in several material ways:

1. **Orchestrator agent is not wired into the graph.** `OrchestratorAgent` still exists (`src/agents/orchestrator.py`) and is instantiated in `graph.py`, but no graph node calls it. Request parsing became a deterministic step in the FastAPI layer (`src/main.py`) instead of an LLM call — the client sends a structured `PlanRequest`, not a raw natural-language query.
2. **Single LLM provider in production.** The plan called for Gemini (parallel agents) + Groq (review). In practice, `get_llm_client()` in `graph.py` routes **every** agent — including Review — to `GeminiClient`, due to Groq free-tier token limits being exhausted. `GroqClient` remains fully implemented and unit-tested but dormant.
3. **"Final validation" stages are stubs.** `logistics_final` and `budget_final` nodes exist in the graph purely as structural placeholders (each is a no-op returning `{}`), with comments acknowledging they should eventually re-validate sequencing/budget using `DistanceTool`/`PricingTool` against the merged draft. Today, the Review Agent is the only real post-merge QA step.
4. **State is a `TypedDict`, not a Pydantic `BaseModel`.** `PlanningState` uses LangGraph's idiomatic `TypedDict` + `Annotated[..., add]` reducer pattern for `errors`/`warnings`, rather than the Pydantic model sketched in the plan.
5. **Deterministic, not LLM-driven, day-assignment.** `merge_draft_itinerary_node` assigns activities to days with a simple round-robin/cycling slice (`activities[:2]`) rather than an agent reasoning about pacing — a pragmatic, non-LLM merge step.
6. **Added `extra_activities` / budget-surplus backfill.** Not present in the original design: when the budget breakdown leaves unallocated surplus, the merge step greedily adds the highest-cost remaining attractions from the local repository, up to the surplus.
7. **Revision loop bookkeeping has a known gap.** `revision_count` is only reliably incremented via the `revise_merge`/`increment_revision` path; direct re-routes to `budget_base`/`logistics_base`/`destination` bypass the increment, as flagged by inline comments in `graph.py`.
8. **No live external APIs for pricing/distance/currency.** All three "tools" are grounded in **static local data** (`dubai_wikivoyage.json` + `dubai_luxury.json`, scraped once via `scraper.py`) or **hardcoded heuristics** (a 5-district travel-time matrix in `distance.py`, a fixed AED/USD rate in config) — not live search, mapping, or FX APIs as implied by tool names.
9. **Persistence added.** The original plan had no explicit persistence layer; the actual system adds a full Postgres + Alembic + SQLAlchemy async stack (`plans` table, `PostgresPlanStore`) so plans can be retrieved later by ID via `GET /api/v1/plan/{id}`.
10. **Streaming endpoint added.** `/api/v1/plan/stream` (SSE) is a real addition supporting incremental frontend progress updates per graph node, absent from the original design.
11. **Frontend added.** A full React SPA (`frontend/`) was built and deployed separately (Vercel) — this consumes the API but was not part of the original backend-focused architecture document.

---

## 13. Testing

`tests/` contains:
- `test_agents.py` — per-agent unit behavior
- `test_api.py` — FastAPI endpoint tests
- `test_contracts.py` — schema/contract checks between agent payloads and Pydantic models
- `test_e2e.py` — end-to-end graph runs
- `test_llm_client.py` — `GeminiClient`/`GroqClient` retry & error-mapping behavior
- `test_models.py` — Pydantic model validation
- `test_postgres.py` — `PostgresPlanStore` behavior
- `test_scraper.py` — Wikivoyage scraper parsing
- `test_smoke.py` — basic sanity checks
- `test_tools.py` — `PricingTool`, `CurrencyTool`, `DistanceTool`, `SearchTool`, `DubaiRepository`

Outside `tests/`, there are also standalone manual scripts not run under `pytest`: `test_live.py` (repo root), and `scripts/demo.py` / `scripts/test_structured_api.py`.
