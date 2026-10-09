"""Constants for the SHL API client."""

from __future__ import annotations

DEFAULT_BASE_URL = "https://www.shl.se/api"
DEFAULT_INSTANCE_ID = "shl1_shl"
DEFAULT_SERIES_CODE = "SHL"
DEFAULT_SERIES_UUID = "qQ9-bb0bzEWUk"

DEFAULT_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "x-s8y-instance-id": DEFAULT_INSTANCE_ID,
    "User-Agent": "shl-api-python/1.0.0",
}

DEFAULT_TIMEOUT = 10.0
