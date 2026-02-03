"""Power control operations"""

import sys
import json
import requests
from .api_client import APIClient
from .exceptions import APIError, ConnectionError
from .constants import POWER_OPERATION_TIMEOUT


class PowerManager:
    """Manages server power operations"""

    def __init__(self, api_client: APIClient):
        self.api = api_client

    def _stream_power_operation(self, endpoint: str, data: dict, action_verb: str):
        """Stream power operation with real-time logs
        
        Raises:
            APIError: If the operation fails
            ConnectionError: If cannot connect to server
        """
        url = f"{self.api.server_url}{endpoint}"

        try:
            response = requests.post(
                url,
                headers=self.api.headers,
                json=data,
                stream=True,
                timeout=POWER_OPERATION_TIMEOUT,
            )

            # Check for HTTP errors
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("detail", f"HTTP {response.status_code}")
                except:
                    error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                raise APIError(error_msg, status_code=response.status_code)

            print()  # Empty line before logs

            final_result = None
            current_event = None

            # Process SSE stream
            for line in response.iter_lines():
                if not line:
                    continue

                line = line.decode("utf-8")

                # Skip keepalive comments
                if line.startswith(":"):
                    continue

                # Parse SSE format
                if line.startswith("event:"):
                    current_event = line.split(":", 1)[1].strip()
                elif line.startswith("data:"):
                    data_str = line.split(":", 1)[1].strip()

                    try:
                        # Try to parse as JSON
                        if data_str.startswith("{"):
                            data_obj = json.loads(data_str)

                            # Check if it's a log message
                            if isinstance(data_obj, dict) and "message" in data_obj:
                                # If there's both 'success' and 'message', it's the final result
                                if "success" in data_obj:
                                    final_result = data_obj
                                else:
                                    # It's a log message
                                    print(f"  {data_obj['message']}")
                                    sys.stdout.flush()
                            else:
                                # It's the final result
                                final_result = data_obj
                        else:
                            # Plain text log
                            print(f"  {data_str}")
                            sys.stdout.flush()

                    except json.JSONDecodeError:
                        # Plain text
                        print(f"  {data_str}")
                        sys.stdout.flush()

            print()  # Empty line after logs

            return final_result

        except requests.exceptions.Timeout:
            raise APIError(f"Request timed out after {POWER_OPERATION_TIMEOUT} seconds")
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(f"Cannot connect to server: {e}")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {e}")

    def power_on(self, name: str) -> bool:
        """Power on a server with real-time progress
        
        Returns:
            bool: True if successful
            
        Raises:
            APIError: If the operation fails
        """
        print(f"⚡ Powering on server '{name}'...")

        result = self._stream_power_operation(
            "/power/on", {"name": name}, "Powering on"
        )

        if result and result.get("success"):
            print(f"✓ Server '{name}' powered on successfully")
            return True
        else:
            message = result.get("message") if result else "Unknown error"
            raise APIError(f"Failed to power on: {message}")

    def power_off(self, name: str) -> bool:
        """Power off a server with real-time progress
        
        Returns:
            bool: True if successful
        """
        print(f"🔴 Powering off server '{name}'...")

        result = self._stream_power_operation(
            "/power/off", {"name": name}, "Powering off"
        )

        if result and result.get("success"):
            print(f"✓ Server '{name}' powered off successfully")
            return True
        else:
            message = result.get("message") if result else "Unknown error"
            print(f"⚠️  {message}")
            return False
