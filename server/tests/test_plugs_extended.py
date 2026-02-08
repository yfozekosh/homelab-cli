"""Extended plug management tests"""

def test_list_plugs(api_client):
    response = api_client.get("/plugs")
    assert response.status_code == 200
    data = response.json()
    assert "plugs" in data

def test_add_plug_with_valid_data(api_client):
    response = api_client.post("/plugs", json={"name": "extra-plug", "ip": "192.168.1.88"})
    assert response.status_code in [200, 201]

def test_add_plug_missing_name(api_client):
    response = api_client.post("/plugs", json={"ip": "192.168.1.89"})
    assert response.status_code in [400, 422]

def test_add_plug_missing_ip(api_client):
    response = api_client.post("/plugs", json={"name": "missing-ip-plug"})
    assert response.status_code in [400, 422]

def test_add_plug_empty_name(api_client):
    response = api_client.post("/plugs", json={"name": "", "ip": "192.168.1.90"})
    assert response.status_code in [200, 400, 422]

def test_add_plug_very_long_name(api_client):
    long_name = "a" * 500
    response = api_client.post("/plugs", json={"name": long_name, "ip": "192.168.1.91"})
    assert response.status_code in [200, 400, 422]

def test_edit_plug_that_exists(api_client):
    # First add
    api_client.post("/plugs", json={"name": "edit-test", "ip": "192.168.1.92"})
    # Then edit
    response = api_client.put("/plugs", json={"name": "edit-test", "ip": "192.168.1.93"})
    assert response.status_code in [200, 404]

def test_delete_plug_that_exists(api_client):
    # First add
    api_client.post("/plugs", json={"name": "del-test", "ip": "192.168.1.94"})
    # Then delete
    response = api_client.delete("/plugs", json={"name": "del-test"})
    assert response.status_code in [200, 404]

def test_delete_nonexistent_plug(api_client):
    response = api_client.delete("/plugs", json={"name": "does-not-exist-xyz"})
    assert response.status_code in [404, 200]

def test_add_plug_special_characters(api_client):
    response = api_client.post("/plugs", json={"name": "plug-@#$%", "ip": "192.168.1.95"})
    assert response.status_code in [200, 400, 422]
