# Multi-Agent Architecture

The AI Travel Planner is powered by a team of 5 specialized agents, coordinated through a Hybrid-DAG implemented via LangGraph. This document outlines the distinct role, capabilities, and I/O contracts of each agent.

## 1. Orchestrator Agent (`src/agents/orchestrator.py`)
- **Role:** The entry point. It parses the natural language query from the user into a structured schema, filling in defaults (like duration or destination) if the user implies them or leaves them blank.
- **Tools:** None. Relies purely on LLM reasoning and Pydantic constraints.
- **Input:** Natural language string (e.g., "5 days in Dubai with a $3000 budget").
- **Output:** `TravelRequest` (destination, duration, budget, travelers, preferences, avoidances).

## 2. Destination Agent (`src/agents/destination.py`)
- **Role:** The local expert. Suggests a wide pool of activities, restaurants, and areas tailored to the parsed `TravelRequest`. It does not sequence them into a timeline.
- **Tools:** `SearchTool`, `DubaiRepository`.
- **Input:** `TravelRequest`.
- **Output:** `DestinationResponse` (categorized lists of recommended activities, must-do attractions, and dining options).

## 3. Logistics Agent (`src/agents/logistics.py`)
- **Role:** The scheduler. It runs in two phases:
  - **Base Phase:** Proposes a daily sequence template based on the parsed request.
  - **Final Phase:** Takes the activities selected during the Merge Node and ensures they are physically feasible, estimating transit times and organizing them by geographical proximity.
- **Tools:** `DistanceTool`.
- **Input:** `TravelRequest`, `DestinationResponse` (in final phase).
- **Output:** `LogisticsResponse` (daily sequences, transport summaries, accommodation suggestions).

## 4. Budget Agent (`src/agents/budget.py`)
- **Role:** The accountant. It also runs in two phases:
  - **Base Phase:** Allocates the total user budget across high-level categories (stay, food, activities).
  - **Final Phase:** Takes the finalized activities and hotel from the Merge Node and calculates exact costs, issuing warnings if the itinerary exceeds the budget.
- **Tools:** `PricingTool`, `CurrencyTool`.
- **Input:** `TravelRequest`.
- **Output:** `BudgetResponse` (exact budget breakdown, warnings, money-saving suggestions).

## 5. Review Agent (`src/agents/review.py`)
- **Role:** The quality assurance engine. It inspects the fully merged `DraftItinerary` against the user's initial constraints. If the itinerary fails critical checks (e.g., drastically over budget or missing non-negotiable preferences), it rejects the plan and generates targeted feedback.
- **Tools:** None.
- **Input:** `TravelRequest`, `DraftItinerary`.
- **Output:** `ReviewResponse` (approved boolean, feedback strings, granular check scores). If `approved` is False, the LangGraph routes execution back to the Merge/Revise nodes.
