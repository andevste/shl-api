"""Integration tests against live SHL API."""

import pytest

from shl import SHLClient

pytestmark = pytest.mark.live


@pytest.fixture(scope="module")
def client():
    with SHLClient() as c:
        yield c


def test_live_get_site_settings(client):
    settings = client.get_site_settings()
    assert settings.name == "SHL"
    assert len(settings.teams) >= 14
    assert settings.country == "se"


def test_live_get_teams(client):
    teams = client.get_teams()
    assert len(teams) >= 14
    codes = [t.code for t in teams]
    assert "FBK" in codes
    assert "LHF" in codes
    assert "FHC" in codes


def test_live_get_standings(client):
    standings = client.get_standings()
    assert len(standings) == 14
    assert standings[0].rank == 1
    assert standings[0].points >= standings[-1].points


def test_live_get_last_game_day(client):
    last_day = client.get_last_game_day()
    assert last_day.date != ""
    assert len(last_day) > 0
    game = last_day[0]
    assert game.home_team.code != ""
    assert game.away_team.code != ""


def test_live_get_next_game_day(client):
    next_day = client.get_next_game_day()
    assert next_day.date != ""
    assert len(next_day) > 0


def test_live_get_schedule(client):
    schedule = client.get_schedule(limit=10)
    assert len(schedule) > 0


def test_live_get_news(client):
    news = client.get_news(limit=3)
    assert len(news) == 3
    assert news[0].header != ""
