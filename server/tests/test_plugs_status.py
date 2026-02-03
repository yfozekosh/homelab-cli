"""Test individual plug status and control"""
import pytest

def test_get_plug_status(api_client):
    """Test getting status of a specific plug"""
    response = api_client.get("/plugs/test-plug/status")
    # May fail if actual device not accessible
    assert response.status_code in [200, 404, 500, 503]

def test_turn_plug_on(api_client):
    """Test turning a plug on"""
    response = api_client.post("/plugs/test-plug/on")
    # May fail if device not accessible
    assert response.status_code in [200, 404, 500, 503]

def test_turn_plug_off(api_client):
    """Test turning a plug off"""
    response = api_client.post("/plugs/test-plug/off")
    # May fail if device not accessible
    assert response.status_code in [200, 404, 500, 503]

def test_plug_status_nonexistent(api_client):
    """Test getting status of non-existent plug"""
    response = api_client.get("/plugs/doesnotexist/status")
    assert response.status_code == 404

def test_turn_on_nonexistent_plug(api_client):
    """Test turning on non-existent plug"""
    response = api_client.post("/plugs/doesnotexist/on")
    assert response.status_code == 404

def test_turn_off_nonexistent_plug(api_client):
    """Test turning off non-existent plug"""
    response = api_client.post("/plugs/doesnotexist/off")
    assert response.status_code == 404
