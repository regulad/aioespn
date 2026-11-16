from datetime import UTC, datetime

from conftest import fixture

from aioespn import News, Standings, Team, TeamSchedule
from aioespn.rankings import _RankingsFeed
from aioespn.sports import _LeaguesFeed
from aioespn.teams import _TeamFeed, _TeamsFeed


def test_leagues() -> None:
    soccer = _LeaguesFeed.model_validate_json(fixture("leagues-soccer.json")).leagues

    premier_league = next(league for league in soccer if league.slug == "eng.1")
    assert (premier_league.name, premier_league.abbreviation) == ("English Premier League", "Premier League")
    assert premier_league.has_standings
    assert premier_league.url == "https://www.espn.com/soccer/league/_/name/eng.1"
    assert premier_league.logo_url is not None

    rugby = _LeaguesFeed.model_validate_json(fixture("leagues-rugby.json")).leagues
    assert len(rugby) == 18
    assert next(league.name for league in rugby if league.slug == "180659") == "Six Nations"


def test_teams() -> None:
    teams = _TeamsFeed.model_validate_json(fixture("teams-football-nfl.json")).teams

    cardinals = teams[0]
    assert (cardinals.id, cardinals.display_name, cardinals.abbreviation) == ("22", "Arizona Cardinals", "ARI")
    assert cardinals.color == "a40227"
    assert cardinals.logo_url == "https://a.espncdn.com/i/teamlogos/nfl/500/ari.png"
    assert cardinals.url == "https://www.espn.com/nfl/team/_/name/ari/arizona-cardinals"


def test_team_detail() -> None:
    team = _TeamFeed.model_validate_json(fixture("team-football-nfl.json")).team

    assert team.standing_summary == "4th in NFC West"
    assert (team.record_of(), team.record_of("home")) == ("3-7", "0-4")
    (last_game,) = team.next_event
    assert last_game.short_name == "LAR @ ARI"
    game = last_game.competition
    assert game is not None
    # Here a score comes as {"value": 6.0, "displayValue": "6"}.
    assert [(c.display_name, c.score, c.winner) for c in game.competitors] == [
        ("Arizona Cardinals", "6", False),
        ("Los Angeles Rams", "34", True),
    ]
    assert game.home is not None and game.home.record() == "3-7"


def test_team_schedule() -> None:
    schedule = TeamSchedule.model_validate_json(fixture("schedule-football-nfl.json"))

    assert schedule.team.record_summary == "3-7" and schedule.bye_week == 14
    opener = schedule.events[0]
    assert opener.status is None
    assert opener.current_status is not None and opener.current_status.type.name == "STATUS_FINAL"
    assert opener.week is not None and opener.week.text == "Week 1"
    game = opener.competition
    assert game is not None
    assert [(c.display_name, c.score) for c in game.competitors] == [
        ("Los Angeles Chargers", "14"),
        ("Arizona Cardinals", "26"),
    ]
    assert [(b.market, b.names) for b in game.broadcasts] == [("national", ("CBS",))]


def test_standings_by_conference_and_division() -> None:
    standings = Standings.model_validate_json(fixture("standings-football-nfl.json"))

    assert standings.name == "National Football League"
    assert standings.season is not None and standings.season.year == 2026
    assert [conference.name for conference in standings.children] == [
        "American Football Conference",
        "National Football Conference",
    ]
    assert standings.entries == ()
    divisions = list(standings.tables())
    assert [division.name for division in divisions] == ["AFC East", "AFC North", "NFC East", "NFC North"]
    bills = divisions[0].entries[0]
    assert bills.display_name == "Buffalo Bills"
    wins, streak = bills.stat("wins"), bills.stat("streak")
    assert wins is not None and (wins.value, wins.display_value) == (8.0, "8")
    assert streak is not None and streak.display_value == "W5"
    assert bills.stat("goals") is None


def test_soccer_table() -> None:
    standings = Standings.model_validate_json(fixture("standings-soccer-eng.1.json"))

    (table,) = standings.tables()
    arsenal = table.entries[0]
    points = arsenal.stat("points")
    assert points is not None and points.display_value == "27"
    assert arsenal.note is not None and arsenal.note.description == "Champions League"


def test_drivers_standings() -> None:
    standings = Standings.model_validate_json(fixture("standings-racing-f1.json"))

    drivers, constructors = standings.tables()
    assert drivers.name == "Driver Standings" and constructors.name == "Constructor Standings"
    leader = drivers.entries[0]
    assert leader.team is None and leader.display_name == "Kimi Antonelli"
    points = leader.stat("championshipPts")
    assert points is not None and points.display_value == "390"


def test_no_standings() -> None:
    standings = Standings.model_validate_json(fixture("standings-golf-pga.json"))

    assert standings.children == () and list(standings.tables()) == []


def test_news() -> None:
    news = News.model_validate_json(fixture("news-football-nfl.json"))

    assert news.header == "NFL News"
    story = news.articles[1]
    assert story.type == "HeadlineNews" and story.byline == "Kevin Seifert"
    assert story.url == "https://www.espn.com/nfl/story/_/id/50503437/vikings-wr-jordan-addison-needs-thumb-surgery"
    assert story.published == datetime(2026, 11, 16, 19, 56, 9, tzinfo=UTC)
    assert story.image_url is not None
    assert News.model_validate_json(fixture("news-rugby-270559.json")).articles == ()


def test_college_polls() -> None:
    polls = _RankingsFeed.model_validate_json(fixture("rankings-football-college-football.json")).rankings

    ap = polls[0]
    assert (ap.name, ap.short_name) == ("AP Top 25", "AP Poll")
    first = ap.ranks[0]
    assert (first.current, first.previous, first.points, first.first_place_votes) == (1, 1, 1734.0, 58)
    # Rankings name teams without a display name; it's made from the place and name.
    assert first.display_name == "Georgia Bulldogs" and first.record_summary == "9-1"
    assert len(ap.others) == 2


def test_athlete_rankings() -> None:
    (atp,) = _RankingsFeed.model_validate_json(fixture("rankings-tennis-atp.json")).rankings
    assert [rank.display_name for rank in atp.ranks] == ["Alexander Zverev", "Jannik Sinner", "Carlos Alcaraz"]

    (pound_for_pound,) = _RankingsFeed.model_validate_json(fixture("rankings-mma-ufc.json")).rankings
    usman = pound_for_pound.ranks[0].athlete
    # Rankings give a flag as its bare URL, and spell shortName in lower case.
    assert usman is not None and usman.flag is not None and usman.flag.href.endswith("ngr.png")
    assert usman.short_name == "K. Usman"


def test_team_display_name_from_its_parts() -> None:
    assert (
        Team.model_validate({"id": "61", "location": "Georgia", "name": "Bulldogs"}).display_name == "Georgia Bulldogs"
    )
    assert Team.model_validate({"id": "61", "abbreviation": "UGA"}).display_name == "UGA"
    assert Team(id="1", display_name="Given").display_name == "Given"
