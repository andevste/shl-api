"""Data models for Swedish Hockey League (SHL) API entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional, Union


def _parse_datetime(val: Optional[str]) -> Optional[datetime]:
    """Parse ISO or RFC formatted datetime string safely."""
    if not val:
        return None
    val = val.strip()
    try:
        # Replace trailing Z with UTC timezone
        if val.endswith("Z"):
            val = val[:-1] + "+00:00"
        return datetime.fromisoformat(val)
    except (ValueError, TypeError):
        try:
            return datetime.strptime(val, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            return None


def _parse_int(val: Any, default: Optional[int] = None) -> Optional[int]:
    """Parse an integer safely, returning default if invalid or 'N/A'."""
    if val is None or val == "" or val == "N/A":
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


@dataclass
class Team:
    """Represents a team in the Swedish Hockey League."""

    uuid: str
    code: str
    name: str
    short_name: str
    long_name: str
    full_name: str
    logo_url: str
    icon_url: str
    public_url: str
    instance_id: str
    founded: Optional[str] = None
    golds: Optional[str] = None
    finals: Optional[str] = None
    retired_numbers: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    social_media: Dict[str, str] = field(default_factory=dict)
    series_codes: List[str] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Team:
        """Create a Team instance from an API response dictionary."""
        team_names = data.get("teamNames") or {}
        team_info = data.get("teamInfo") or {}
        code = data.get("teamCode") or team_names.get("code") or data.get("ownersite") or ""
        name = data.get("name") or team_names.get("short") or code
        short_name = team_names.get("short") or name
        long_name = team_names.get("long") or name
        full_name = team_names.get("full") or long_name

        social_media: Dict[str, str] = {}
        for sm in data.get("socialMediaInformation", []) or []:
            if isinstance(sm, dict) and sm.get("type") and sm.get("url"):
                social_media[sm["type"]] = sm["url"]
        for key in ("facebook", "instagram", "twitter"):
            if team_info.get(key):
                social_media[key] = team_info[key]

        series_codes: List[str] = [
            str(s["code"]) for s in data.get("series", []) or [] if isinstance(s, dict) and s.get("code")
        ]

        return cls(
            uuid=data.get("uuid") or data.get("id") or "",
            code=code,
            name=name,
            short_name=short_name,
            long_name=long_name,
            full_name=full_name,
            logo_url=data.get("logo") or "",
            icon_url=data.get("icon") or data.get("logo") or "",
            public_url=data.get("publicUrl") or "",
            instance_id=data.get("ownerInstanceId") or data.get("instanceId") or "",
            founded=team_info.get("founded"),
            golds=team_info.get("golds"),
            finals=team_info.get("finals"),
            retired_numbers=team_info.get("retiredNumbers") or team_info.get("retired_numbers"),
            address=team_info.get("address"),
            phone=team_info.get("phone"),
            email=team_info.get("email"),
            social_media=social_media,
            series_codes=series_codes,
            raw_data=data,
        )


@dataclass
class TeamGameInfo:
    """Represents team information within a specific game."""

    code: str
    short_name: str
    long_name: str
    full_name: str
    score: Optional[int]
    status: str
    logo_url: Optional[str] = None
    uuid: Optional[str] = None
    instance_id: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TeamGameInfo:
        """Create TeamGameInfo from API dictionary."""
        names = data.get("names") or {}
        code = data.get("code") or names.get("code") or ""
        short_name = names.get("short") or code
        long_name = names.get("long") or short_name
        full_name = names.get("full") or long_name
        score = _parse_int(data.get("score"))
        status = data.get("status") or ("N/A" if score is None else "")

        return cls(
            code=code,
            short_name=short_name,
            long_name=long_name,
            full_name=full_name,
            score=score,
            status=status,
            logo_url=data.get("icon") or data.get("logo"),
            uuid=data.get("uuid"),
            instance_id=data.get("ownerInstanceId") or data.get("instanceId"),
            raw_data=data,
        )


@dataclass
class Game:
    """Represents a game in the Swedish Hockey League."""

    uuid: str
    start_date_time: Optional[datetime]
    start_date_time_str: Optional[str]
    state: str
    overtime: bool
    shootout: bool
    home_team: TeamGameInfo
    away_team: TeamGameInfo
    venue_name: Optional[str] = None
    venue_uuid: Optional[str] = None
    series_code: str = "SHL"
    series_name: str = "SHL"
    round_number: Optional[int] = None
    ssgt_uuid: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def is_finished(self) -> bool:
        """Return True if the game has ended."""
        return self.state in ("post-game", "post_game", "GameEnded")

    @property
    def is_live(self) -> bool:
        """Return True if the game is currently live."""
        return self.state in ("live", "live-game", "Ongoing", "PeriodBreak")

    @property
    def is_upcoming(self) -> bool:
        """Return True if the game has not started yet."""
        return self.state in ("pre-game", "pre_game", "upcoming", "NotStarted")

    @property
    def winner_code(self) -> Optional[str]:
        """Return the team code of the winner, if finished."""
        if not self.is_finished:
            return None
        if self.home_team.score is not None and self.away_team.score is not None:
            if self.home_team.score > self.away_team.score:
                return self.home_team.code
            if self.away_team.score > self.home_team.score:
                return self.away_team.code
        if self.home_team.status == "WIN":
            return self.home_team.code
        if self.away_team.status == "WIN":
            return self.away_team.code
        return None

    @property
    def summary(self) -> str:
        """Return a human-readable one-line game summary."""
        h_score = self.home_team.score if self.home_team.score is not None else "-"
        a_score = self.away_team.score if self.away_team.score is not None else "-"
        extra = ""
        if self.shootout:
            extra = " (SO)"
        elif self.overtime:
            extra = " (OT)"

        state_label = self.state
        if self.is_finished:
            state_label = "Slut"
        elif self.is_live:
            state_label = "Live"

        return f"{self.home_team.code} {h_score} - {a_score} {self.away_team.code}{extra} [{state_label}]"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Game:
        """Create a Game instance from an API response dictionary."""
        # Support both game structure from /sports-v2/last-game-day and /sports-v2/game-info
        home_raw = data.get("homeTeamInfo") or data.get("homeTeam") or {}
        away_raw = data.get("awayTeamInfo") or data.get("awayTeam") or {}
        venue_raw = data.get("venueInfo") or {}
        series_raw = data.get("seriesInfo") or {}

        # Handle score attached at gameInfo level if present
        game_info = data.get("gameInfo") or {}
        venue_name = venue_raw.get("name") or game_info.get("arenaName") or data.get("arenaName")
        series_code = series_raw.get("code") or game_info.get("seriesCode") or "SHL"
        series_name = series_raw.get("displayName") or game_info.get("seriesDisplayName") or series_code

        dt_str = data.get("startDateTime") or data.get("rawStartDateTime") or game_info.get("startDateTime")
        state = data.get("state") or game_info.get("state") or "unknown"
        overtime = bool(data.get("overtime", game_info.get("overtime", False)))
        shootout = bool(data.get("shootout", game_info.get("shootout", False)))
        round_number = _parse_int(data.get("roundNumber", game_info.get("roundNumber")))

        return cls(
            uuid=data.get("uuid") or game_info.get("gameUuid") or "",
            start_date_time=_parse_datetime(dt_str),
            start_date_time_str=dt_str,
            state=state,
            overtime=overtime,
            shootout=shootout,
            home_team=TeamGameInfo.from_dict(home_raw),
            away_team=TeamGameInfo.from_dict(away_raw),
            venue_name=venue_name,
            venue_uuid=venue_raw.get("uuid"),
            series_code=series_code,
            series_name=series_name,
            round_number=round_number,
            ssgt_uuid=data.get("ssgtUuid") or data.get("seasonSeriesGameType"),
            raw_data=data,
        )


@dataclass
class GameDay:
    """Represents a date and the games played/scheduled on that day."""

    date: str
    games: List[Game] = field(default_factory=list)

    def __iter__(self) -> Iterator[Game]:
        return iter(self.games)

    def __len__(self) -> int:
        return len(self.games)

    def __getitem__(self, index: int) -> Game:
        return self.games[index]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GameDay:
        """Create GameDay from API dictionary."""
        date = data.get("date") or ""
        raw_games = data.get("games") or []
        games = [Game.from_dict(g) for g in raw_games if isinstance(g, dict)]
        return cls(date=date, games=games)


@dataclass
class StandingRow:
    """Represents a single team's standing row in the SHL league table."""

    rank: int
    team_code: str
    team_name: str
    team_uuid: str
    games_played: int
    wins: int
    ot_wins: int
    losses: int
    ot_losses: int
    goals_for: int
    goals_against: int
    goal_diff: int
    points: int
    team_logo: Optional[str] = None
    club_url: Optional[str] = None
    team_owner_instance_id: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> StandingRow:
        """Create StandingRow from API dictionary."""
        info = data.get("info") or {}
        team_info = info.get("teamInfo") or {}
        team_names = team_info.get("teamNames") or {}

        code = info.get("teamId") or team_info.get("teamId") or team_names.get("code") or ""
        name = team_info.get("siteTeamDisplayName") or team_names.get("short") or info.get("code") or code

        return cls(
            rank=_parse_int(data.get("Rank"), 0) or 0,
            team_code=code,
            team_name=name,
            team_uuid=team_info.get("teamUuid") or "",
            games_played=_parse_int(data.get("GP"), 0) or 0,
            wins=_parse_int(data.get("W"), 0) or 0,
            ot_wins=_parse_int(data.get("OTW"), 0) or 0,
            losses=_parse_int(data.get("L"), 0) or 0,
            ot_losses=_parse_int(data.get("OTL"), 0) or 0,
            goals_for=_parse_int(data.get("G"), 0) or 0,
            goals_against=_parse_int(data.get("GA"), 0) or 0,
            goal_diff=_parse_int(data.get("Diff"), 0) or 0,
            points=_parse_int(data.get("Points"), 0) or 0,
            team_logo=team_info.get("teamMedia"),
            club_url=team_info.get("clubPageLink"),
            team_owner_instance_id=team_info.get("teamOwnerInstanceId"),
            raw_data=data,
        )


