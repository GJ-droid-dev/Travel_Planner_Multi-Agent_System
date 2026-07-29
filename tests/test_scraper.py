import pytest
from bs4 import BeautifulSoup
from src.tools.scraper import parse_section

def test_parse_section():
    html = """
    <h2><span id="See">See</span></h2>
    <div class="vcard">
        <span class="org">Burj Khalifa</span>
        <span class="geo">
            <span class="latitude">25.1972</span>
            <span class="longitude">55.2744</span>
        </span>
        <div class="listing-content">Tallest building in the world.</div>
        <span class="listing-price">150 AED</span>
    </div>
    <h2><span id="Do">Do</span></h2>
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    items = parse_section(soup, "See")
    assert len(items) == 1
    assert items[0]["name"] == "Burj Khalifa"
    assert items[0]["description"] == "Tallest building in the world."
    assert items[0]["price"] == "150 AED"
    assert items[0]["coordinates"]["lat"] == 25.1972
    assert items[0]["coordinates"]["lon"] == 55.2744

    items_do = parse_section(soup, "Do")
    assert len(items_do) == 0
