"""Shared cooperative-cancellation helpers for file conversions."""

from __future__ import annotations

from typing import Callable


class ConversionCancelled(Exception):
    """Raised when a user cancels an in-progress file conversion."""


def raise_if_cancelled(cancelled: Callable[[], bool] | None) -> None:
    """Stop conversion at a safe boundary when cancellation was requested."""
    if cancelled and cancelled():
        raise ConversionCancelled("Conversion cancelled by user.")
