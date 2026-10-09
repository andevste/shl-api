# shl-api 🏒

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A modern, fast, and feature-rich Python client and CLI for the **Swedish Hockey League (SHL)** API.

Provides typed access to:
- 🏒 **Teams**: metadata, logos, arena, championships, retired numbers, contact info.
- 📊 **Standings (Tabell)**: rank, GP, wins, overtime wins/losses, losses, goals, goal diff, points.
- 📅 **Schedule & Game Results (Spelschema)**: season schedule, last played games, next game day, today's games.
- 🔍 **Game Details & Head-to-head**: arena info, period results, team form, past meetings.
- 📰 **News & RSS**: articles, headlines, press releases, RSS feeds.
- ⚙️ **League Settings & Status**: live endpoint from `https://www.shl.se/api/site/settings`.
- ⚡ **Both Sync (`SHLClient`) and Async (`AsyncSHLClient`)** interfaces.
- 💻 **Interactive CLI (`shl`)** with rich tables and JSON export.

---

## Installation

```bash
pip install shl-api
```

Or install locally in editable mode:

```bash
pip install -e .
```

---

## Quickstart

Both `import shl` and `import shl_api` are supported:

### Synchronous Usage

```python
from shl import SHLClient

with SHLClient() as client:
    # 1. Get all SHL teams
    teams = client.get_teams()
    for team in teams:
        print(f"{team.code}: {team.name} ({team.full_name})")

    # 2. Get current league standings
    standings = client.get_standings()
    for row in standings:
        print(f"#{row.rank:2} {row.team_name:<20} {row.points} pts (GP: {row.games_played})")

    # 3. Get results from the most recent game day
    last_games = client.get_last_game_day()
    print(f"Date: {last_games.date}")
    for game in last_games:
        print(game.summary)
        # e.g.: "LHF 2 - 3 MIF [Slut]"

    # 4. Get schedule for the upcoming game day
    next_games = client.get_next_game_day()
    print(f"Date: {next_games.date}")
    for game in next_games:
        print(f"{game.home_team.short_name} vs {game.away_team.short_name} at {game.venue_name}")

    # 5. Get a specific team by code, name, or UUID
    fbk = client.get_team("FBK")
    print(f"{fbk.name} - Founded: {fbk.founded}, Arena: {fbk.address}")
```

### Asynchronous Usage (`asyncio`)

Perfect for Home Assistant integrations, FastAPI, Discord bots, and asynchronous applications:

```python
import asyncio
from shl import AsyncSHLClient

async def main():
    async with AsyncSHLClient() as client:
        # Fetch standings and teams concurrently
        standings, teams = await asyncio.gather(
            client.get_standings(),
            client.get_teams(),
        )
        print(f"Loaded {len(teams)} teams. Leader: {standings[0].team_name}")

asyncio.run(main())
```

---

## API Reference

### Teams
- `client.get_teams(force_refresh=False)`: Returns a list of all 14 `Team` objects.
- `client.get_team(identifier)`: Look up a team by code (`"FBK"`, `"LHF"`), name (`"Färjestad"`, `"Luleå"`), or UUID.
- `team.uuid`, `team.code`, `team.name`, `team.short_name`, `team.full_name`, `team.logo_url`, `team.public_url`, `team.founded`, `team.golds`, `team.finals`, `team.retired_numbers`, `team.address`, `team.phone`, `team.email`, `team.social_media`.

### League Standings
- `client.get_standings()`: Returns a `Standings` collection of `StandingRow` objects.
- `standings[0]`: Top team in the league.
- `standings.get("FBK")`: Look up standing row for a specific team.
- Properties on `StandingRow`: `rank`, `team_code`, `team_name`, `games_played`, `wins`, `ot_wins`, `losses`, `ot_losses`, `goals_for`, `goals_against`, `goal_diff`, `points`, `team_logo`.

### Schedule & Games
- `client.get_last_game_day()`: Results from the most recent game day.
- `client.get_next_game_day()`: Schedule for the next upcoming game day.
- `client.get_today_games()`: Games scheduled for today (empty list if no games today).
- `client.get_schedule(team=None, played=None, limit=None)`: Full season schedule with optional filters.
- `client.get_upcoming_games(team=None, limit=10)`: Upcoming games across the league or for a specific team.
- `client.get_played_games(team)`: Completed games for a given team.
- `client.get_game(game_uuid)`: Full details for a single game.
- Properties on `Game`: `uuid`, `start_date_time`, `state`, `overtime`, `shootout`, `home_team`, `away_team`, `venue_name`, `is_finished`, `is_live`, `is_upcoming`, `winner_code`, `summary`.

### Team Form & Statistics
- `client.get_game_form(home_team, away_team)`: Recent head-to-head match history between two teams.
- `client.get_team_form(team)`: Recent match form for a single team.
- `client.get_statistics_overview()`: Team stats and player leaderboards.

### News & Settings
- `client.get_news(limit=10, page=0)`: Latest news articles from the SHL editorial desk.
- `client.get_article(article_id)`: Detailed article content with body HTML, author, and images.
- `client.get_rss()`: Raw RSS feed XML string from `/api/articles/rss`.
- `client.get_site_settings()`: Full site settings from `https://www.shl.se/api/site/settings`.

---

## CLI Usage

The package installs the `shl` command-line tool:

```bash
# List all teams
shl teams

# View a specific team profile
shl team FBK

# View current league standings (tabell)
shl standings

# View results from the last played game day
shl last

# View schedule for the next upcoming game day
shl next

# View games today
shl today

# View schedule (optionally filter by team)
shl games --team FBK --limit 5

# View latest news
shl news --limit 3

# View league settings
shl settings
```

### JSON Output

Append `--json` to any command for structured JSON output:

```bash
shl standings --json
shl teams --json
shl last --json
```

---

## Home Assistant Integration Example

If using in a Home Assistant custom component or automation script:

```python
from shl import AsyncSHLClient

async def async_update_shl_data(hass):
    async with AsyncSHLClient() as client:
        # Get favorite team upcoming game and standing
        standings = await client.get_standings()
        upcoming = await client.get_upcoming_games(team="FBK", limit=1)
        
        team_row = standings.get("FBK")
        next_game = upcoming[0] if upcoming else None
        
        return {
            "rank": team_row.rank,
            "points": team_row.points,
            "next_opponent": next_game.away_team.short_name if next_game else None,
            "next_game_time": next_game.start_date_time if next_game else None,
        }
```

---

## Development

All tasks are driven by [`just`](https://github.com/casey/just). Run `just` to list every recipe.

```bash
just install      # create .venv and install with [dev,cli] extras
just test         # offline unit tests
just test-live    # integration tests against www.shl.se
just cov          # coverage report (htmlcov/)
just fix          # ruff autofix + format
just check        # lint + format check + mypy + unit tests
just build        # build sdist + wheel into dist/
just check-dist   # twine check
just run standings --json   # run the CLI from the venv
just bump 0.2.0   # bump version
just release 0.2.0  # check, bump, commit and tag
just publish      # upload to PyPI (with confirmation)
just clean        # remove caches and build artifacts
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

