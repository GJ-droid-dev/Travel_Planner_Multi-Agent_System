import json
import logging
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class DubaiRepository:
    """A singleton repository that loads and indexes the scraped Wikivoyage data once."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DubaiRepository, cls).__new__(cls)
            cls._instance._load_data()
        return cls._instance
        
    def _load_data(self):
        data_path = Path(__file__).parent.parent / "data" / "dubai_wikivoyage.json"
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except Exception as e:
            print(f"Exception loading JSON from {data_path}: {e}")
            logger.error(f"Failed to load Dubai Wikivoyage data: {e}")
            self.data = {}
            
        # Combine 'see', 'do', and 'buy' into attractions
        self.attractions = self.data.get("see", []) + self.data.get("do", []) + self.data.get("buy", [])
        
        # Flatten restaurants and inject price tier
        self.restaurants = []
        eat_data = self.data.get("eat", {})
        if isinstance(eat_data, dict):
            for tier, rests in eat_data.items():
                for r in rests:
                    r["price_tier"] = tier
                    self.restaurants.append(r)
        elif isinstance(eat_data, list):
            for i, r in enumerate(eat_data):
                r["price_tier"] = "budget" if i % 3 == 0 else "mid_range" if i % 3 == 1 else "splurge"
                self.restaurants.append(r)
            
        # Flatten hotels and inject price tier
        self.hotels = []
        sleep_data = self.data.get("sleep", {})
        if isinstance(sleep_data, dict):
            for tier, hots in sleep_data.items():
                for h in hots:
                    h["price_tier"] = tier
                    self.hotels.append(h)
        elif isinstance(sleep_data, list):
            for i, h in enumerate(sleep_data):
                h["price_tier"] = "budget" if i % 3 == 0 else "mid_range" if i % 3 == 1 else "splurge"
                self.hotels.append(h)
            
        self.districts = [
            {"name": "Deira", "description": "Old Dubai, known for souks."},
            {"name": "Bur Dubai", "description": "Historic district with heritage sites."},
            {"name": "Downtown Dubai", "description": "Modern hub with Burj Khalifa and Dubai Mall."},
            {"name": "Jumeirah", "description": "Coastal residential area with beaches."},
            {"name": "Dubai Marina", "description": "High-rise waterfront district."}
        ]
        
    def get_attractions(self) -> List[Dict[str, Any]]:
        return self.attractions
        
    def get_restaurants(self) -> List[Dict[str, Any]]:
        return self.restaurants
        
    def get_hotels(self) -> List[Dict[str, Any]]:
        return self.hotels
        
    def get_districts(self) -> List[Dict[str, Any]]:
        return self.districts
