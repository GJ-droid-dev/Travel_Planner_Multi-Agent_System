import pytest
from decimal import Decimal
from src.tools.repository import DubaiRepository
from src.tools.search import SearchTool
from src.tools.pricing import PricingTool
from src.tools.distance import DistanceTool
from src.tools.currency import CurrencyTool

@pytest.fixture(scope="module")
def repo():
    return DubaiRepository()

def test_repository_loads_data(repo):
    assert len(repo.get_districts()) > 0
    assert len(repo.get_attractions()) > 0
    assert len(repo.get_restaurants()) > 0
    assert len(repo.get_hotels()) > 0

def test_search_tool():
    tool = SearchTool()
    
    # Test finding Burj Khalifa
    res = tool.find_attractions(preferences=["Burj Khalifa"])
    assert res["status"] == "found"
    assert any("Burj Khalifa" in a["name"] for a in res["records"])
    
    # Test finding districts
    dists = tool.find_districts()
    assert dists["status"] == "found"
    assert len(dists["records"]) > 0

def test_pricing_tool():
    tool = PricingTool()
    
    # Test hotel pricing extraction
    res = tool.search_hotels(price_tier="budget")
    assert res["status"] == "found"
    assert all(h["price_tier"] == "budget" for h in res["records"])
    
    # Test activity pricing
    act = tool.get_activity_price("Burj Khalifa")
    assert act["status"] == "found"
    assert "dirham" in act["price_info"].lower()
    
    # Test missing activity
    missing = tool.get_activity_price("Fake Activity Not Found")
    assert missing["status"] == "not_found"

def test_distance_tool():
    tool = DistanceTool()
    
    # Test valid heuristic lookup
    res = tool.estimate_travel("Deira", "Marina")
    assert res["estimated_minutes"] == "50-65"
    assert res["feasible_for_two_hour_window"] is False
    
    # Test fast transit
    res_fast = tool.estimate_travel("Downtown Dubai", "Bur Dubai")
    assert "15" in res_fast["estimated_minutes"]
    assert res_fast["feasible_for_two_hour_window"] is True
    
    # Test identical districts
    res_same = tool.estimate_travel("Deira", "Deira")
    assert res_same["recommended_mode"] == "walking/taxi"
    assert "10-15" in res_same["estimated_minutes"]

def test_currency_tool():
    tool = CurrencyTool()
    tool.rate = Decimal("3.67") # force rate for predictable testing
    
    # Test AED to USD
    res1 = tool.convert(367, "AED", "USD")
    assert res1["output_amount"] == 100.0
    
    # Test USD to AED
    res2 = tool.convert(100, "USD", "AED")
    assert res2["output_amount"] == 367.0
