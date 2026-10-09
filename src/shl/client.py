"""Synchronous Python client for Swedish Hockey League (SHL) API."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Union

import requests
from requests.exceptions import ConnectionError as ReqConnectionError
from requests.exceptions import HTTPError, RequestException, Timeout

from .const import (
    DEFAULT_BASE_URL,
    DEFAULT_HEADERS,
    DEFAULT_INSTANCE_ID,
    DEFAULT_SERIES_CODE,
    DEFAULT_SERIES_UUID,
    DEFAULT_TIMEOUT,
)
from .exceptions import (
    SHLAPIError,
    SHLConnectionError,
    SHLNotFoundError,
    SHLTimeoutError,
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

logger = logging.getLogger(__name__)


class SHLClient:
    """Client for querying the Swedish Hockey League (SHL) API.

    Example usage:
        >>> with SHLClient() as client:
        ...     teams = client.get_teams()
        ...     standings = client.get_standings()
        ...     last_games = client.get_last_game_day()
        ...     fbk = client.get_team("FBK")
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        instance_id: str = DEFAULT_INSTANCE_ID,
        series_uuid: str = DEFAULT_SERIES_UUID,
        series_code: str = DEFAULT_SERIES_CODE,
        timeout: float = DEFAULT_TIMEOUT,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.instance_id = instance_id
        self.series_uuid = series_uuid
        self.series_code = series_code
        self.timeout = timeout

        self._session_provided = session is not None
        self._session = session or requests.Session()

        # Cached tournament and team state
        self._site_settings: Optional[SiteSettings] = None
        self._teams_cache: Optional[List[Team]] = None
        self._tournament_context: Optional[Dict[str, Any]] = None

    def __enter__(self) -> SHLClient:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying session if created by this client."""
        if not self._session_provided:
            self._session.close()

    def _request(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Make an HTTP GET request to the SHL API."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        req_headers = dict(DEFAULT_HEADERS)
        req_headers["x-s8y-instance-id"] = self.instance_id
        if headers:
            req_headers.update(headers)

        # Filter out None values in params
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}

        try:
            resp = self._session.get(
                url,
                params=clean_params,
                headers=req_headers,
                timeout=self.timeout,
            )
            resp.raise_for_status()

            # Handle empty response body (e.g. today-games when no games scheduled)
            if not resp.content or not resp.text.strip():
                return {}

            # Handle non-JSON response (e.g. RSS XML)
            content_type = resp.headers.get("content-type", "")
            if "application/json" not in content_type and ("xml" in content_type or "text" in content_type):
                return resp.text

            return resp.json()
        except Timeout as err:
            raise SHLTimeoutError(f"Request to {url} timed out after {self.timeout}s") from err
        except ReqConnectionError as err:
            raise SHLConnectionError(f"Failed to connect to SHL API at {url}") from err
        except HTTPError as err:
            status = resp.status_code if resp is not None else None
            text = resp.text if resp is not None else ""
            if status == 404:
                raise SHLNotFoundError(f"Resource not found: {url}", status_code=status, response_text=text) from err
            raise SHLAPIError(f"SHL API error ({status}): {text}", status_code=status, response_text=text) from err
        except RequestException as err:
            raise SHLAPIError(f"Unexpected request error: {err}") from err

    def get_site_settings(self, force_refresh: bool = False) -> SiteSettings:
        """Fetch general site settings, configurations, and all league teams.

        Endpoint: /api/site/settings
        """
        if self._site_settings is None or force_refresh:
            data = self._request("/site/settings")
            self._site_settings = SiteSettings.from_dict(data)
            self._teams_cache = self._site_settings.teams
        return self._site_settings

    def get_teams(self, force_refresh: bool = False) -> List[Team]:
        """Fetch all Swedish Hockey League teams."""
        if self._teams_cache is None or force_refresh:
            settings = self.get_site_settings(force_refresh=force_refresh)
            self._teams_cache = settings.teams
        return list(self._teams_cache)

    def get_team(self, identifier: str) -> Optional[Team]:
        """Find a team by code (e.g. 'FBK'), name ('Färjestad'), or UUID."""
        teams = self.get_teams()
        query = identifier.strip().lower()
        for t in teams:
            if (
                t.code.lower() == query
                or t.name.lower() == query
                or t.short_name.lower() == query
                or t.uuid.lower() == query
            ):
                return t
        return None

    def _resolve_team_uuid(self, identifier: str) -> str:
        """Resolve a team code or name to a team UUID, or return identifier if already a UUID."""
        team = self.get_team(identifier)
        if team:
            return team.uuid
        return identifier

    def get_tournament_context(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Dynamically resolve the active season, series, and seasonSeriesGameType (ssgtUuid).

        Endpoint: /api/sports-v2/latest-ssgt/{seriesUuid}
        """
        if self._tournament_context is None or force_refresh:
            # First try using self.series_uuid
            try:
                data = self._request(f"/sports-v2/latest-ssgt/{self.series_uuid}")
            except SHLAPIError:
                # If series_uuid failed, discover it from site settings
                settings = self.get_site_settings()
                discovered_uuid = None
                for t in settings.teams:
                    for s in t.raw_data.get("series", []):
                        if isinstance(s, dict) and s.get("code") == self.series_code:
                            discovered_uuid = s.get("uuid")
                            break
                    if discovered_uuid:
                        break
                if discovered_uuid and discovered_uuid != self.series_uuid:
                    self.series_uuid = discovered_uuid
                    data = self._request(f"/sports-v2/latest-ssgt/{self.series_uuid}")
                else:
                    raise

            self._tournament_context = {
                "ssgt_uuid": data.get("uuid"),
                "season_uuid": (data.get("season") or {}).get("uuid"),
                "season_code": (data.get("season") or {}).get("code"),
                "series_uuid": (data.get("series") or {}).get("uuid") or self.series_uuid,
                "game_type_uuid": (data.get("gameType") or {}).get("uuid"),
                "raw_data": data,
            }
        return self._tournament_context

    def get_standings(self, ssgt_uuid: Optional[str] = None) -> Standings:
        """Fetch current SHL league standings table.

        Endpoint: /api/statistics-v2/league-standings?ssgtUuid={ssgt_uuid}
        """
        if not ssgt_uuid:
            ctx = self.get_tournament_context()
            ssgt_uuid = ctx["ssgt_uuid"]

        data = self._request("/statistics-v2/league-standings", params={"ssgtUuid": ssgt_uuid})
        return Standings.from_dict(data)

    def get_last_game_day(self, ssgt_uuid: Optional[str] = None) -> GameDay:
        """Fetch the most recent game day results and played games.

        Endpoint: /api/sports-v2/last-game-day?seasonSeriesGameType={ssgt_uuid}
        """
        if not ssgt_uuid:
            ctx = self.get_tournament_context()
            ssgt_uuid = ctx["ssgt_uuid"]

        data = self._request("/sports-v2/last-game-day", params={"seasonSeriesGameType": ssgt_uuid})
        return GameDay.from_dict(data)

    def get_next_game_day(self, ssgt_uuid: Optional[str] = None) -> GameDay:
        """Fetch the upcoming game day and scheduled games.

        Endpoint: /api/sports-v2/next-game-day?seasonSeriesGameType={ssgt_uuid}
        """
        if not ssgt_uuid:
            ctx = self.get_tournament_context()
            ssgt_uuid = ctx["ssgt_uuid"]

        data = self._request("/sports-v2/next-game-day", params={"seasonSeriesGameType": ssgt_uuid})
        return GameDay.from_dict(data)

    def get_today_games(self, ssgt_uuid: Optional[str] = None) -> List[Game]:
        """Fetch games scheduled for today (returns empty list if none).

        Endpoint: /api/sports-v2/today-games?seasonSeriesGameType={ssgt_uuid}
        """
        if not ssgt_uuid:
            ctx = self.get_tournament_context()
            ssgt_uuid = ctx["ssgt_uuid"]

        data = self._request("/sports-v2/today-games", params={"seasonSeriesGameType": ssgt_uuid})
        if isinstance(data, list):
            return [Game.from_dict(g) for g in data if isinstance(g, dict)]
        if isinstance(data, dict):
            raw_games = data.get("games") or data.get("todayGames") or []
            return [Game.from_dict(g) for g in raw_games if isinstance(g, dict)]
        return []

    def get_schedule(
        self,
        team: Optional[str] = None,
        played: Optional[Union[bool, str]] = None,
        game_place: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Game]:
        """Fetch season schedule, optionally filtered by team, played status, place, or limit.

        Endpoint: /api/sports-v2/game-schedule
        """
        ctx = self.get_tournament_context()
        params: Dict[str, Any] = {
            "seasonUuid": ctx.get("season_uuid"),
            "seriesUuid": ctx.get("series_uuid"),
            "gameTypeUuid": ctx.get("game_type_uuid"),
        }
        if team:
            params["teams"] = self._resolve_team_uuid(team)
        if played is not None:
            params["played"] = "true" if played is True else ("false" if played is False else str(played))
        if game_place:
            params["gamePlace"] = game_place

        data = self._request("/sports-v2/game-schedule", params=params)
        raw_games = data.get("gameInfo") or []
        games = [Game.from_dict(g) for g in raw_games if isinstance(g, dict)]

        # If team filter was provided and API didn't filter on server side, filter client side
        if team:
            q = team.strip().lower()
            games = [
                g
                for g in games
                if (
                    g.home_team.code.lower() == q
                    or g.away_team.code.lower() == q
                    or (g.home_team.uuid and g.home_team.uuid.lower() == q)
                    or (g.away_team.uuid and g.away_team.uuid.lower() == q)
                    or q in g.home_team.short_name.lower()
                    or q in g.away_team.short_name.lower()
                )
            ]
        if limit is not None:
            games = games[:limit]
        return games

    def get_upcoming_games(
        self,
        team: Optional[str] = None,
        limit: int = 10,
    ) -> List[Game]:
        """Fetch upcoming games across the league or for a specific team.

        Endpoint: /api/sports-v2/upcoming-games/{teamUuid} OR /api/sports-v2/upcoming-games?series[]={seriesUuid}
        """
        if team:
            team_uuid = self._resolve_team_uuid(team)
            data = self._request(f"/sports-v2/upcoming-games/{team_uuid}")
        else:
            ctx = self.get_tournament_context()
            series_uuid = ctx.get("series_uuid") or self.series_uuid
            data = self._request(
                "/sports-v2/upcoming-games",
                params={"series[]": series_uuid, "pageSize": limit},
            )

        raw_games = data.get("upcomingGames") or []
        games = [Game.from_dict(g) for g in raw_games if isinstance(g, dict)]
        return games[:limit]

    def get_played_games(self, team: str) -> List[Game]:
        """Fetch played games for a specific team.

        Endpoint: /api/sports-v2/played-games/{teamUuid}
        """
        team_uuid = self._resolve_team_uuid(team)
        data = self._request(f"/sports-v2/played-games/{team_uuid}")
        raw_games = data.get("playedGames") or []
        return [Game.from_dict(g) for g in raw_games if isinstance(g, dict)]

    def get_game(self, game_uuid: str) -> Game:
        """Fetch details of a single game by its UUID.

        Endpoint: /api/sports-v2/game-info/{gameUuid}
        """
        data = self._request(f"/sports-v2/game-info/{game_uuid}")
        return Game.from_dict(data)

    def get_game_form(
        self,
        home_team: str,
        away_team: str,
        ssgt_uuid: Optional[str] = None,
    ) -> GameForm:
        """Fetch head-to-head match form between two teams and their last meetings.

        Endpoint: /api/statistics-v2/game-form
        """
        if not ssgt_uuid:
            ctx = self.get_tournament_context()
            ssgt_uuid = ctx["ssgt_uuid"]

        home_uuid = self._resolve_team_uuid(home_team)
        away_uuid = self._resolve_team_uuid(away_team)

        data = self._request(
            "/statistics-v2/game-form",
            params={
                "homeTeamUuid": home_uuid,
                "awayTeamUuid": away_uuid,
                "ssgtUuid": ssgt_uuid,
            },
        )
        return GameForm.from_dict(data)

    def get_team_form(self, team: str) -> Dict[str, Any]:
        """Fetch single team recent game form.

        Endpoint: /api/statistics-v2/team-page/single-game-form?teamUuid={teamUuid}
        """
        team_uuid = self._resolve_team_uuid(team)
        return self._request(
            "/statistics-v2/team-page/single-game-form",
            params={"teamUuid": team_uuid},
        )

    def get_statistics_overview(
        self,
        provider: str = "statnet",
        ssgt_uuid: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch statistical overview for teams and player leaderboards.

        Endpoint: /api/statistics-v2/overview/{ssgtUuid}?provider={provider}
        """
        if not ssgt_uuid:
            ctx = self.get_tournament_context()
            ssgt_uuid = ctx["ssgt_uuid"]

        return self._request(
            f"/statistics-v2/overview/{ssgt_uuid}",
            params={"provider": provider},
        )

    def get_news(self, limit: int = 10, page: int = 0) -> List[Article]:
        """Fetch latest news articles from SHL.

        Endpoint: /api/articles/site-news/list
        """
        data = self._request(
            "/articles/site-news/list",
            params={"count": limit, "page": page},
        )
        data_block = data.get("data") or {}
        items = data_block.get("articleItems") or []
        return [Article.from_dict(item) for item in items[:limit] if isinstance(item, dict)]

    def get_article(self, article_id: str) -> Article:
        """Fetch full article content by article ID.

        Endpoint: /api/articles/{id}/view
        """
        data = self._request(f"/articles/{article_id}/view")
        return Article.from_dict(data)

    def get_rss(self) -> str:
        """Fetch raw RSS feed from the SHL articles RSS endpoint.

        Endpoint: /api/articles/rss
        """
        return self._request("/articles/rss")
