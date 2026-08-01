import asyncio
import sys
from pydantic import ValidationError
from uuid import UUID
from datetime import datetime

import os
# Adjust sys path so we can import src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.models.api import PlanRequest

async def main():
    try:
        req = PlanRequest(
            destination="Dubai, UAE",
            duration_days=5,
            travelers=2,
            budget_amount=3000,
            budget_currency="USD",
            budget_scope="Total trip",
            include_accommodation=True,
            interests=["Food", "Culture"],
            avoidances=["Crowds"],
            extra_notes="Vegetarian"
        )
        print("Validation Successful:")
        print(req.model_dump())
        
        # Test error
        try:
            PlanRequest(
                duration_days=0, # Invalid
                travelers=2,
                budget_amount=-1, # Invalid
                budget_currency="EUR", # Invalid
                budget_scope="Total trip",
                include_accommodation=True,
            )
            print("Validation FAILED: Expected an error but got none.")
        except ValidationError as e:
            print("Caught expected validation error:")
            print(e)
            
    except Exception as e:
        print(f"Failed with {e}")

if __name__ == "__main__":
    asyncio.run(main())
