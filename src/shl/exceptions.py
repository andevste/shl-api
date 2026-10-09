"""Exceptions for the SHL API client."""

from __future__ import annotations

from typing import Optional


class SHLError(Exception):
    """Base exception for all SHL API client errors."""


class SHLAPIError(SHLError):
    """Raised when the SHL API returns an error response."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_text: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class SHLNotFoundError(SHLAPIError):
    """Raised when an SHL resource (game, team, etc.) is not found."""


class SHLConnectionError(SHLError):
    """Raised when unable to connect to the SHL API."""


class SHLTimeoutError(SHLError):
    """Raised when a request to the SHL API times out."""
