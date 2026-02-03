"""Electricity price management"""

from .api_client import APIClient


class PriceManager:
    """Manages electricity price settings"""

    def __init__(self, api_client: APIClient):
        self.api = api_client

    def set_electricity_price(self, price: float):
        """Set electricity price per kWh"""
        self.api._post("/settings/electricity-price", {"price": price})
        print(f"✓ Electricity price set to {price} per kWh")

    def get_electricity_price(self):
        """Get current electricity price"""
        result = self.api._get("/settings/electricity-price")
        price = result.get("price", 0.0)
        if price > 0:
            print(f"💰 Current electricity price: {price} per kWh")
        else:
            print(f"💰 No electricity price set (set with: lab set price <value>)")
