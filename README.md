# AI Travel Planner

A fully autonomous, multi-agent AI travel planning system built with **FastAPI**, **LangGraph**, and **Pydantic**. 

This system generates highly detailed, hyper-personalized, and logically sound multi-day itineraries for Dubai (and other destinations) by orchestrating a team of specialized AI agents working in a Hybrid-DAG (Directed Acyclic Graph) architecture.

## Features
- **Multi-Agent Orchestration**: Specialized agents for Orchestration, Destination Research, Logistics, Budgeting, and Review.
- **Hybrid-DAG Architecture**: LangGraph enables parallel execution (e.g. Budget and Logistics) and cyclical review loops to refine plans before presenting them.
- **Resilience**: Fallback parsing, timeout handling, partial plan recovery, and structured output parsing.
- **FastAPI Backend**: Fully async RESTful API for triggering planning jobs and checking system health.

## Quick Start

### Prerequisites
- Python 3.12+
- `uv` (fast Python package installer and resolver)

### Installation
1. Clone the repository and navigate to the project root.
2. Create and activate a virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   uv pip install -e .
   ```
4. Copy the environment template and add your API keys:
   ```bash
   cp .env.example .env
   # Edit .env to add your GEMINI_API_KEY and/or GROQ_API_KEY
   ```

### Running the API
Start the FastAPI server:
```bash
uv run uvicorn src.main:app --reload
```
The API will be available at `http://127.0.0.1:8000`. 
- **Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Running Tests
To run the full test suite (unit, integration, and E2E tests):
```bash
uv run pytest tests/ -v
```

## Architecture
See the [Implementation Plan](Docs/implementation-plan.md) and [Walkthrough](Docs/walkthrough.md) for an in-depth breakdown of the Hybrid-DAG design.

- **`src/graph.py`**: The LangGraph definition.
- **`src/agents/`**: Core logic for the specialized AI agents.
- **`src/models/`**: Pydantic schemas enforcing strict I/O contracts.
- **`src/tools/`**: External tools (distance calculator, pricing heuristics).

## License
MIT
