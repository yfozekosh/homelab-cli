"""Test electricity price endpoints"""
import pytest

class TestElectricityPrice:
    def test_get_price_returns_200(self, api_client):
        response = api_client.get("/config/electricity-price")
        assert response.status_code == 200

    def test_get_price_returns_configured_value(self, api_client):
        response = api_client.get("/config/electricity-price")
        data = response.json()
        assert data["price"] == 0.25

    def test_set_price_returns_200(self, api_client):
        response = api_client.put("/config/electricity-price", json={"price": 0.30})
        assert response.status_code == 200
