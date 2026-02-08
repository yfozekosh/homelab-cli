"""Test server management endpoints"""

class TestListServers:
    def test_list_servers_returns_200(self, api_client):
        response = api_client.get("/servers")
        assert response.status_code == 200

    def test_list_servers_contains_test_data(self, api_client):
        response = api_client.get("/servers")
        data = response.json()
        assert "test-server" in data["servers"]

class TestSSHHealthCheck:
    def test_ssh_healthcheck_returns_200(self, api_client):
        response = api_client.get("/ssh-healthcheck")
        assert response.status_code == 200

    def test_ssh_healthcheck_returns_results(self, api_client):
        response = api_client.get("/ssh-healthcheck")
        data = response.json()
        assert "results" in data
        assert isinstance(data["results"], list)
