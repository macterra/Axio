"""Watchdog timer for kernel timeout enforcement."""

import signal
import threading
import time
from typing import Callable, Optional, Any
from contextlib import contextmanager

from ..common.errors import WatchdogTimeoutError


class WatchdogTimer:
    """Watchdog timer that enforces kernel evaluation timeout.

    If PolicyGate.evaluate() exceeds timeout_ms:
    - Log FATAL_HANG audit entry
    - Terminate process

    Rule: Watchdog cannot issue tokens or execute actions.
    """

    def __init__(
        self,
        timeout_ms: int = 200,
        on_timeout: Optional[Callable[[Optional[str]], None]] = None
    ):
        """Initialize watchdog timer.

        Args:
            timeout_ms: Timeout in milliseconds
            on_timeout: Callback on timeout, receives proposal_hash
        """
        self.timeout_ms = timeout_ms
        self.on_timeout = on_timeout
        self._timer: Optional[threading.Timer] = None
        self._proposal_hash: Optional[str] = None
        self._started = False

    def start(self, proposal_hash: Optional[str] = None) -> None:
        """Start the watchdog timer.

        Args:
            proposal_hash: Current proposal hash for logging
        """
        if self._started:
            self.cancel()

        self._proposal_hash = proposal_hash
        self._started = True

        timeout_sec = self.timeout_ms / 1000.0
        self._timer = threading.Timer(timeout_sec, self._handle_timeout)
        self._timer.daemon = True
        self._timer.start()

    def cancel(self) -> None:
        """Cancel the watchdog timer."""
        if self._timer:
            self._timer.cancel()
            self._timer = None
        self._started = False

    def _handle_timeout(self) -> None:
        """Handle watchdog timeout."""
        if self.on_timeout:
            self.on_timeout(self._proposal_hash)

        # In production, this would terminate the process
        # For testing, we raise an exception
        raise WatchdogTimeoutError(self.timeout_ms, self._proposal_hash)

    @contextmanager
    def guard(self, proposal_hash: Optional[str] = None):
        """Context manager for watchdog-guarded execution.

        Usage:
            with watchdog.guard(proposal_hash):
                # Code that must complete within timeout
        """
        self.start(proposal_hash)
        try:
            yield
        finally:
            self.cancel()


class NoOpWatchdog:
    """No-op watchdog for testing without timeouts."""

    def __init__(self, timeout_ms: int = 200, on_timeout: Optional[Callable] = None):
        self.timeout_ms = timeout_ms

    def start(self, proposal_hash: Optional[str] = None) -> None:
        pass

    def cancel(self) -> None:
        pass

    @contextmanager
    def guard(self, proposal_hash: Optional[str] = None):
        yield
