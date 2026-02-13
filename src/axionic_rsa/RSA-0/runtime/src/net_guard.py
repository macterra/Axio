"""
RSA-0 X-0E — Net Guard (Defense-in-Depth)

Best-effort Python-level network disable.
Monkeypatches socket to raise on any connection attempt.
Treat as defense-in-depth, not determinism enforcement.
"""

from __future__ import annotations

import socket as _socket

_original_connect = _socket.socket.connect
_guard_active = False


class NetworkDisabledError(RuntimeError):
    """Raised when a socket operation is attempted while net guard is active."""
    pass


def _blocked_connect(self, *args, **kwargs):
    raise NetworkDisabledError(
        "Network access is disabled in X-0E mode. "
        "No socket connections permitted during run or replay."
    )


def enable_net_guard() -> None:
    """Monkeypatch socket.connect to prevent any network I/O."""
    global _guard_active
    if not _guard_active:
        _socket.socket.connect = _blocked_connect  # type: ignore[assignment]
        _guard_active = True


def disable_net_guard() -> None:
    """Restore original socket.connect (for testing only)."""
    global _guard_active
    if _guard_active:
        _socket.socket.connect = _original_connect  # type: ignore[assignment]
        _guard_active = False


def is_net_guard_active() -> bool:
    return _guard_active
