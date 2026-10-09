"""Command Line Interface (CLI) for the SHL API."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, List

try:
    from rich.console import Console
    from rich.table import Table

    HAVE_RICH = True
except ImportError:
    HAVE_RICH = False

from .client import SHLClient
from .exceptions import SHLError
from .models import Game


def _dump_json(data: Any) -> None:
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def cmd_teams(client: SHLClient, args: argparse.Namespace) -> None:
    """List all SHL teams."""
    teams = client.get_teams()
    if args.json:
        _dump_json(
            [
                {
                    "code": t.code,
                    "name": t.name,
                    "short_name": t.short_name,
                    "full_name": t.full_name,
                    "uuid": t.uuid,
                    "instance_id": t.instance_id,
                    "founded": t.founded,
                    "golds": t.golds,
                    "address": t.address,
                    "website": t.public_url,
                    "logo": t.logo_url,
                }
                for t in teams
            ]
        )
        return

    if HAVE_RICH:
        console = Console()
        table = Table(title="Swedish Hockey League (SHL) Teams", show_header=True)
        table.add_column("Code", style="cyan", no_wrap=True)
        table.add_column("Team Name", style="bold")
        table.add_column("Full Club Name", style="dim")
        table.add_column("Founded", style="green")
        table.add_column("Championships (Guld)", style="yellow")
        for t in teams:
            golds_str = t.golds.split(" ")[0] if t.golds else "-"
            table.add_row(t.code, t.name, t.full_name, t.founded or "-", golds_str)
        console.print(table)
    else:
        print(f"{'CODE':<6} {'NAME':<24} {'FOUNDED':<10} {'GOLDS'}")
        print("-" * 55)
        for t in teams:
            golds_str = t.golds.split(" ")[0] if t.golds else "-"
            print(f"{t.code:<6} {t.name:<24} {str(t.founded or '-'):<10} {golds_str}")


def cmd_team(client: SHLClient, args: argparse.Namespace) -> None:
    """Show details for a specific team."""
    team = client.get_team(args.identifier)
    if not team:
        print(f"Error: Team '{args.identifier}' not found.", file=sys.stderr)
        sys.exit(1)

    if args.json:
        _dump_json(team.raw_data)
        return

    if HAVE_RICH:
        console = Console()
        table = Table(title=f"Team Profile: {team.name} ({team.code})", show_header=False)
        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value")
        table.add_row("Code", team.code)
        table.add_row("Short Name", team.short_name)
        table.add_row("Full Name", team.full_name)
        table.add_row("Founded", team.founded or "-")
        table.add_row("Championships", team.golds or "-")
        table.add_row("Finals", team.finals or "-")
        table.add_row("Retired Numbers", (team.retired_numbers or "-").replace("\r", ""))
        table.add_row("Address", (team.address or "-").replace("\r", " "))
        table.add_row("Phone", team.phone or "-")
        table.add_row("Email", team.email or "-")
        table.add_row("Website", team.public_url or "-")
        table.add_row("Logo URL", team.logo_url or "-")
        table.add_row("UUID", team.uuid)
        console.print(table)
    else:
        print(f"Team: {team.name} ({team.code})")
        print(f"Full name: {team.full_name}")
        print(f"Founded:   {team.founded or '-'}")
        print(f"Golds:     {team.golds or '-'}")
        print(f"Address:   {team.address or '-'}")
        print(f"Website:   {team.public_url or '-'}")
        print(f"UUID:      {team.uuid}")


def cmd_standings(client: SHLClient, args: argparse.Namespace) -> None:
    """Show current league standings."""
    standings = client.get_standings()
    if args.json:
        _dump_json(
            [
                {
                    "rank": r.rank,
                    "team_code": r.team_code,
                    "team_name": r.team_name,
                    "team_uuid": r.team_uuid,
                    "games_played": r.games_played,
                    "wins": r.wins,
                    "ot_wins": r.ot_wins,
                    "losses": r.losses,
                    "ot_losses": r.ot_losses,
                    "goals_for": r.goals_for,
                    "goals_against": r.goals_against,
                    "goal_diff": r.goal_diff,
                    "points": r.points,
                }
                for r in standings
            ]
        )
        return

    if HAVE_RICH:
        console = Console()
        table = Table(title="SHL Standings (Tabell)", show_header=True)
        table.add_column("#", justify="right", style="cyan")
        table.add_column("Team", style="bold")
        table.add_column("GP", justify="right")
        table.add_column("W", justify="right")
        table.add_column("OTW", justify="right")
        table.add_column("OTL", justify="right")
        table.add_column("L", justify="right")
        table.add_column("+/-", justify="right")
        table.add_column("Diff", justify="right")
        table.add_column("PTS", justify="right", style="bold green")

        for r in standings:
            diff_str = f"+{r.goal_diff}" if r.goal_diff > 0 else str(r.goal_diff)
            gf_ga = f"{r.goals_for}:{r.goals_against}"
            table.add_row(
                str(r.rank),
                f"{r.team_name} ({r.team_code})",
                str(r.games_played),
                str(r.wins),
                str(r.ot_wins),
                str(r.ot_losses),
                str(r.losses),
                gf_ga,
                diff_str,
                str(r.points),
            )
        console.print(table)
    else:
        print(f"{'#':<3} {'TEAM':<24} {'GP':<4} {'W':<3} {'OTW':<4} {'OTL':<4} {'L':<3} {'DIFF':<6} {'PTS'}")
        print("-" * 65)
        for r in standings:
            diff_str = f"+{r.goal_diff}" if r.goal_diff > 0 else str(r.goal_diff)
            print(
                f"{r.rank:<3} {r.team_name + ' (' + r.team_code + ')':<24} "
                f"{r.games_played:<4} {r.wins:<3} {r.ot_wins:<4} {r.ot_losses:<4} {r.losses:<3} "
                f"{diff_str:<6} {r.points}"
            )


def _print_games(games: List[Game], title: str, json_mode: bool) -> None:
    """Helper to display games."""
    if json_mode:
        _dump_json(
            [
                {
                    "uuid": g.uuid,
                    "start_time": g.start_date_time_str,
                    "state": g.state,
                    "home_team": {
                        "code": g.home_team.code,
                        "name": g.home_team.short_name,
                        "score": g.home_team.score,
                        "status": g.home_team.status,
                    },
                    "away_team": {
                        "code": g.away_team.code,
                        "name": g.away_team.short_name,
                        "score": g.away_team.score,
                        "status": g.away_team.status,
                    },
                    "arena": g.venue_name,
                    "overtime": g.overtime,
                    "shootout": g.shootout,
                }
                for g in games
            ]
        )
        return

    if not games:
        print(f"No games found for: {title}")
        return

    if HAVE_RICH:
        console = Console()
        table = Table(title=title, show_header=True)
        table.add_column("Start Time", style="cyan")
        table.add_column("Home", justify="right", style="bold")
        table.add_column("Score", justify="center", style="yellow")
        table.add_column("Away", justify="left", style="bold")
        table.add_column("State", style="dim")
        table.add_column("Arena")

        for g in games:
            dt_display = g.start_date_time_str[:16].replace("T", " ") if g.start_date_time_str else "-"
            h_score = str(g.home_team.score) if g.home_team.score is not None else "-"
            a_score = str(g.away_team.score) if g.away_team.score is not None else "-"
            score_str = f"{h_score} - {a_score}"
            if g.shootout:
                score_str += " (SO)"
            elif g.overtime:
                score_str += " (OT)"

            table.add_row(
                dt_display,
                f"{g.home_team.short_name} ({g.home_team.code})",
                score_str,
                f"{g.away_team.short_name} ({g.away_team.code})",
                g.state,
                g.venue_name or "-",
            )
        console.print(table)
    else:
        print(title)
        print("-" * 75)
        for g in games:
            print(f"[{g.start_date_time_str or '-'}] {g.summary} | {g.venue_name or '-'}")


def cmd_last(client: SHLClient, args: argparse.Namespace) -> None:
    """Show last game day results."""
    day = client.get_last_game_day()
    _print_games(day.games, f"Last Played Games ({day.date})", args.json)


def cmd_next(client: SHLClient, args: argparse.Namespace) -> None:
    """Show next game day schedule."""
    day = client.get_next_game_day()
    _print_games(day.games, f"Next Upcoming Games ({day.date})", args.json)


def cmd_today(client: SHLClient, args: argparse.Namespace) -> None:
    """Show games scheduled for today."""
    games = client.get_today_games()
    _print_games(games, "Games Today", args.json)


def cmd_games(client: SHLClient, args: argparse.Namespace) -> None:
    """Show upcoming or scheduled games."""
    if args.upcoming:
        games = client.get_upcoming_games(team=args.team, limit=args.limit)
        title = f"Upcoming Games (Team: {args.team})" if args.team else "Upcoming Games"
    else:
        games = client.get_schedule(team=args.team, played=args.played)
        if args.limit:
            games = games[: args.limit]
        title = f"Schedule (Team: {args.team})" if args.team else "Schedule"
    _print_games(games, title, args.json)


def cmd_game(client: SHLClient, args: argparse.Namespace) -> None:
    """Show details of a specific game."""
    game = client.get_game(args.game_uuid)
    if args.json:
        _dump_json(game.raw_data)
        return
    _print_games([game], f"Game Details: {game.uuid}", False)


def cmd_news(client: SHLClient, args: argparse.Namespace) -> None:
    """Show latest SHL news articles."""
    articles = client.get_news(limit=args.limit)
    if args.json:
        _dump_json(
            [
                {
                    "id": a.id,
                    "header": a.header,
                    "intro": a.intro,
                    "published_at": a.published_at,
                    "author": a.author,
                    "image_url": a.image_url,
                }
                for a in articles
            ]
        )
        return

    print(f"Latest SHL News ({len(articles)} articles)")
    print("-" * 75)
    for a in articles:
        date_str = str(a.published_at)[:16] if a.published_at else ""
        print(f"• {a.header}")
        if a.intro:
            print(f"  {a.intro[:120]}...")
        print(f"  Date: {date_str} | ID: {a.id}")
        print()


def cmd_settings(client: SHLClient, args: argparse.Namespace) -> None:
    """Show site settings and league status."""
    settings = client.get_site_settings()
    if args.json:
        _dump_json(settings.raw_data)
        return

    print(f"League:       {settings.name}")
    print(f"Instance ID:  {settings.instance_id}")
    print(f"Sport:        {settings.sport}")
    print(f"Country:      {settings.country}")
    print(f"Total Teams:  {len(settings.teams)}")
    print(f"Logo:         {settings.logo_url}")
    print(f"Feature Flags ({len(settings.feature_flags)}):")
    for k, v in list(settings.feature_flags.items())[:8]:
        print(f"  - {k}: {v}")


def main() -> None:
    """CLI entrypoint."""
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("--json", action="store_true", help="Output raw JSON format")

    parser = argparse.ArgumentParser(
        prog="shl",
        description="Swedish Hockey League (SHL) Command Line Interface",
        parents=[common_parser],
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # teams
    subparsers.add_parser("teams", parents=[common_parser], help="List all SHL teams")

    # team <identifier>
    p_team = subparsers.add_parser("team", parents=[common_parser], help="Show info for a specific team")
    p_team.add_argument("identifier", help="Team code (e.g. 'FBK'), name, or UUID")

    # standings
    subparsers.add_parser("standings", parents=[common_parser], help="Show league standings (tabell)")

    # last
    subparsers.add_parser("last", parents=[common_parser], help="Show results from the last played game day")

    # next
    subparsers.add_parser("next", parents=[common_parser], help="Show schedule for the next upcoming game day")

    # today
    subparsers.add_parser("today", parents=[common_parser], help="Show games scheduled for today")

    # games
    p_games = subparsers.add_parser("games", parents=[common_parser], help="Show games / schedule")
    p_games.add_argument("--team", help="Filter by team code (e.g. 'FBK')")
    p_games.add_argument("--upcoming", action="store_true", help="Show upcoming games only")
    p_games.add_argument("--played", action="store_true", help="Show played games only")
    p_games.add_argument("--limit", type=int, default=15, help="Maximum number of games to show")

    # game <uuid>
    p_game = subparsers.add_parser("game", parents=[common_parser], help="Show details for a specific game by UUID")
    p_game.add_argument("game_uuid", help="Game UUID")

    # news
    p_news = subparsers.add_parser("news", parents=[common_parser], help="Show latest SHL news")
    p_news.add_argument("--limit", type=int, default=5, help="Number of articles to fetch")

    # settings
    subparsers.add_parser("settings", parents=[common_parser], help="Show site settings and league metadata")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    try:
        with SHLClient() as client:
            cmd_map = {
                "teams": cmd_teams,
                "team": cmd_team,
                "standings": cmd_standings,
                "last": cmd_last,
                "next": cmd_next,
                "today": cmd_today,
                "games": cmd_games,
                "game": cmd_game,
                "news": cmd_news,
                "settings": cmd_settings,
            }
            handler = cmd_map.get(args.command)
            if handler:
                handler(client, args)
            else:
                parser.print_help()
    except SHLError as e:
        print(f"SHL API Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
