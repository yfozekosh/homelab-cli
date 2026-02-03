"""Test power operation endpoints"""
import pytest

class TestPowerOperations:
    def test_power_on_nonexistent_server_returns_404(self, api_client):
        response = api_client.post("/power/on", json={"name": "nonexistent"})
        assert response.status_code == 404

    def test_power_off_nonexistent_server_returns_404(self, api_client):
        response = api_client.post("/power/off", json={"name": "nonexistent"})
        assert response.status_code == 404

    def test_power_on_returns_streaming(self, api_client):
        response = api_client.post("/power/on", json={"name": "test-server"}, stream=True, timeout=5)
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
