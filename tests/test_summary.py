from datetime import UTC, datetime

import pytest
from conftest import FIXTURES, fixture

from aioespn import Play, State, Summary


def summary(name: str) -> Summary:
    return Summary.model_validate_json(fixture(name))


@pytest.mark.parametrize("name", sorted(path.name for path in FIXTURES.glob("summary-*.json")))
def test_every_summary_parses(name: str) -> None:
    game = summary(name).competition

    assert game is not None
    assert len(game.competitors) == 2
    assert game.status is not None


def test_football_scoring_plays_and_drives() -> None:
    nfl = summary("summary-football-nfl.json")

    assert nfl.header.week == 10
    assert nfl.header.url == "https://www.espn.com/nfl/game/_/gameId/401873064/steelers-bengals"
    assert nfl.plays == () and nfl.key_events == ()
    assert nfl.scoring_summary == nfl.scoring_plays
    field_goal, touchdown = nfl.scoring_plays[:2]
    assert field_goal.text == "Evan McPherson 24 Yd Field Goal"
    assert field_goal.scoring_type is not None and field_goal.scoring_type.display_name == "Field Goal"
    assert (field_goal.away_score, field_goal.home_score) == (0, 3)
    assert field_goal.period is not None and field_goal.period.number == 1
    assert field_goal.clock is not None and field_goal.clock.display_value == "8:56"
    assert field_goal.team is not None and field_goal.team.display_name == "Cincinnati Bengals"
    assert touchdown.scoring_type is not None and touchdown.scoring_type.display_name == "Touchdown"

    assert nfl.drives is not None
    drive = nfl.drives.previous[0]
    assert (drive.description, drive.result, drive.display_result) == ("13 plays, 80 yards, 6:04", "FG", "Field Goal")
    assert drive.team is not None and drive.team.display_name == "Cincinnati Bengals"
    assert nfl.all_plays == tuple(play for drive in nfl.drives.previous for play in drive.plays)
    assert nfl.all_plays[0].wallclock == datetime(2026, 11, 16, 1, 22, 31, tzinfo=UTC)


def test_basketball_play_by_play() -> None:
    nba = summary("summary-basketball-nba.json")

    assert nba.all_plays == nba.plays
    scoring = nba.scoring_summary
    assert scoring and all(play.scoring_play for play in scoring)
    three = scoring[0]
    assert three.score_value == 3 and (three.away_score, three.home_score) == (3, 0)
    # Basketball's plays name their athletes by ID alone.
    assert three.participants[0].athlete.id == "4900671" and three.participants[0].athlete.name is None
    end = nba.plays[-1]
    assert end.text == "End of Game"
    assert (end.away_score, end.home_score) == (125, 103)
    game = nba.competition
    assert game is not None and game.status is not None and game.status.state is State.POST
    assert [(c.display_name, c.score) for c in game.competitors] == [
        ("Sacramento Kings", "103"),
        ("Oklahoma City Thunder", "125"),
    ]


def test_hockey_goals() -> None:
    nhl = summary("summary-hockey-nhl.json")

    goals = nhl.scoring_summary
    assert len(goals) == 6
    goal = goals[0]
    assert goal.type is not None and goal.type.text == "Goal"
    assert [(p.athlete.display_name, p.type) for p in goal.participants] == [
        ("Will Smith", "scorer"),
        ("Ivar Stenberg", "assister"),
        ("Macklin Celebrini", "assister"),
    ]
    assert nhl.game_info is not None and nhl.game_info.officials[0].position == "Referee"


def test_hockey_penalty() -> None:
    # A play from a live game's summary, as ESPN served it on 2026-11-17, without its coordinates and headshots.
    penalty = Play.model_validate_json("""{"id": "401892726000003490", "sequenceNumber": "95",
            "type": {"id": "55", "text": "Tripping", "abbreviation": "Tripping", "penaltyMinutes": "2",
                     "penaltyType": "Minor"},
            "text": "Jacob Fowler Tripping against Gabe Perreault served by Cole Caufield",
            "awayScore": 0, "homeScore": 0, "period": {"number": 1, "displayValue": "1st"},
            "clock": {"displayValue": "18:36"}, "scoringPlay": false, "scoreValue": 0, "team": {"id": "10"},
            "participants": [{"athlete": {"id": "5188437", "displayName": "Jacob Fowler"}},
                             {"athlete": {"id": "5149204", "displayName": "Gabe Perreault"}}],
            "wallclock": "2026-11-17T01:24:09Z"}""")
    assert penalty.type is not None
    assert (penalty.type.penalty_type, penalty.type.penalty_minutes) == ("Minor", 2)
    assert penalty.type.is_penalty and not penalty.is_scoring
    # Other plays aren't penalties.
    goal = summary("summary-hockey-nhl.json").scoring_summary[0]
    assert goal.type is not None and not goal.type.is_penalty


def test_baseball() -> None:
    mlb = summary("summary-baseball-mlb.json")

    assert mlb.header.game_note == "World Series - Game 5"
    runs = mlb.scoring_summary
    assert len(runs) == 5
    assert runs[0].period is not None and (runs[0].period.type, runs[0].period.number) == ("Top", 2)
    assert [p.type for p in runs[0].participants][:2] == ["pitcher", "batter"]
    assert mlb.game_info is not None and mlb.game_info.attendance == 40489


def test_soccer_key_events_and_commentary() -> None:
    soccer = summary("summary-soccer-eng.1.json")

    goals = soccer.scoring_summary
    assert len(goals) == 8
    goal = goals[0]
    assert goal.type is not None and goal.type.type == "goal"
    assert goal.short_text == "Alysson Goal"
    assert goal.clock is not None and goal.clock.display_value == "1'"
    assert goal.team is not None and goal.team.display_name == "Aston Villa"
    assert [p.athlete.display_name for p in goal.participants] == ["Alysson", "John McGinn"]
    # Soccer's key events carry no score.
    assert goal.away_score is None and goal.home_score is None
    assert soccer.all_plays == soccer.key_events
    assert soccer.commentary[0].text == "Lineups are announced and players are warming up."
    game = soccer.competition
    assert game is not None and len(game.details) == 8
    assert game.status is not None and game.status.type.name == "STATUS_FULL_TIME"
    assert soccer.boxscore is not None
    fouls = soccer.boxscore.teams[0].statistics[0]
    assert (fouls.label, fouls.display_value) == ("Fouls", "18")


def test_a_live_soccer_game() -> None:
    live = summary("summary-soccer-concacaf.nations.league-live.json")

    game = live.competition
    assert game is not None and game.status is not None
    assert game.status.state is State.IN
    assert (game.status.period, game.status.display_clock) == (2, "79'")
    assert len(live.scoring_summary) == 7
    assert [c.score for c in game.competitors] == ["7", "0"]


def test_australian_rules_scores_by_change() -> None:
    afl = summary("summary-australian-football-afl.json")

    # Australian rules plays don't say whether they scored, and all of them did.
    assert all(play.scoring_play is None for play in afl.plays)
    assert afl.scoring_summary == afl.plays
    assert afl.header.game_note == "GF - Dockers vs Lions"


def test_rugby_details() -> None:
    rugby = summary("summary-rugby-270559.json")

    game = rugby.competition
    assert game is not None
    try_ = game.details[0]
    assert try_.type is not None and try_.type.text == "try"
    assert (try_.away_score, try_.home_score) == (0, 5)
    assert try_.team is not None and try_.team.display_name == "La Rochelle"
    assert rugby.scoring_summary == () and rugby.all_plays == ()
