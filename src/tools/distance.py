from typing import Dict, Any, Optional
from src.tools.repository import DubaiRepository

class DistanceTool:
    """Estimates travel time and feasibility between Dubai districts."""
    
    def __init__(self):
        self.repo = DubaiRepository()
        
        # A simple hardcoded heuristic table for major districts for demonstration.
        # In a real app, this would use a routing API or be parsed from the transport section.
        self._travel_matrix = {
            "deira": {"bur dubai": 15, "downtown": 25, "jumeirah": 35, "marina": 50},
            "bur dubai": {"deira": 15, "downtown": 15, "jumeirah": 25, "marina": 40},
            "downtown": {"deira": 25, "bur dubai": 15, "jumeirah": 15, "marina": 25},
            "jumeirah": {"deira": 35, "bur dubai": 25, "downtown": 15, "marina": 20},
            "marina": {"deira": 50, "bur dubai": 40, "downtown": 25, "jumeirah": 20}
        }
        
    def normalize_area(self, area: str) -> Optional[str]:
        area_lower = area.lower()
        if "deira" in area_lower: return "deira"
        if "bur dubai" in area_lower or "fahidi" in area_lower: return "bur dubai"
        if "downtown" in area_lower or "zayed" in area_lower or "khalifa" in area_lower: return "downtown"
        if "jumeirah" in area_lower or "palm" in area_lower: return "jumeirah"
        if "marina" in area_lower or "jbr" in area_lower: return "marina"
        return None
        
    def estimate_travel(
        self, 
        origin_area: str, 
        destination_area: str, 
        preferred_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """Estimate travel times using a heuristic matrix for Dubai districts."""
        if not origin_area or not destination_area:
            return {"status": "error", "message": "Origin and destination must be provided."}
            
        norm_orig = self.normalize_area(origin_area)
        norm_dest = self.normalize_area(destination_area)
        
        if norm_orig == norm_dest and norm_orig is not None:
            return {
                "origin": origin_area,
                "destination": destination_area,
                "recommended_mode": "walking/taxi",
                "estimated_minutes": "10-15",
                "confidence": "estimated",
                "feasible_for_two_hour_window": True,
                "notes": []
            }
            
        if norm_orig and norm_dest:
            base_time = self._travel_matrix.get(norm_orig, {}).get(norm_dest) or self._travel_matrix.get(norm_dest, {}).get(norm_orig)
            if base_time:
                min_time = base_time
                max_time = base_time + 15
                feasible = max_time < 45
                return {
                    "origin": origin_area,
                    "destination": destination_area,
                    "recommended_mode": preferred_mode or "metro/taxi",
                    "estimated_minutes": f"{min_time}-{max_time}",
                    "confidence": "estimated",
                    "feasible_for_two_hour_window": feasible,
                    "notes": [] if feasible else ["This movement takes significant time; do not schedule consecutive short activities between these areas."]
                }
                
        return {
            "origin": origin_area,
            "destination": destination_area,
            "recommended_mode": "taxi",
            "estimated_minutes": "unknown",
            "confidence": "unknown",
            "feasible_for_two_hour_window": False,
            "notes": ["Distance is unknown in local knowledge base. Assume 45+ minutes."]
        }
