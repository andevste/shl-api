"""Asynchronous Python client for Swedish Hockey League (SHL) API."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Union

from .client import SHLClient
from .const import (
    DEFAULT_BASE_URL,
    DEFAULT_INSTANCE_ID,
    DEFAULT_SERIES_CODE,
    DEFAULT_SERIES_UUID,
    DEFAULT_TIMEOUT,
)
from .models import (
    Article,
    Game,
    GameDay,
    GameForm,
    SiteSettings,
    Standings,
    Team,
)


class AsyncSHLClient:
    """Asynchronous client for querying the Swedish Hockey League (SHL) API.

    Example usage:
        >>> async with AsyncSHLClient() as client:
        ...     teams = await client.get_teams()
        ...     standings = await client.get_standings()
        ...     last_games = await client.get_last_game_day()
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        instance_id: str = DEFAULT_INSTANCE_ID,
        series_uuid: str = DEFAULT_SERIES_UUID,
        series_code: str = DEFAULT_SERIES_CODE,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._sync_client = SHLClient(
            base_url=base_url,
            instance_id=instance_id,
            series_uuid=series_uuid,
            series_code=series_code,
            timeout=timeout,
        )

    async def __aenter__(self) -> AsyncSHLClient:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the underlying client session."""
        await asyncio.to_thread(self._sync_client.close)

    async def get_site_settings(self, force_refresh: bool = False) -> SiteSettings:
        """Fetch general site settings, configurations, and all league teams."""
        return await asyncio.to_thread(self._sync_client.get_site_settings, force_refresh)

    async def get_teams(self, force_refresh: bool = False) -> List[Team]:
        """Fetch all Swedish Hockey League teams."""
        return await asyncio.to_thread(self._sync_client.get_teams, force_refresh)

    async def get_team(self, identifier: str) -> Optional[Team]:
        """Find a team by code (e.g. 'FBK'), name ('Färjestad'), or UUID."""
        return await asyncio.to_thread(self._sync_client.get_team, identifier)

    async def get_tournament_context(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Dynamically resolve the active season, series, and seasonSeriesGameType (ssgtUuid)."""
        return await asyncio.to_thread(self._sync_client.get_tournament_context, force_refresh)

    async def get_standings(self, ssgt_uuid: Optional[str] = None) -> Standings:
        """Fetch current SHL league standings table."""
        return await asyncio.to_thread(self._sync_client.get_standings, ssgt_uuid)

    async def get_last_game_day(self, ssgt_uuid: Optional[str] = None) -> GameDay:
        """Fetch the most recent game day results and played games."""
        return await asyncio.to_thread(self._sync_client.get_last_game_day, ssgt_uuid)

    async def get_next_game_day(self, ssgt_uuid: Optional[str] = None) -> GameDay:
        """Fetch the upcoming game day and scheduled games."""
        return await asyncio.to_thread(self._sync_client.get_next_game_day, ssgt_uuid)

    async def get_today_games(self, ssgt_uuid: Optional[str] = None) -> List[Game]:
        """Fetch games scheduled for today (returns empty list if none)."""
        return await asyncio.to_thread(self._sync_client.get_today_games, ssgt_uuid)

    async def get_schedule(
        self,
        team: Optional[str] = None,
        played: Optional[Union[bool, str]] = None,
        game_place: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Game]:
        """Fetch season schedule, optionally filtered by team, played status, place, or limit."""
        return await asyncio.to_thread(self._sync_client.get_schedule, team, played, game_place, limit)

    async def get_upcoming_games(
        self,
        team: Optional[str] = None,
        limit: int = 10,
    ) -> List[Game]:
        """Fetch upcoming games across the league or for a specific team."""
        return await asyncio.to_thread(self._sync_client.get_upcoming_games, team, limit)

    async def get_played_games(self, team: str) -> List[Game]:
        """Fetch played games for a specific team."""
        return await asyncio.to_thread(self._sync_client.get_played_games, team)

    async def get_game(self, game_uuid: str) -> Game:
        """Fetch details of a single game by its UUID."""
        return await asyncio.to_thread(self._sync_client.get_game, game_uuid)

    async def get_game_form(
        self,
        home_team: str,
        away_team: str,
        ssgt_uuid: Optional[str] = None,
    ) -> GameForm:
        """Fetch head-to-head match form between two teams and their last meetings."""
        return await asyncio.to_thread(self._sync_client.get_game_form, home_team, away_team, ssgt_uuid)

    async def get_team_form(self, team: str) -> Dict[str, Any]:
        """Fetch single team recent game form."""
        return await asyncio.to_thread(self._sync_client.get_team_form, team)

    async def get_statistics_overview(
        self,
        provider: str = "statnet",
        ssgt_uuid: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch statistical overview for teams and player leaderboards."""
        return await asyncio.to_thread(self._sync_client.get_statistics_overview, provider, ssgt_uuid)

    async def get_news(self, limit: int = 10, page: int = 0) -> List[Article]:
        """Fetch latest news articles from SHL."""
        return await asyncio.to_thread(self._sync_client.get_news, limit, page)

    async def get_article(self, article_id: str) -> Article:
        """Fetch full article content by article ID."""
        return await asyncio.to_thread(self._sync_client.get_article, article_id)

    async def get_rss(self) -> str:
        """Fetch raw RSS feed from the SHL articles RSS endpoint."""
        return await asyncio.to_thread(self._sync_client.get_rss)
