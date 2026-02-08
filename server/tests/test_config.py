"""Test electricity price endpoints"""

class TestElectricityPrice:
    def test_get_price_returns_200(self, api_client):
        response = api_client.get("/settings/electricity-price")
        assert response.status_code == 200

    def test_get_price_returns_configured_value(self, api_client):
        response = api_client.get("/settings/electricity-price")
        data = response.json()
        # Default or configured value
        assert "price" in data
        assert isinstance(data["price"], (int, float))

    def test_set_price_returns_200(self, api_client):
        response = api_client.post("/settings/electricity-price", json={"price": 0.30})
        assert response.status_code == 200
