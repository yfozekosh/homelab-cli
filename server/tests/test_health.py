"""Test basic server functionality and health endpoints"""
import pytest


class TestHealth:
    def test_health_endpoint_returns_200(self, api_client):
        response = api_client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_structure(self, api_client):
        response = api_client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "version" in data

    def test_health_no_auth_required(self, unauthenticated_client):
        response = unauthenticated_client.get("/health")
        assert response.status_code == 200


class TestAuthentication:
    def test_missing_api_key_returns_403(self, unauthenticated_client):
        response = unauthenticated_client.get("/plugs")
        assert response.status_code == 403

    def test_wrong_api_key_returns_401(self, server_process):
        import requests
        response = requests.get(f"{server_process}/plugs", headers={"X-API-Key": "wrong-key"})
        assert response.status_code == 401

    def test_valid_api_key_works(self, api_client):
        response = api_client.get("/plugs")
        assert response.status_code == 200


class TestErrorHandling:
    def test_404_for_unknown_endpoint(self, api_client):
        response = api_client.get("/nonexistent")
        assert response.status_code == 404

    def test_405_for_wrong_method(self, api_client):
        response = api_client.post("/health")
        assert response.status_code == 405

    def test_error_response_has_detail(self, api_client):
        response = api_client.get("/nonexistent")
        data = response.json()
        assert "detail" in data
