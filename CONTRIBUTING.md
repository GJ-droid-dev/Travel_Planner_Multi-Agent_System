# Contributing Guide

Welcome to the AI Travel Planner! The project is designed to be highly modular. 

## Adding a New Agent
1. **Create the Agent Class**: In `src/agents/`, create a new Python file (e.g., `weather.py`) inheriting from `AgentBase`.
2. **Define the Response Schema**: In the same file, define a Pydantic model (e.g., `WeatherResponse`) to enforce strict output parsing.
3. **Write the Prompt**: Add a markdown file in `src/prompts/` (e.g., `weather.md`) detailing the system instructions.
4. **Register in the Graph**: Update `src/graph.py` to instantiate your agent and add it as a node to the LangGraph `StateGraph`.

## Adding a New Destination
Currently, the system is hardcoded with a `DubaiRepository`. To add Paris:
1. Create `src/tools/paris_repository.py`.
2. Update `src/tools/search.py` and `src/tools/pricing.py` to route queries based on the `destination` specified in the `TravelRequest`.
3. Add a raw data file to `src/data/paris_wikivoyage.json`.

## Best Practices
- **Strict Pydantic schemas**: Always use Pydantic `Field` descriptions; the LLMs use these as instructions for formatting JSON.
- **Fail Gracefully**: If an API call to an LLM or an external tool fails, return a partial object or a generic warning rather than crashing the orchestrator pipeline.
- **Run the Tests**: Before committing, ensure you run `uv run pytest tests/ -v`.