@dataclass
class Standings:
    """Represents the complete standings table for the Swedish Hockey League."""

    rows: List[StandingRow] = field(default_factory=list)
    provider: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict, repr=False)

    def __iter__(self) -> Iterator[StandingRow]:
        return iter(self.rows)

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: Union[int, slice]) -> Union[StandingRow, List[StandingRow]]:
        return self.rows[index]

    def get(self, team_code_or_name: str) -> Optional[StandingRow]:
        """Look up a team's standing row by team code (e.g., 'FBK') or name."""
        query = team_code_or_name.strip().lower()
        for row in self.rows:
            if row.team_code.lower() == query or row.team_name.lower() == query:
                return row
        return None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Standings:
        """Create Standings from API dictionary."""
        raw_rows = data.get("leagueStandings") or []
        rows = [StandingRow.from_dict(r) for r in raw_rows if isinstance(r, dict)]
        rows.sort(key=lambda r: r.rank)
        return cls(
            rows=rows,
            provider=data.get("provider"),
            raw_data=data,
        )


@dataclass
class GameForm:
    """Represents recent game form and head-to-head match history."""

    home_team: Dict[str, Any] = field(default_factory=dict)
    away_team: Dict[str, Any] = field(default_factory=dict)
    last_meetings: List[Dict[str, Any]] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GameForm:
        """Create GameForm from API dictionary."""
        return cls(
            home_team=data.get("homeTeam") or {},
            away_team=data.get("awayTeam") or {},
            last_meetings=data.get("lastMeetings") or [],
            raw_data=data,
        )


