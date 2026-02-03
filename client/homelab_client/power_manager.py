"""Power control operations"""

import sys
import time
from .api_client import APIClient


class PowerManager:
    """Manages server power operations"""

    def __init__(self, api_client: APIClient):
        self.api = api_client

    def _show_progress(self, name: str, action: str):
        """Show progress animation while operation completes"""
        import threading

        stop_event = threading.Event()
        spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

        def spinner():
            idx = 0
            while not stop_event.is_set():
                print(
                    f"\r{spinner_chars[idx]} {action} server '{name}'... ",
                    end="",
                    flush=True,
                )
                idx = (idx + 1) % len(spinner_chars)
                time.sleep(0.1)

        spinner_thread = threading.Thread(target=spinner, daemon=True)
        spinner_thread.start()
        return stop_event

    def power_on(self, name: str):
        """Power on a server"""
        print(f"⚡ Powering on server '{name}'...")
        print()

        stop_event = self._show_progress(name, "Powering on")

        try:
            result = self.api._post("/power/on", {"name": name}, timeout=180)
        finally:
            stop_event.set()
            time.sleep(0.15)  # Let spinner thread finish
            print("\r" + " " * 80 + "\r", end="")  # Clear spinner line

        if result.get("success"):
            print(f"✓ Server '{name}' powered on successfully\n")
            if result.get("logs"):
                print("Progress Log:")
                print("─" * 60)
                for log in result["logs"]:
                    print(f"  {log}")
                print()
        else:
            print(f"❌ Failed: {result.get('message')}")
            if result.get("logs"):
                print("\nLogs:")
                for log in result["logs"]:
                    print(f"  {log}")
            sys.exit(1)

    def power_off(self, name: str):
        """Power off a server"""
        print(f"🔴 Powering off server '{name}'...")
        print()

        stop_event = self._show_progress(name, "Powering off")

        try:
            result = self.api._post("/power/off", {"name": name}, timeout=180)
        finally:
            stop_event.set()
            time.sleep(0.15)  # Let spinner thread finish
            print("\r" + " " * 80 + "\r", end="")  # Clear spinner line

        if result.get("success"):
            print(f"✓ Server '{name}' powered off successfully\n")
            if result.get("logs"):
                print("Progress Log:")
                print("─" * 60)
                for log in result["logs"]:
                    print(f"  {log}")
                print()
        else:
            print(f"⚠️  {result.get('message')}")
            if result.get("logs"):
                print("\nLogs:")
                for log in result["logs"]:
                    print(f"  {log}")
