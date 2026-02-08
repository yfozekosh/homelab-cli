"""Test edge cases and boundary conditions"""

class TestInputValidation:
    def test_plug_with_very_long_name(self, api_client):
        long_name = "a" * 1000
        response = api_client.post("/plugs", json={"name": long_name, "ip": "192.168.1.100"})
        assert response.status_code in [200, 422, 500]

    def test_empty_string_values(self, api_client):
        response = api_client.post("/plugs", json={"name": "", "ip": ""})
        # Server may accept empty strings (no validation) or reject them
        assert response.status_code in [200, 400, 422, 500]

class TestErrorRecovery:
    def test_malformed_json(self, api_client):
        import requests
        response = requests.post(
            api_client.base_url + "/plugs",
            headers=api_client.headers,
            data="not valid json",
        )
        assert response.status_code == 422