@dataclass
class Article:
    """Represents a news article from the SHL news feed."""

    id: str
    header: str
    intro: Optional[str] = None
    published_at: Optional[datetime] = None
    author: Optional[str] = None
    image_url: Optional[str] = None
    body_html: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Article:
        """Create Article from API dictionary."""
        author_data = data.get("author") or {}
        author = author_data.get("name") if isinstance(author_data, dict) else None
        main_media = data.get("mainMediaRenderMetaData") or {}
        image_url = main_media.get("url") if isinstance(main_media, dict) else None

        return cls(
            id=data.get("id") or "",
            header=data.get("header") or "",
            intro=data.get("intro") or data.get("introRawText"),
            published_at=_parse_datetime(data.get("publishedAt")),
            author=author,
            image_url=image_url,
            body_html=data.get("body"),
            raw_data=data,
        )


@dataclass
class SiteSettings:
    """Represents the site settings, metadata, and league teams from /api/site/settings."""

    instance_id: str
    name: str
    is_league_site: bool
    logo_url: str
    country: str
    sport: str
    teams: List[Team] = field(default_factory=list)
    social_media: List[Dict[str, str]] = field(default_factory=list)
    feature_flags: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    raw_data: Dict[str, Any] = field(default_factory=dict, repr=False)

    def get_team(self, code_or_name: str) -> Optional[Team]:
        """Look up a team by code (e.g. 'FBK') or name (e.g. 'Färjestad')."""
        query = code_or_name.strip().lower()
        for t in self.teams:
            if (
                t.code.lower() == query
                or t.name.lower() == query
                or t.short_name.lower() == query
                or t.uuid.lower() == query
            ):
                return t
        return None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SiteSettings:
        """Create SiteSettings from API dictionary."""
        sport_info = data.get("siteSportInformation") or {}
        raw_teams = data.get("teamsInSite") or []
        teams = [Team.from_dict(t) for t in raw_teams if isinstance(t, dict)]

        return cls(
            instance_id=data.get("instanceId") or "",
            name=data.get("name") or "SHL",
            is_league_site=bool(data.get("isLeagueSite", True)),
            logo_url=data.get("logo") or "",
            country=sport_info.get("country") or "se",
            sport=sport_info.get("type") or "hockey",
            teams=teams,
            social_media=data.get("socialMediaInformation") or [],
            feature_flags=data.get("featureFlags") or {},
            config=data.get("config") or {},
            raw_data=data,
        )
