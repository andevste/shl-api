"""Unit tests for SHL data models."""

from shl.models import (
    Article,
    Game,
    Standings,
    Team,
)


def test_team_from_dict():
    sample = {
        "uuid": "752c-752c12zB7Z",
        "teamCode": "FBK",
        "name": "Färjestad BK",
        "logo": "https://sportality.cdn.s8y.se/team-logos/fbk1_fbk.svg",
        "publicUrl": "http://www.farjestadbk.se/",
        "ownerInstanceId": "fbk1_fbk",
        "teamNames": {
            "code": "FBK",
            "short": "Färjestad",
            "long": "Färjestad BK",
            "full": "Färjestad Bollklubb",
        },
        "teamInfo": {
            "founded": "1932",
            "golds": "10 st",
            "finals": "21 st",
            "address": "Färjestad BK, Box 318",
            "phone": "054-22 33 00",
            "email": "info@farjestadsbk.se",
            "twitter": "https://twitter.com/farjestad_bk",
        },
        "series": [{"code": "SHL"}],
    }

    team = Team.from_dict(sample)
    assert team.code == "FBK"
    assert team.name == "Färjestad BK"
    assert team.short_name == "Färjestad"
    assert team.full_name == "Färjestad Bollklubb"
    assert team.founded == "1932"
    assert team.golds == "10 st"
    assert team.instance_id == "fbk1_fbk"
    assert team.series_codes == ["SHL"]
    assert team.social_media.get("twitter") == "https://twitter.com/farjestad_bk"


def test_game_states_and_summary():
    data = {
        "uuid": "g123",
        "startDateTime": "2026-10-08T17:00:00.000Z",
        "state": "post-game",
        "overtime": True,
        "shootout": False,
        "homeTeamInfo": {
            "code": "LHF",
            "names": {"short": "Luleå"},
            "score": 3,
            "status": "WIN",
        },
        "awayTeamInfo": {
            "code": "FBK",
            "names": {"short": "Färjestad"},
            "score": 2,
            "status": "LOSE",
        },
        "venueInfo": {"name": "Coop Arena"},
    }

    game = Game.from_dict(data)
    assert game.uuid == "g123"
    assert game.is_finished is True
    assert game.is_live is False
    assert game.is_upcoming is False
    assert game.winner_code == "LHF"
    assert game.home_team.score == 3
    assert game.away_team.score == 2
    assert "LHF 3 - 2 FBK (OT)" in game.summary
    assert game.venue_name == "Coop Arena"


def test_standings_lookup():
    data = {
        "leagueStandings": [
            {
                "Rank": 1,
                "GP": 7,
                "W": 6,
                "OTW": 0,
                "OTL": 1,
                "L": 0,
                "G": 28,
                "GA": 6,
                "Diff": 22,
                "Points": 19,
                "info": {
                    "teamId": "FBK",
                    "code": "Färjestad",
                    "teamInfo": {
                        "siteTeamDisplayName": "Färjestad BK",
                        "teamUuid": "752c",
                    },
                },
            },
            {
                "Rank": 2,
                "GP": 7,
                "W": 5,
                "OTW": 1,
                "OTL": 0,
                "L": 1,
                "G": 24,
                "GA": 17,
                "Diff": 7,
                "Points": 17,
                "info": {
                    "teamId": "FHC",
                    "code": "Frölunda",
                    "teamInfo": {
                        "siteTeamDisplayName": "Frölunda HC",
                        "teamUuid": "087a",
                    },
                },
            },
        ]
    }

    standings = Standings.from_dict(data)
    assert len(standings) == 2
    first = standings[0]
    assert first.rank == 1
    assert first.team_code == "FBK"
    assert first.points == 19

    # Test lookup by code and name
    by_code = standings.get("FBK")
    assert by_code is not None
    assert by_code.team_code == "FBK"

    by_name = standings.get("frölunda hc")
    assert by_name is not None
    assert by_name.team_code == "FHC"

    assert standings.get("NONEXISTENT") is None


def test_article_from_dict():
    data = {
        "id": "art-1",
        "header": "Victory for Färjestad",
        "intro": "Great match yesterday.",
        "publishedAt": "2026-10-09T12:00:00.000Z",
        "author": {"name": "Hockey Reporter"},
    }

    article = Article.from_dict(data)
    assert article.id == "art-1"
    assert article.header == "Victory for Färjestad"
    assert article.author == "Hockey Reporter"
    assert article.published_at is not None
