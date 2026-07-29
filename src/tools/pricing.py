from typing import Dict, Any, Optional
from src.tools.repository import DubaiRepository

class PricingTool:
    """Grounded cost tool for hotels, meals, and attractions."""
    
    def __init__(self):
        self.repo = DubaiRepository()
        
    def search_hotels(
        self,
        area: Optional[str] = None,
        price_tier: Optional[str] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """Lookup verified accommodation options by area and budget tier."""
        hotels = self.repo.get_hotels()
        filtered = hotels
        if area:
            filtered = [h for h in filtered if area.lower() in str(h.get("area", "")).lower() or area.lower() in str(h.get("description", "")).lower()]
        if price_tier:
            filtered = [h for h in filtered if price_tier.lower() == str(h.get("price_tier", "")).lower()]
            
        records = filtered[:limit]
        return {
            "status": "found" if records else "not_found",
            "source": "dubai_wikivoyage.json",
            "records": records,
            "currency": "AED",
            "warnings": [] if records else ["No matching hotel records exists in the local Dubai knowledge base."]
        }
        
    def get_activity_price(self, activity_name: str) -> Dict[str, Any]:
        """Attempt to find price info for a specific activity name."""
        attractions = self.repo.get_attractions()
        for a in attractions:
            if activity_name.lower() in str(a.get("name", "")).lower():
                price = a.get("price")
                if price:
                    return {
                        "status": "found",
                        "source": "dubai_wikivoyage.json",
                        "price_info": price,
                        "currency": "AED"
                    }
        return {
            "status": "not_found",
            "source": "dubai_wikivoyage.json",
            "warnings": [f"No price information found for '{activity_name}'"]
        }

    def estimate_food_budget(self, days: int, travelers: int, price_tier: str) -> Dict[str, Any]:
        """Return a rough food budget estimate based on price tier."""
        # Simple heuristic based on Wikivoyage typical prices
        daily_per_person = {
            "budget": 100,      # AED
            "mid_range": 250,   # AED
            "splurge": 600      # AED
        }.get(price_tier.lower(), 250)
        
        total_aed = days * travelers * daily_per_person
        
        return {
            "status": "estimated",
            "source": "heuristics",
            "total_estimated_aed": total_aed,
            "daily_per_person_aed": daily_per_person,
            "currency": "AED"
        }
