"""Test plug management endpoints"""

class TestListPlugs:
    def test_list_plugs_returns_200(self, api_client):
        response = api_client.get("/plugs")
        assert response.status_code == 200

    def test_list_plugs_contains_test_data(self, api_client):
        response = api_client.get("/plugs")
        data = response.json()
        assert "test-plug" in data["plugs"]

class TestAddPlug:
    def test_add_plug_returns_200(self, api_client):
        response = api_client.post("/plugs", json={"name": "new-plug", "ip": "192.168.1.200"})
        assert response.status_code == 200

    def test_add_plug_appears_in_list(self, api_client):
        api_client.post("/plugs", json={"name": "added-plug", "ip": "192.168.1.201"})
        response = api_client.get("/plugs")
        assert "added-plug" in response.json()["plugs"]

class TestEditPlug:
    def test_edit_plug_returns_200(self, api_client):
        response = api_client.put("/plugs", json={"name": "test-plug", "ip": "192.168.1.150"})
        assert response.status_code == 200

class TestRemovePlug:
    def test_remove_plug_returns_200(self, api_client):
        api_client.post("/plugs", json={"name": "removable", "ip": "192.168.1.220"})
        response = api_client.delete("/plugs", json={"name": "removable"})
        assert response.status_code == 200
