"""Unit tests for the CLI commands."""

import argparse
from unittest.mock import MagicMock

from shl.cli import cmd_standings, cmd_teams
from shl.models import StandingRow, Standings, Team


def test_cmd_teams_json(capsys):
    client = MagicMock()
    client.get_teams.return_value = [
        Team(
            uuid="u1",
            code="FBK",
            name="Färjestad BK",
            short_name="Färjestad",
            long_name="Färjestad BK",
            full_name="Färjestad Bollklubb",
            logo_url="https://logo.png",
            icon_url="https://logo.png",
            public_url="https://fbk.se",
            instance_id="fbk1_fbk",
        )
    ]
    args = argparse.Namespace(json=True)
    cmd_teams(client, args)
    captured = capsys.readouterr()
    assert '"code": "FBK"' in captured.out


def test_cmd_standings_json(capsys):
    client = MagicMock()
    client.get_standings.return_value = Standings(
        rows=[
            StandingRow(
                rank=1,
                team_code="FBK",
                team_name="Färjestad",
                team_uuid="u1",
                games_played=7,
                wins=6,
                ot_wins=0,
                losses=0,
                ot_losses=1,
                goals_for=28,
                goals_against=6,
                goal_diff=22,
                points=19,
            )
        ]
    )
    args = argparse.Namespace(json=True)
    cmd_standings(client, args)
    captured = capsys.readouterr()
    assert '"team_code": "FBK"' in captured.out
    assert '"points": 19' in captured.out
