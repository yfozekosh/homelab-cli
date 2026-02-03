"""Test API error handling"""
import pytest

def test_invalid_json_body(api_client):
    import requests
    response = requests.post(
        "http://127.0.0.1:18000/plugs",
        data="not-json",
        headers={"X-API-Key": "test-api-key", "Content-Type": "application/json"}
    )
    assert response.status_code in [400, 422]

def test_missing_content_type(api_client):
    import requests
    response = requests.post(
        "http://127.0.0.1:18000/plugs",
        data='{"name": "test", "ip": "192.168.1.1"}',
        headers={"X-API-Key": "test-api-key"}
    )
    # Should still work or return specific error
    assert response.status_code in [200, 400, 415, 422]

def test_extra_fields_in_request(api_client):
    response = api_client.post("/plugs", json={
        "name": "extra-fields",
        "ip": "192.168.1.96",
        "extra_field": "should-be-ignored",
        "another_extra": 123
    })
    # Pydantic may ignore or reject
    assert response.status_code in [200, 400, 422]

def test_null_values_in_request(api_client):
    response = api_client.post("/plugs", json={
        "name": None,
        "ip": "192.168.1.97"
    })
    assert response.status_code in [400, 422]

def test_wrong_type_in_request(api_client):
    response = api_client.post("/plugs", json={
        "name": 12345,  # Should be string
        "ip": "192.168.1.98"
    })
    assert response.status_code in [200, 400, 422]

def test_array_instead_of_object(api_client):
    import requests
    response = requests.post(
        "http://127.0.0.1:18000/plugs",
        json=[{"name": "test", "ip": "192.168.1.1"}],
        headers={"X-API-Key": "test-api-key"}
    )
    assert response.status_code in [400, 422]

def test_empty_request_body(api_client):
    import requests
    response = requests.post(
        "http://127.0.0.1:18000/plugs",
        data="",
        headers={"X-API-Key": "test-api-key", "Content-Type": "application/json"}
    )
    assert response.status_code in [400, 422]

def test_very_large_request_body(api_client):
    large_name = "a" * 1000000  # 1MB
    response = api_client.post("/plugs", json={
        "name": large_name,
        "ip": "192.168.1.99"
    })
    # Should either accept or reject
    assert response.status_code in [200, 400, 413, 422]
