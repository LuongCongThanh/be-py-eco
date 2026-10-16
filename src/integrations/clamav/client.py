"""ClamAV adapter — guild.md §15 Slice 2, commit 10. Thin wrapper over
`clamd`'s TCP protocol so `modules.media.tasks` doesn't import a
third-party client directly (matches the adapter-selected-via-config
convention already used by `integrations/google_oauth`, guild.md §7.6).
"""

from __future__ import annotations

import clamd
import environ

env = environ.Env()


class InfectedFileError(Exception):
    """Raised when ClamAV flags a scanned object as infected."""

    def __init__(self, signature: str) -> None:
        self.signature = signature
        super().__init__(f"file is infected: {signature}")


def _client() -> clamd.ClamdNetworkSocket:
    return clamd.ClamdNetworkSocket(
        host=env("CLAMAV_HOST", default="localhost"),
        port=env.int("CLAMAV_PORT", default=3310),
    )


def scan_bytes(data: bytes) -> None:
    """Raise `InfectedFileError` if `data` is flagged; return silently
    (including on a clean result) otherwise."""
    result = _client().instream(data)
    status, signature = result["stream"]
    if status == "FOUND":
        raise InfectedFileError(signature or "unknown")
