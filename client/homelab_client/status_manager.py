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
        self.scroll_offset = 0  # For paging support
        self.current_status = None  # Latest status data
        self.status_lock = threading.Lock()  # Protect status data

    def _handle_input(self, stop_event: threading.Event) -> str:
        """Non-blocking check for keyboard input

        Returns:
            Character pressed or empty string
        """
        # Check for keyboard input (Unix-like systems)
        if os.name != "nt":  # Unix/Linux/macOS
            if select.select([sys.stdin], [], [], 0)[0]:
                char = sys.stdin.read(1)
                # Handle arrow keys (ESC sequences)
                if char == "\x1b":  # ESC
                    next1 = sys.stdin.read(1)
                    if next1 == "[":
                        next2 = sys.stdin.read(1)
                        if next2 == "A":
                            return "up"
                        elif next2 == "B":
                            return "down"
                        elif next2 == "5":
                            sys.stdin.read(1)  # Read the ~
                            return "pageup"
                        elif next2 == "6":
                            sys.stdin.read(1)  # Read the ~
                            return "pagedown"
                return char
        else:  # Windows
            try:
                import msvcrt

                if msvcrt.kbhit():
                    char = msvcrt.getch()
                    # Handle special keys
                    if char == b"\xe0":  # Special key prefix
                        char = msvcrt.getch()
                        if char == b"H":
                            return "up"
                        elif char == b"P":
                            return "down"
                        elif char == b"I":
                            return "pageup"
                        elif char == b"Q":
                            return "pagedown"
                    else:
                        return char.decode("utf-8", errors="ignore")
            except ImportError:
                pass
        return ""

    def _wait_for_input(self, interval: float, stop_event: threading.Event) -> tuple:
        """Wait for interval or keyboard input

        Args:
            interval: Time to wait in seconds
            stop_event: Event to signal early exit

        Returns:
            Tuple of (should_continue: bool, immediate_refresh: bool)
        """
        start_time = time.time()

        while time.time() - start_time < interval:
            if stop_event.is_set():
                return (False, False)

            char = self._handle_input(stop_event)
            if char:
                if char.lower() == "q":
                    return (False, False)
                elif char in ["up", "pageup", "down", "pagedown", "j", "k"]:
                    # Scroll commands - trigger immediate refresh
                    return (True, True)

            time.sleep(0.05)  # Reduced from 0.1 for better responsiveness

        return (True, False)

    def _fetch_status_loop(
        self, interval: float, stop_event: threading.Event, error_callback
    ):
        """Background thread to fetch status data periodically

        Args:
            interval: Time between fetches in seconds
            stop_event: Event to signal thread should stop
            error_callback: Function to call on error
        """
        while not stop_event.is_set():
            try:
                response = requests.get(
                    f"{self.api.server_url}/status",
                    headers=self.api.headers,
                    timeout=30,
                )
                response.raise_for_status()
                status = response.json()

                # Update shared status data
                with self.status_lock:
                    self.current_status = status

            except requests.exceptions.RequestException as e:
                error_callback(e)
                return

            # Wait for interval, checking stop_event frequently
            for _ in range(int(interval * 10)):
                if stop_event.is_set():
                    return
                time.sleep(0.1)

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
        fetch_thread = None
        error_container = {"error": None}

        def error_callback(e):
            error_container["error"] = e

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
            # Show loading screen immediately in follow mode
            if follow_interval is not None:
                print("\033[2J\033[H\033[?25l", end="")  # Clear, move, hide cursor
                print("⏳ Loading homelab status...")
                sys.stdout.flush()

            # Initial fetch (synchronous for one-time mode, async for follow mode)
            if follow_interval is None:
                # One-time mode: fetch synchronously
                try:
                    response = requests.get(
                        f"{self.api.server_url}/status",
                        headers=self.api.headers,
                        timeout=30,
                    )
                    response.raise_for_status()
                    with self.status_lock:
                        self.current_status = response.json()
                except requests.exceptions.RequestException as e:
                    print(f"❌ Error: {e}")
                    sys.exit(1)
            else:
                # Follow mode: start background fetcher immediately
                fetch_thread = threading.Thread(
                    target=self._fetch_status_loop,
                    args=(follow_interval, stop_event, error_callback),
                    daemon=True,
                )
                fetch_thread.start()

                # Wait for first data with loading animation
                loading_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
                loading_idx = 0
                max_wait = 30  # Maximum 30 seconds for first fetch
                wait_start = time.time()

                while self.current_status is None:
                    # Check for errors
                    if error_container["error"]:
                        raise error_container["error"]

                    # Check timeout
                    if time.time() - wait_start > max_wait:
                        print("\033[?25h")  # Show cursor
                        print(f"\n❌ Error: Timeout waiting for initial data")
                        sys.exit(1)

                    # Animate loading
                    print(
                        f"\033[H\033[K{loading_chars[loading_idx]} Loading homelab status..."
                    )
                    sys.stdout.flush()
                    loading_idx = (loading_idx + 1) % len(loading_chars)
                    time.sleep(0.1)

            first_run = True

            while True:
                # Check for errors from fetch thread
                if error_container["error"]:
                    raise error_container["error"]

                # Get current status (thread-safe)
                with self.status_lock:
                    if self.current_status is None:
                        time.sleep(0.1)
                        continue
                    status = self.current_status

                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                current_lines = self.display.format_status_output(
                    status, timestamp, follow_interval, use_color
                )

                if follow_interval is not None:
                    # Get terminal size
                    height = os.get_terminal_size().lines

                    # Handle paging - check for scroll input
                    char = self._handle_input(stop_event)
                    if char == "up" or char == "k":
                        self.scroll_offset = max(0, self.scroll_offset - 1)
                    elif char == "down" or char == "j":
                        max_offset = max(0, len(current_lines) - height + 2)
                        self.scroll_offset = min(max_offset, self.scroll_offset + 1)
                    elif char == "pageup":
                        self.scroll_offset = max(0, self.scroll_offset - (height - 5))
                    elif char == "pagedown":
                        max_offset = max(0, len(current_lines) - height + 2)
                        self.scroll_offset = min(
                            max_offset, self.scroll_offset + (height - 5)
                        )
                    elif char.lower() == "q":
                        print("\033[?25h")  # Show cursor
                        print("\n\n✓ Status monitoring stopped\n")
                        break

                    # Apply paging - slice the lines to show
                    end_offset = min(
                        self.scroll_offset + height - 1, len(current_lines)
                    )
                    visible_lines = current_lines[self.scroll_offset : end_offset]

                    # Add scroll indicator if needed
                    if len(current_lines) > height - 1:
                        total_lines = len(current_lines)
                        viewing_line = f"[Lines {self.scroll_offset + 1}-{end_offset} of {total_lines}]"
                        if use_color:
                            viewing_line = f"\033[90m{viewing_line} ↑↓/j/k/PgUp/PgDn: scroll, q: quit\033[0m"
                        else:
                            viewing_line = (
                                f"{viewing_line} Up/Down/j/k/PgUp/PgDn: scroll, q: quit"
                            )

                        # Replace last line with scroll indicator
                        if visible_lines:
                            visible_lines[-1] = viewing_line
                        else:
                            visible_lines.append(viewing_line)

                    if first_run:
                        # First run: clear screen, hide cursor, and print
                        print(
                            "\033[2J\033[H\033[?25l", end=""
                        )  # Clear, move to top, hide cursor
                        for line in visible_lines:
                            print(line)
                    else:
                        # Subsequent runs: update in place
                        print("\033[H", end="")  # Move cursor to top-left

                        for i, line in enumerate(visible_lines):
                            if i >= len(prev_lines) or line != prev_lines[i]:
                                # Clear line and print new content
                                print(f"\033[K{line}")
                            else:
                                # Skip to next line without rewriting
                                print()

                        # Clear any extra lines from previous output
                        if len(prev_lines) > len(visible_lines):
                            for _ in range(len(prev_lines) - len(visible_lines)):
                                print("\033[K")

                    sys.stdout.flush()  # Force immediate display
                    prev_lines = visible_lines
                    first_run = False

                    # Short sleep for input responsiveness
                    time.sleep(0.05)
                else:
                    # One-time mode: print normally
                    for line in current_lines:
                        print(line)
                    print()
                    break

        except KeyboardInterrupt:
            print("\033[?25h")  # Show cursor
            print("\n\n✓ Status monitoring stopped\n")
        except requests.exceptions.RequestException as e:
            print("\033[?25h")  # Show cursor
            print(f"❌ Error: {e}")
            sys.exit(1)
        finally:
            # Show cursor
            if follow_interval is not None:
                print("\033[?25h", end="")
                sys.stdout.flush()

            # Stop background thread
            stop_event.set()
            if fetch_thread and fetch_thread.is_alive():
                fetch_thread.join(timeout=2)

            # Restore terminal settings
            if old_settings is not None and os.name != "nt":
                try:
                    import termios

                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                except (ImportError, OSError):
                    pass
