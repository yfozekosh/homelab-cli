"""Status monitoring operations"""

import sys
import os
import time
import select
import threading
from typing import Optional
import requests
from status_display import StatusDisplay
from .api_client import APIClient


class StatusManager:
    """Manages status monitoring and display"""

    def __init__(self, api_client: APIClient):
        self.api = api_client
        self.display = StatusDisplay()

    def _wait_for_input(self, interval: float, stop_event: threading.Event) -> bool:
        """Wait for interval or keyboard input

        Args:
            interval: Time to wait in seconds
            stop_event: Event to signal early exit

        Returns:
            True if should continue, False if should exit
        """
        start_time = time.time()

        while time.time() - start_time < interval:
            if stop_event.is_set():
                return False

            # Check for keyboard input (Unix-like systems)
            if os.name != "nt":  # Unix/Linux/macOS
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    char = sys.stdin.read(1)
                    if char.lower() == "q":
                        return False
            else:  # Windows
                # On Windows, use msvcrt if available
                try:
                    import msvcrt

                    if msvcrt.kbhit():
                        char = msvcrt.getch().decode("utf-8", errors="ignore")
                        if char.lower() == "q":
                            return False
                except ImportError:
                    pass

            time.sleep(0.1)

        return True

    def get_status(
        self, follow_interval: Optional[float] = None, use_color: bool = True
    ):
        """Get comprehensive status of all servers and plugs

        Args:
            follow_interval: If provided, continuously update at this interval (in seconds)
            use_color: Whether to use colored output (default: True)
        """
        prev_lines = []
        stop_event = threading.Event()

        # Set terminal to raw mode for non-blocking input (Unix only)
        old_settings = None
        if follow_interval is not None and os.name != "nt":
            try:
                import tty
                import termios

                old_settings = termios.tcgetattr(sys.stdin)
                tty.setcbreak(sys.stdin.fileno())
            except (ImportError, OSError):
                pass

        try:
            first_run = True
            while True:
                response = requests.get(
                    f"{self.api.server_url}/status",
                    headers=self.api.headers,
                    timeout=30,
                )
                response.raise_for_status()
                status = response.json()

                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                current_lines = self.display.format_status_output(
                    status, timestamp, follow_interval, use_color
                )

                if follow_interval is not None:
                    if first_run:
                        # First run: clear screen and print
                        print("\033[2J\033[H", end="")  # Clear screen and move to top
                        for line in current_lines:
                            print(line)
                    else:
                        # Subsequent runs: update in place
                        # ANSI codes: \033[H moves to home, \033[K clears to end of line
                        print("\033[H", end="")  # Move cursor to top-left

                        for i, line in enumerate(current_lines):
                            if i >= len(prev_lines) or line != prev_lines[i]:
                                # Clear line and print new content
                                print(f"\033[K{line}")
                            else:
                                # Skip to next line without rewriting
                                print()

                        # Clear any extra lines from previous output
                        if len(prev_lines) > len(current_lines):
                            for _ in range(len(prev_lines) - len(current_lines)):
                                print("\033[K")
                else:
                    # One-time mode: print normally
                    for line in current_lines:
                        print(line)
                    print()
                    break

                prev_lines = current_lines
                first_run = False

                if follow_interval is not None:
                    # Wait for interval or keyboard input
                    if not self._wait_for_input(follow_interval, stop_event):
                        print("\n\n✓ Status monitoring stopped\n")
                        break

        except KeyboardInterrupt:
            print("\n\n✓ Status monitoring stopped\n")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error: {e}")
            sys.exit(1)
        finally:
            # Restore terminal settings
            if old_settings is not None and os.name != "nt":
                try:
                    import termios

                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                except (ImportError, OSError):
                    pass
