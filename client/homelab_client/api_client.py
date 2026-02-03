"""Base API client for Homelab server communication"""

from typing import Optional, Dict, Any
import requests

from .exceptions import APIError, ConnectionError


def _get_status_code(e: requests.exceptions.HTTPError) -> Optional[int]:
    """Extract status code from HTTPError safely"""
    if e.response is not None:
        return int(e.response.status_code)
    return None


class APIClient:
    """Base HTTP client for API communication"""

    def __init__(self, server_url: str, api_key: str):
        self.server_url = server_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"X-API-Key": self.api_key}

    def health_check(self) -> bool:
        """Check server health"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def _get(self, endpoint: str, timeout: int = 10) -> Dict[str, Any]:
        """Make GET request to API"""
        try:
            response = requests.get(
                f"{self.server_url}{endpoint}", headers=self.headers, timeout=timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Cannot connect to server: {e}")
        except requests.exceptions.Timeout as e:
            raise APIError(f"Request timed out: {e}")
        except requests.exceptions.HTTPError as e:
            raise APIError(str(e), status_code=_get_status_code(e))
        except requests.exceptions.RequestException as e:
            raise APIError(f"API request failed: {e}")

    def _post(
        self, endpoint: str, data: Dict[str, Any], timeout: int = 30
    ) -> Dict[str, Any]:
        """Make POST request to API"""
        try:
            response = requests.post(
                f"{self.server_url}{endpoint}",
                headers=self.headers,
                json=data,
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Cannot connect to server: {e}")
        except requests.exceptions.Timeout as e:
            raise APIError(f"Request timed out: {e}")
        except requests.exceptions.HTTPError as e:
            raise APIError(str(e), status_code=_get_status_code(e))
        except requests.exceptions.RequestException as e:
            raise APIError(f"API request failed: {e}")

    def _put(
        self, endpoint: str, data: Dict[str, Any], timeout: int = 30
    ) -> Dict[str, Any]:
        """Make PUT request to API"""
        try:
            response = requests.put(
                f"{self.server_url}{endpoint}",
                headers=self.headers,
                json=data,
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Cannot connect to server: {e}")
        except requests.exceptions.Timeout as e:
            raise APIError(f"Request timed out: {e}")
        except requests.exceptions.HTTPError as e:
            raise APIError(str(e), status_code=_get_status_code(e))
        except requests.exceptions.RequestException as e:
            raise APIError(f"API request failed: {e}")

    def _delete(
        self, endpoint: str, data: Optional[Dict[str, Any]] = None, timeout: int = 10
    ) -> Dict[str, Any]:
        """Make DELETE request to API"""
        try:
            kwargs: Dict[str, Any] = {"headers": self.headers, "timeout": timeout}
            if data:
                kwargs["json"] = data

            response = requests.delete(f"{self.server_url}{endpoint}", **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Cannot connect to server: {e}")
        except requests.exceptions.Timeout as e:
            raise APIError(f"Request timed out: {e}")
        except requests.exceptions.HTTPError as e:
            raise APIError(str(e), status_code=_get_status_code(e))
        except requests.exceptions.RequestException as e:
            raise APIError(f"API request failed: {e}")
