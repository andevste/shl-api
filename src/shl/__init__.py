"""Swedish Hockey League (SHL) Python API library.

A clean, modern Python client for the Swedish Hockey League (SHL) API,
providing access to teams, league standings, schedules, game results,
form, player statistics, and news.
"""

from __future__ import annotations

from .async_client import AsyncSHLClient
from .client import SHLClient
from .exceptions import (
    SHLAPIError,
    SHLConnectionError,
    SHLError,
    SHLNotFoundError,
    SHLTimeoutError,
)
from .models import (
    Article,
    Game,
    GameDay,
    GameForm,
    SiteSettings,
    StandingRow,
    Standings,
    Team,
    TeamGameInfo,
)

__version__ = "0.1.0"

__all__ = [
    "SHLClient",
    "AsyncSHLClient",
    "SHLError",
    "SHLAPIError",
    "SHLNotFoundError",
    "SHLConnectionError",
    "SHLTimeoutError",
    "Team",
    "TeamGameInfo",
    "Game",
    "GameDay",
    "StandingRow",
    "Standings",
    "GameForm",
    "Article",
    "SiteSettings",
]
