from typing import List, Dict, Any, Optional
from src.tools.repository import DubaiRepository

class SearchTool:
    """Read-only retrieval layer to ground the Destination Agent."""
    
    def __init__(self):
        self.repo = DubaiRepository()
        
    def find_attractions(
        self, 
        preferences: Optional[List[str]] = None, 
        areas: Optional[List[str]] = None,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Find attractions, optionally filtering by area or simple keyword match for preferences."""
        attractions = self.repo.get_attractions()
        
        filtered = attractions
        if areas:
            # We don't have perfect area metadata for all attractions in the basic JSON, 
            # so we'll do a simple substring match on description if area isn't explicitly defined.
            areas_lower = [a.lower() for a in areas]
            filtered = [
                a for a in filtered 
                if any(area in str(a.get("area", "")).lower() or area in str(a.get("description", "")).lower() for area in areas_lower)
            ]
            
        if preferences:
            prefs_lower = [p.lower() for p in preferences]
            filtered = [
                a for a in filtered
                if any(p in str(a.get("description", "")).lower() or p in str(a.get("name", "")).lower() for p in prefs_lower)
            ]
            
        records = filtered[:limit]
        return {
            "status": "found" if records else "not_found",
            "source": "dubai_wikivoyage.json",
            "records": records,
            "warnings": [] if records else ["No matching attractions found."]
        }
        
    def find_restaurants(
        self, 
        area: Optional[str] = None, 
        price_tier: Optional[str] = None,
        cuisine: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Find restaurants based on area, price tier, or cuisine."""
        rests = self.repo.get_restaurants()
        
        filtered = rests
        if area:
            filtered = [r for r in filtered if area.lower() in str(r.get("area", "")).lower() or area.lower() in str(r.get("description", "")).lower()]
        if price_tier:
            filtered = [r for r in filtered if price_tier.lower() == str(r.get("price_tier", "")).lower()]
        if cuisine:
            filtered = [r for r in filtered if cuisine.lower() in str(r.get("cuisine", "")).lower() or cuisine.lower() in str(r.get("description", "")).lower()]
            
        records = filtered[:limit]
        return {
            "status": "found" if records else "not_found",
            "source": "dubai_wikivoyage.json",
            "records": records,
            "warnings": [] if records else ["No matching restaurants found."]
        }

    def find_districts(self) -> Dict[str, Any]:
        """Return a list of major Dubai districts."""
        districts = self.repo.get_districts()
        return {
            "status": "found" if districts else "not_found",
            "source": "dubai_wikivoyage.json",
            "records": districts,
            "warnings": [] if districts else ["No districts found."]
        }
