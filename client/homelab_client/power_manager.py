"""Power control operations"""

import sys
import json
import requests
from .api_client import APIClient


class PowerManager:
    """Manages server power operations"""

    def __init__(self, api_client: APIClient):
        self.api = api_client

    def _stream_power_operation(self, endpoint: str, data: dict, action_verb: str):
        """Stream power operation with real-time logs"""
        url = f"{self.api.server_url}{endpoint}"

        try:
            response = requests.post(
                url,
                headers=self.api.headers,
                json=data,
                stream=True,
                timeout=180,
            )
            response.raise_for_status()

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

        except requests.exceptions.RequestException as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)

    def power_on(self, name: str):
        """Power on a server with real-time progress"""
        print(f"⚡ Powering on server '{name}'...")

        result = self._stream_power_operation(
            "/power/on", {"name": name}, "Powering on"
        )

        if result and result.get("success"):
            print(f"✓ Server '{name}' powered on successfully")
        else:
            message = result.get("message") if result else "Unknown error"
            print(f"❌ Failed: {message}")
            sys.exit(1)

    def power_off(self, name: str):
        """Power off a server with real-time progress"""
        print(f"🔴 Powering off server '{name}'...")

        result = self._stream_power_operation(
            "/power/off", {"name": name}, "Powering off"
        )

        if result and result.get("success"):
            print(f"✓ Server '{name}' powered off successfully")
        else:
            message = result.get("message") if result else "Unknown error"
            print(f"⚠️  {message}")
