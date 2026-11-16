from datetime import UTC, date, datetime

import pytest
from conftest import FIXTURES, fixture

from aioespn import Scoreboard, Sport, State
from aioespn.scoreboard import Competitor


def scoreboard(name: str) -> Scoreboard:
    return Scoreboard.model_validate_json(fixture(name))


@pytest.mark.parametrize("name", sorted(path.name for path in FIXTURES.glob("scoreboard-*.json")))
def test_every_scoreboard_parses(name: str) -> None:
    board = scoreboard(name)

    assert board.events
    assert board.league is not None


BY_SPORT = {
    Sport.AUSTRALIAN_FOOTBALL: "scoreboard-australian-football-afl.json",
    Sport.BASEBALL: "scoreboard-baseball-mlb.json",
    Sport.BASKETBALL: "scoreboard-basketball-nba.json",
    Sport.FIELD_HOCKEY: "scoreboard-field-hockey-womens-college-field-hockey.json",
    Sport.FOOTBALL: "scoreboard-football-nfl.json",
    Sport.GOLF: "scoreboard-golf-pga.json",
    Sport.HOCKEY: "scoreboard-hockey-nhl.json",
    Sport.LACROSSE: "scoreboard-lacrosse-mens-college-lacrosse.json",
    Sport.MMA: "scoreboard-mma-ufc.json",
    Sport.RACING: "scoreboard-racing-f1.json",
    Sport.RUGBY: "scoreboard-rugby-180659.json",
    Sport.RUGBY_LEAGUE: "scoreboard-rugby-league-3.json",
    Sport.SOCCER: "scoreboard-soccer-eng.1.json",
    Sport.TENNIS: "scoreboard-tennis-atp.json",
    Sport.VOLLEYBALL: "scoreboard-volleyball-womens-college-volleyball.json",
    Sport.WATER_POLO: "scoreboard-water-polo-mens-college-water-polo.json",
}


def test_a_scoreboard_for_every_sport() -> None:
    assert set(BY_SPORT) == set(Sport)
    for name in BY_SPORT.values():
        assert (FIXTURES / name).is_file()


def test_a_finished_game() -> None:
    board = scoreboard("scoreboard-baseball-mlb.json")

    assert board.day is not None and board.day.date == date(2026, 10, 28)
    event = board.events[0]
    assert event.short_name == "MIL @ TB"
    assert event.date == datetime(2026, 10, 29, tzinfo=UTC)
    assert event.url == "https://www.espn.com/mlb/game/_/gameId/401908046/brewers-rays"
    assert event.status is not None
    assert event.status.state is State.POST and event.status.type.completed

    game = event.competition
    assert game is not None
    assert game.home is not None and game.away is not None
    assert (game.home.display_name, game.home.score, game.home.winner) == ("Tampa Bay Rays", "1", False)
    assert (game.away.display_name, game.away.score, game.away.winner) == ("Milwaukee Brewers", "4", True)
    assert game.away.record() == "103-59"
    assert len(game.away.linescores) == 9
    assert game.series is not None and game.series.summary == "MIL wins series 4-1"
    assert [note.headline for note in game.notes] == ["World Series - Game 5"]
    assert game.headlines and game.headlines[0].type == "Recap"
    assert game.venue is not None and game.venue.full_name == "Tropicana Field"


def test_scores_are_strings() -> None:
    game = scoreboard("scoreboard-football-nfl.json").events[0].competition

    assert game is not None
    assert [competitor.score for competitor in game.competitors] == ["21", "24"]


def test_a_week_of_football() -> None:
    board = scoreboard("scoreboard-football-nfl.json")

    assert board.week is not None and board.week.number == 10
    assert len(board.week.teams_on_bye) == 4
    assert board.season is not None and board.season.year == 2026 and board.season.type == 2
    upcoming = board.events[-1]
    assert upcoming.status is not None and upcoming.status.state is State.PRE
    assert upcoming.status.type.short_detail == "11/16 - 8:15 PM EST"
    assert upcoming.weather is not None and upcoming.weather.display_value == "Clear"
    game = upcoming.competition
    assert game is not None and game.odds and game.odds[0].details == "BAL -4.5"
    assert game.broadcasts[0].names == ("ESPN",)
    assert game.format is not None and game.format.regulation is not None and game.format.regulation.periods == 4


def test_a_live_basketball_game() -> None:
    event = scoreboard("scoreboard-basketball-nba-development-live.json").events[0]

    status = event.status
    assert status is not None
    assert status.state is State.IN
    assert (status.period, status.display_clock, status.type.short_detail) == (3, "9:49", "9:49 - 3rd")
    game = event.competition
    assert game is not None and game.situation is not None
    last_play = game.situation.last_play
    assert last_play is not None and last_play.text is not None
    assert last_play.text.startswith("Nimari Burnett makes 22-foot three point jumper")
    assert [competitor.score for competitor in game.competitors] == ["61", "74"]


def test_live_soccer_details() -> None:
    event = scoreboard("scoreboard-soccer-concacaf.nations.league-live.json").events[0]

    assert event.short_name == "GRN @ CUB"
    assert event.status is not None and event.status.type.name == "STATUS_SECOND_HALF"
    assert event.status.display_clock == "80'"
    game = event.competition
    assert game is not None
    goals = [detail for detail in game.details if detail.is_scoring]
    assert len(goals) == 7
    first = goals[0]
    assert first.type is not None and first.type.text == "Goal"
    assert first.clock is not None and first.clock.display_value == "5'"
    assert first.team is not None and first.team.id == game.competitors[0].id
    assert [p.athlete.display_name for p in first.participants] == ["Eloy Nebreda Martinez"]
    assert any(detail.yellow_card for detail in game.details)


