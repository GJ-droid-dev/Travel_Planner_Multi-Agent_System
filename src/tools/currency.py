from decimal import Decimal
from typing import Dict, Any
from src.config import settings

class CurrencyTool:
    """Deterministic AED ↔ USD converter based on config rate."""
    
    def __init__(self):
        self.rate = Decimal(str(getattr(settings, "exchange_rate_usd_aed", 3.67)))
        
    def aed_to_usd(self, amount_aed: Decimal) -> Decimal:
        return amount_aed / self.rate
        
    def usd_to_aed(self, amount_usd: Decimal) -> Decimal:
        return amount_usd * self.rate
        
    def convert(
        self, 
        amount: float, 
        from_currency: str, 
        to_currency: str
    ) -> Dict[str, Any]:
        """Convert an amount between AED and USD."""
        amt = Decimal(str(amount))
        
        if from_currency.upper() == "AED" and to_currency.upper() == "USD":
            output = self.aed_to_usd(amt)
        elif from_currency.upper() == "USD" and to_currency.upper() == "AED":
            output = self.usd_to_aed(amt)
        else:
            return {
                "error": f"Unsupported conversion from {from_currency} to {to_currency}"
            }
            
        return {
            "input_amount": float(amt),
            "from_currency": from_currency.upper(),
            "output_amount": round(float(output), 2),
            "to_currency": to_currency.upper(),
            "exchange_rate": float(self.rate),
            "rate_source": "application_configuration"
        }
