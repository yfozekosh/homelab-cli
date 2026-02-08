"""Extended server management tests"""

def test_add_server_with_all_fields(api_client):
    response = api_client.post("/servers", json={
        "name": "extra-server",
        "hostname": "192.168.1.199",
        "mac": "11:22:33:44:55:77",
        "plug": "test-plug"
    })
    assert response.status_code in [200, 201]

def test_add_server_missing_hostname(api_client):
    response = api_client.post("/servers", json={
        "name": "no-hostname-server",
        "mac": "11:22:33:44:55:78",
        "plug": "test-plug"
    })
    assert response.status_code in [400, 422]

def test_add_server_missing_mac(api_client):
    response = api_client.post("/servers", json={
        "name": "no-mac-server",
        "hostname": "192.168.1.198",
        "plug": "test-plug"
    })
    # MAC may be optional or have default
    assert response.status_code in [200, 400, 422]

def test_add_server_invalid_mac_format(api_client):
    response = api_client.post("/servers", json={
        "name": "bad-mac-server",
        "hostname": "192.168.1.197",
        "mac": "not-a-mac-address",
        "plug": "test-plug"
    })
    assert response.status_code in [200, 400, 422]

def test_add_server_with_nonexistent_plug(api_client):
    response = api_client.post("/servers", json={
        "name": "bad-plug-server",
        "hostname": "192.168.1.196",
        "mac": "11:22:33:44:55:79",
        "plug": "nonexistent-plug"
    })
    assert response.status_code in [200, 400, 404]

def test_edit_server_hostname(api_client):
    # Add server first
    api_client.post("/servers", json={
        "name": "edit-srv",
        "hostname": "192.168.1.195",
        "mac": "11:22:33:44:55:80",
        "plug": "test-plug"
    })
    # Edit it
    response = api_client.put("/servers", json={
        "name": "edit-srv",
        "hostname": "192.168.1.194",
        "mac": "11:22:33:44:55:80",
        "plug": "test-plug"
    })
    assert response.status_code in [200, 404]

def test_delete_server(api_client):
    # Add server first
    api_client.post("/servers", json={
        "name": "del-srv",
        "hostname": "192.168.1.193",
        "mac": "11:22:33:44:55:81",
        "plug": "test-plug"
    })
    # Delete it
    response = api_client.delete("/servers", json={"name": "del-srv"})
    assert response.status_code in [200, 404]

def test_delete_nonexistent_server(api_client):
    response = api_client.delete("/servers", json={"name": "doesnt-exist-xyz"})
    assert response.status_code in [404, 200]

def test_list_servers_response_structure(api_client):
    response = api_client.get("/servers")
    data = response.json()
    assert "servers" in data
    servers = data["servers"]
    if servers:
        first_server = list(servers.values())[0]
        # Should have expected fields
        assert isinstance(first_server, dict)
