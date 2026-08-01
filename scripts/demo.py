import asyncio
import time
import httpx
from rich.console import Console

console = Console()

SCENARIOS = [
    {"name": "Standard request", "query": "5-day Dubai trip, $3000, food + architecture + desert, avoid crowds"},
    {"name": "Budget-constrained", "query": "3-day budget Dubai trip, $500 for 2 people"},
    {"name": "Preference-heavy", "query": "4-day Dubai trip. Love desert, hate shopping."},
    {"name": "Minimal input", "query": "Dubai trip"},
    {"name": "Revision trigger", "query": "Plan 5 days in Dubai for 2 people with $800. Include a luxury hotel, daily fine dining, Burj Khalifa, desert safari, private driver, and shopping."}
]

async def run_demo():
    console.print("[bold blue]Starting Travel Planner Demo[/bold blue]\n")
    
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
        # Check health
        try:
            health = await client.get("/api/v1/health")
            if health.status_code != 200:
                console.print("[bold red]API is not running. Start it with `uv run uvicorn src.main:app`[/bold red]")
                return
        except httpx.ConnectError:
            console.print("[bold red]API is not running. Start it with `uv run uvicorn src.main:app`[/bold red]")
            return
            
        for i, scenario in enumerate(SCENARIOS, 1):
            console.print(f"[bold yellow]Scenario {i}: {scenario['name']}[/bold yellow]")
            console.print(f"Query: [italic]'{scenario['query']}'[/italic]")
            
            start_time = time.time()
            response = await client.post("/api/v1/plan", json={"query": scenario["query"]}, timeout=180.0)
            latency = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                status = data.get("status")
                
                color = "green" if status == "completed" else "yellow" if status == "partial" else "red"
                console.print(f"Result: [{color}]{status.upper()}[/{color}] (took {latency:.2f}s)")
                
                if data.get("warnings"):
                    for w in data["warnings"]:
                        console.print(f"  [yellow]⚠ {w}[/yellow]")
                
                if data.get("errors"):
                    for e in data["errors"]:
                        console.print(f"  [red]✖ {e}[/red]")
                        
                if data.get("itinerary"):
                    budget = data["itinerary"]["budget_breakdown"]
                    console.print(f"  [cyan]Budget:[//cyan] ${budget['estimated_total_usd']} / ${budget['total_budget_usd']}")
                    
            else:
                console.print(f"[bold red]API Error {response.status_code}[/bold red]")
            
            console.print("-" * 40)

if __name__ == "__main__":
    asyncio.run(run_demo())