def test_college_groups() -> None:
    board = scoreboard("scoreboard-basketball-mens-college-basketball-groups-50.json")

    assert len(board.events) == 3
    live = board.events[0].competition
    assert live is not None and live.status is not None and live.status.state is State.IN
    assert live.situation is not None and live.situation.last_play is not None


def test_college_rankings() -> None:
    game = scoreboard("scoreboard-lacrosse-mens-college-lacrosse.json").events[0].competition

    assert game is not None
    assert [(c.short_display_name, c.ranking) for c in game.competitors] == [("Princeton", 1), ("Notre Dame", 2)]
    unranked = scoreboard("scoreboard-football-nfl.json").events[0].competition
    assert unranked is not None and all(c.ranking is None for c in unranked.competitors)


def test_golf() -> None:
    event = scoreboard("scoreboard-golf-pga.json").events[0]

    assert event.end_date is not None and event.end_date > event.date
    assert event.status is not None and event.status.clock is None and event.status.type.detail is None
    field = event.competition
    assert field is not None and field.status is not None and field.status.period == 4
    leader = field.competitors[0]
    assert (leader.type, leader.order, leader.display_name, leader.short_display_name) == (
        "athlete",
        1,
        "Chad Ramey",
        "C. Ramey",
    )
    assert leader.team is None and leader.athlete is not None
    assert [c.score for c in field.competitors[:3]] == ["-19", "-17", "-16"]
    first_round = leader.linescores[0]
    assert (first_round.period, first_round.value, first_round.display_value) == (1, 68.0, "-4")
    assert len(first_round.linescores) == 18


def test_tennis_groupings() -> None:
    event = scoreboard("scoreboard-tennis-atp.json").events[0]

    assert event.competitions == ()
    assert [grouping.slug for grouping in event.groupings] == ["mens-doubles", "mens-singles"]
    assert len(event.all_competitions) == 6
    assert event.venue is not None and event.venue.full_name == "Inalpi Arena, Turin, Italy"

    doubles = event.groupings[0].competitions[0]
    assert doubles.round is not None and doubles.round.display_name == "Group Stage"
    assert doubles.tournament_id == 339
    pair = doubles.competitors[0]
    assert pair.type == "team" and pair.team is None and pair.roster is not None
    assert pair.display_name == "Orlando Luz / Rafael Matos"
    assert pair.short_display_name == "O. Luz / R. Matos"
    assert [a.display_name for a in pair.roster.athletes] == ["Orlando Luz", "Rafael Matos"]
    assert [(s.value, s.winner, s.tiebreak) for s in pair.linescores] == [
        (3, False, None),
        (7, True, None),
        (0, False, 4),
    ]
    assert pair.score is None and pair.ranking == 8

    singles = event.groupings[1].competitions[0]
    assert singles.status is not None and singles.status.state is State.IN
    assert singles.type is not None and singles.type.text == "Men's Singles"
    player = singles.competitors[0]
    assert player.athlete is not None and player.athlete.flag is not None and player.athlete.flag.alt == "Italy"
    assert player.display_name == "Flavio Cobolli"


def test_racing_sessions() -> None:
    finished, upcoming = scoreboard("scoreboard-racing-f1.json").events

    assert finished.circuit is not None and finished.circuit.full_name is not None
    sessions = [c.type.abbreviation for c in finished.competitions if c.type is not None]
    assert sessions == ["FP1", "FP2", "FP3", "Qual", "Race"]
    race = finished.competitions[-1]
    winner = race.competitors[0]
    assert (winner.order, winner.winner, winner.display_name, winner.score) == (1, True, "Lando Norris", None)
    assert all(not session.competitors for session in upcoming.competitions)


def test_an_mma_card() -> None:
    card = scoreboard("scoreboard-mma-ufc.json").events[0]

    assert card.name == "UFC 334: Gane vs. Hokit"
    assert card.venues and card.venues[0].full_name == "Madison Square Garden"
    main_event = card.competitions[-1]
    assert main_event.type is not None and main_event.type.abbreviation == "Heavyweight"
    winner = next(c for c in main_event.competitors if c.winner)
    assert winner.display_name == "Ciryl Gane" and winner.score is None
    assert winner.record() == "15-2-0"
    assert main_event.details and main_event.details[0].type is not None


def test_a_defunct_mma_promotion() -> None:
    event = scoreboard("scoreboard-mma-affliction.json").events[0]

    assert event.status is None and event.competitions == ()
    assert event.current_status is None and event.competition is None
    assert event.venues[0].full_name == "Honda Center"


def test_rugby_details() -> None:
    game = scoreboard("scoreboard-rugby-180659.json").events[0].competition

    assert game is not None
    try_ = game.details[0]
    assert try_.type is not None and try_.type.text == "try"
    assert [p.athlete.name for p in try_.participants] == ["Jamie Osborne"]
    assert game.home is not None and game.home.form == "WWLWW"


def test_two_kinds_of_record() -> None:
    # Some college scoreboards give a team's overall record twice: as "records", and as a bare "record" string.
    competitor = Competitor.model_validate({"id": "1", "record": "1-2"})

    assert competitor.record() == "1-2"
    assert competitor.display_name == "1"


def test_soccer_odds_with_nulls() -> None:
    event = {"id": "1", "date": "2026-11-16T19:00Z", "name": "A at B", "shortName": "A @ B"}
    board = Scoreboard.model_validate(
        {"events": [{**event, "competitions": [{"id": "1", "odds": [None, {"details": "B -1.5"}]}]}]}
    )

    game = board.events[0].competition
    assert game is not None and [odds.details for odds in game.odds] == ["B -1.5"]
