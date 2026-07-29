import json
import os
from pathlib import Path
import httpx
from bs4 import BeautifulSoup
import structlog
from typing import Dict, Any

logger = structlog.get_logger(__name__)

WIKIVOYAGE_DUBAI_URL = "https://en.wikivoyage.org/wiki/Dubai/Jumeirah"
CACHE_FILE = Path(__file__).parent.parent / "data" / "dubai_wikivoyage.json"

async def fetch_wikivoyage_html() -> str:
    """Fetch the raw HTML from Wikivoyage."""
    headers = {"User-Agent": "TravelPlannerBot/1.0 (https://github.com/GJ-droid-dev/Travel_Planner_Multi-Agent_System)"}
    async with httpx.AsyncClient(headers=headers) as client:
        response = await client.get(WIKIVOYAGE_DUBAI_URL, timeout=30.0)
        response.raise_for_status()
        return response.text

def parse_section(soup: BeautifulSoup, section_id: str) -> list[Dict[str, Any]]:
    """
    Extract listings from a specific Wikivoyage section.
    Wikivoyage listings typically use class 'vcard'.
    """
    items = []
    # Find the heading with the given ID
    heading = soup.find(id=section_id)
    if not heading:
        logger.warning(f"Section {section_id} not found on Wikivoyage page.")
        return items
        
    # Find the parent heading tag (h2, h3, etc.)
    heading_tag = heading.parent
    
    # Iterate through siblings until the next heading of the same or higher level
    curr = heading_tag.next_sibling
    while curr:
        if curr.name and curr.name.startswith('h') and curr.name <= heading_tag.name:
            break
            
        if curr.name:
            # Look for vcard elements within this sibling
            vcards = curr.find_all(class_='vcard') if curr.find_all else []
            # Also check if the sibling itself is a vcard
            if 'vcard' in curr.get('class', []):
                vcards.append(curr)
                
            for vcard in vcards:
                name_tag = vcard.find(class_='org') or vcard.find(class_='fn')
                name = name_tag.text.strip() if name_tag else "Unknown"
                
                # Extract coordinates if available
                geo_tag = vcard.find(class_='geo')
                lat, lon = None, None
                if geo_tag:
                    lat_tag = geo_tag.find(class_='latitude')
                    lon_tag = geo_tag.find(class_='longitude')
                    if lat_tag and lon_tag:
                        try:
                            lat = float(lat_tag.text)
                            lon = float(lon_tag.text)
                        except ValueError:
                            pass

                # Description usually follows the listing details
                desc_tag = vcard.find(class_='listing-content')
                description = desc_tag.text.strip() if desc_tag else ""
                
                # Try to extract price or budget info if available
                price_tag = vcard.find(class_='listing-price')
                price = price_tag.text.strip() if price_tag else ""

                items.append({
                    "name": name,
                    "description": description,
                    "price": price,
                    "coordinates": {"lat": lat, "lon": lon} if lat and lon else None
                })
                
        curr = curr.next_sibling
        
    return items

async def scrape_dubai_data(force_refresh: bool = False) -> Dict[str, Any]:
    """Scrape Dubai data from Wikivoyage and cache it to a local JSON file."""
    if not force_refresh and CACHE_FILE.exists():
        logger.info("Loading Dubai data from cache.", path=str(CACHE_FILE))
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    logger.info("Scraping Dubai data from Wikivoyage.", url=WIKIVOYAGE_DUBAI_URL)
    html = await fetch_wikivoyage_html()
    soup = BeautifulSoup(html, 'html.parser')
    
    data = {
        "see": parse_section(soup, "See"),
        "do": parse_section(soup, "Do"),
        "buy": parse_section(soup, "Buy"),
        "eat": parse_section(soup, "Eat"),
        "sleep": parse_section(soup, "Sleep"),
        "get_around": parse_section(soup, "Get_around")
    }
    
    # Ensure data directory exists
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    logger.info("Successfully scraped and cached Dubai data.", 
                total_items=sum(len(items) for items in data.values()))
    
    return data

if __name__ == "__main__":
    import asyncio
    asyncio.run(scrape_dubai_data(force_refresh=True))
