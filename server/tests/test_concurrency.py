"""Test concurrent requests"""
import pytest
import concurrent.futures

class TestConcurrency:
    def test_multiple_simultaneous_health_checks(self, api_client):
        def make_request():
            return api_client.get("/health").status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert all(status == 200 for status in results)
        assert len(results) == 20
