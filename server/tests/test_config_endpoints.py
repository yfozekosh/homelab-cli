"""Test configuration management endpoints"""

def test_set_price_and_verify(api_client):
    """Test setting price and verifying it changed"""
    # Set a new price
    response = api_client.post("/settings/electricity-price", json={"price": 0.42})
    assert response.status_code == 200
    
    # Verify it was set
    response = api_client.get("/settings/electricity-price")
    assert response.status_code == 200
    assert response.json()["price"] == 0.42

def test_set_price_zero(api_client):
    """Test setting price to zero"""
    response = api_client.post("/settings/electricity-price", json={"price": 0.0})
    assert response.status_code in [200, 400]

def test_set_price_very_high(api_client):
    """Test setting very high price is rejected by validation"""
    response = api_client.post("/settings/electricity-price", json={"price": 999.99})
    assert response.status_code == 422  # Validation error

def test_set_price_with_many_decimals(api_client):
    """Test setting price with many decimal places"""
    response = api_client.post("/settings/electricity-price", json={"price": 0.123456789})
    assert response.status_code == 200

def test_electricity_price_requires_auth(unauthenticated_client):
    """Test that electricity price endpoints require auth"""
    response = unauthenticated_client.get("/settings/electricity-price")
    assert response.status_code in [401, 403]
    
    response = unauthenticated_client.post("/settings/electricity-price", json={"price": 0.5})
    assert response.status_code in [401, 403]
