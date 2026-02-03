"""Test status endpoint"""
import pytest

class TestStatus:
    def test_status_returns_200(self, api_client):
        response = api_client.get("/status")
        assert response.status_code == 200

    def test_status_has_servers_section(self, api_client):
        response = api_client.get("/status")
        data = response.json()
        assert "servers" in data

    def test_status_has_plugs_section(self, api_client):
        response = api_client.get("/status")
        data = response.json()
        assert "plugs" in data
