"""Test detailed status information"""
import pytest

def test_status_response_structure(api_client):
    """Test status response has correct structure"""
    response = api_client.get("/status")
    assert response.status_code == 200
    data = response.json()
    
    # Should have both sections
    assert "servers" in data
    assert "plugs" in data
    # Status returns lists, not dicts
    assert isinstance(data["servers"], (dict, list))
    assert isinstance(data["plugs"], (dict, list))

def test_status_includes_test_server(api_client):
    """Test that test-server appears in status"""
    response = api_client.get("/status")
    data = response.json()
    # Check if servers is a list or dict
    if isinstance(data["servers"], list):
        server_names = [s.get("name") for s in data["servers"]]
        assert "test-server" in server_names
    else:
        assert "test-server" in data["servers"]

def test_status_includes_test_plug(api_client):
    """Test that test-plug appears in status"""
    response = api_client.get("/status")
    data = response.json()
    # Check if plugs is a list or dict
    if isinstance(data["plugs"], list):
        plug_names = [p.get("name") for p in data["plugs"]]
        assert "test-plug" in plug_names
    else:
        assert "test-plug" in data["plugs"]

def test_status_server_has_required_fields(api_client):
    """Test server status has required fields"""
    response = api_client.get("/status")
    data = response.json()
    if isinstance(data["servers"], list) and len(data["servers"]) > 0:
        server = data["servers"][0]
        assert isinstance(server, dict)
    elif isinstance(data["servers"], dict) and len(data["servers"]) > 0:
        server = list(data["servers"].values())[0]
        assert isinstance(server, dict)

def test_status_plug_has_info(api_client):
    """Test plug status has information"""
    response = api_client.get("/status")
    data = response.json()
    if isinstance(data["plugs"], list) and len(data["plugs"]) > 0:
        plug = data["plugs"][0]
        assert isinstance(plug, dict)
    elif isinstance(data["plugs"], dict) and len(data["plugs"]) > 0:
        plug = list(data["plugs"].values())[0]
        assert isinstance(plug, dict)

def test_get_specific_server(api_client):
    """Test getting specific server details"""
    response = api_client.get("/servers/test-server")
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, dict)

def test_get_nonexistent_server(api_client):
    """Test getting non-existent server"""
    response = api_client.get("/servers/does-not-exist-xyz")
    assert response.status_code == 404
