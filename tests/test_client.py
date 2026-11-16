from collections.abc import Awaitable, Callable
from datetime import date

import pytest
from aiohttp import ClientResponseError, ClientSession, web
from aiohttp.test_utils import TestServer
from conftest import FIXTURES
from pydantic import ValidationError

from aioespn import DEFAULT_USER_AGENT, ESPNClient, SeasonType, Sport, State

type ServerFactory = Callable[[web.Application], Awaitable[TestServer]]
type Requests = list[web.Request]

# Each path the API serves, and the fixture the test server answers it with.
ROUTES = {
    "/apis/site/v2/leagues/dropdown": "leagues-soccer.json",
    "/apis/site/v2/sports/football/nfl/scoreboard": "scoreboard-football-nfl.json",
    "/apis/site/v2/sports/tennis/atp/scoreboard": "scoreboard-tennis-atp.json",
    "/apis/site/v2/sports/football/nfl/summary": "summary-football-nfl.json",
    "/apis/site/v2/sports/football/nfl/teams": "teams-football-nfl.json",
    "/apis/site/v2/sports/football/nfl/teams/22": "team-football-nfl.json",
    "/apis/site/v2/sports/football/nfl/teams/22/schedule": "schedule-football-nfl.json",
    "/apis/v2/sports/football/nfl/standings": "standings-football-nfl.json",
    "/apis/site/v2/sports/football/nfl/news": "news-football-nfl.json",
    "/apis/site/v2/sports/football/college-football/rankings": "rankings-football-college-football.json",
}


@pytest.fixture
async def api(aiohttp_server: ServerFactory) -> tuple[TestServer, Requests]:
    """Serve the fixtures where ESPN serves them, recording each request."""
    requests: Requests = []

    async def serve(request: web.Request) -> web.StreamResponse:
        requests.append(request)
        if request.path.startswith("/wrong-shape/"):
            return web.json_response({"events": "not a list"})
        if request.path not in ROUTES:
            raise web.HTTPNotFound()
        return web.FileResponse(FIXTURES / ROUTES[request.path])

    app = web.Application()
    app.router.add_get("/{path:.*}", serve)
    return await aiohttp_server(app), requests


async def test_fetches_each_endpoint(api: tuple[TestServer, Requests]) -> None:
    server, requests = api

    async with ESPNClient(base_url=server.make_url("/apis/")) as client:
        leagues = await client.leagues(Sport.SOCCER)
        scoreboard = await client.scoreboard(Sport.FOOTBALL, "nfl")
        summary = await client.summary(Sport.FOOTBALL, "nfl", "401873064")
        teams = await client.teams(Sport.FOOTBALL, "nfl")
        team = await client.team(Sport.FOOTBALL, "nfl", "22")
        schedule = await client.schedule(Sport.FOOTBALL, "nfl", "22")
        standings = await client.standings(Sport.FOOTBALL, "nfl")
        news = await client.news(Sport.FOOTBALL, "nfl")
        rankings = await client.rankings(Sport.FOOTBALL, "college-football")

    assert any(league.slug == "eng.1" for league in leagues)
    assert scoreboard.week is not None and scoreboard.week.number == 10
    assert summary.scoring_plays
    assert teams[0].display_name == "Arizona Cardinals"
    assert team.standing_summary == "4th in NFC West"
    assert schedule.events
    assert list(standings.tables())
    assert news.articles
    assert rankings[0].name == "AP Top 25"

    assert all(request.headers["User-Agent"] == DEFAULT_USER_AGENT for request in requests)
    assert dict(requests[0].query) == {"sport": "soccer", "limit": "1000"}
    assert dict(requests[1].query) == {}
    assert dict(requests[2].query) == {"event": "401873064"}
    assert dict(requests[3].query) == {"limit": "1000"}


async def test_scoreboard_query(api: tuple[TestServer, Requests]) -> None:
    server, requests = api

    async with ESPNClient(user_agent="MyBot/1.0", base_url=server.make_url("/apis/")) as client:
        await client.scoreboard(Sport.FOOTBALL, "nfl", dates=date(2026, 11, 15))
        await client.scoreboard(Sport.FOOTBALL, "nfl", dates=(date(2026, 11, 13), date(2026, 11, 17)))
        await client.scoreboard(Sport.FOOTBALL, "nfl", dates="202611", limit=500)
        await client.scoreboard(Sport.FOOTBALL, "nfl", week=10, season_type=SeasonType.REGULAR_SEASON, groups=80)
        board = await client.scoreboard(Sport.TENNIS, "atp", season_type=3)

    assert [dict(request.query) for request in requests] == [
        {"dates": "20261115"},
        {"dates": "20261113-20261117"},
        {"dates": "202611", "limit": "500"},
        {"groups": "80", "week": "10", "seasontype": "2"},
        {"seasontype": "3"},
    ]
    assert all(request.headers["User-Agent"] == "MyBot/1.0" for request in requests)
    assert board.events[0].groupings


async def test_standings_and_schedule_query(api: tuple[TestServer, Requests]) -> None:
    server, requests = api

    async with ESPNClient(base_url=server.make_url("/apis/")) as client:
        await client.standings(Sport.FOOTBALL, "nfl", season=2025, level=3)
        await client.schedule(Sport.FOOTBALL, "nfl", "22", season=2025, season_type=SeasonType.POSTSEASON)
        await client.news(Sport.FOOTBALL, "nfl", limit=20)
        await client.teams(Sport.FOOTBALL, "nfl", limit=None)

    assert [dict(request.query) for request in requests] == [
        {"season": "2025", "level": "3"},
        {"season": "2025", "seasontype": "3"},
        {"limit": "20"},
        {},
    ]


async def test_refuses_what_could_not_be_a_slug_or_id(api: tuple[TestServer, Requests]) -> None:
    server, requests = api

    async with ESPNClient(base_url=server.make_url("/apis/")) as client:
        with pytest.raises(ValueError):
            await client.scoreboard(Sport.FOOTBALL, "../nfl")
        with pytest.raises(ValueError):
            await client.summary(Sport.FOOTBALL, "nfl", "1/../../x")
        with pytest.raises(ValueError):
            await client.team(Sport.FOOTBALL, "nfl", "")
        with pytest.raises(ValueError):
            await client.scoreboard("cricket", "ipl")  # type: ignore[arg-type]
        # Numeric rugby slugs, dotted soccer slugs and hyphenated tennis IDs are all fine.
        with pytest.raises(ClientResponseError):
            await client.summary(Sport.SOCCER, "fifa.friendly_u21", "339-2026")

    assert len(requests) == 1


async def test_closes_only_its_own_session(api: tuple[TestServer, Requests]) -> None:
    server, _ = api

    client = ESPNClient(base_url=server.make_url("/apis/"))
    await client.news(Sport.FOOTBALL, "nfl")
    session = client._session
    await client.close()
    assert session is not None and session.closed

    async with ClientSession() as shared:
        async with ESPNClient(session=shared, base_url=server.make_url("/apis/")) as client:
            await client.news(Sport.FOOTBALL, "nfl")
        assert not shared.closed


async def test_raises_on_http_errors(api: tuple[TestServer, Requests]) -> None:
    server, _ = api

    async with ESPNClient(base_url=server.make_url("/apis/")) as client:
        with pytest.raises(ClientResponseError) as raised:
            await client.summary(Sport.GOLF, "pga", "401850980")
    assert raised.value.status == 404


async def test_raises_on_a_response_of_the_wrong_shape(api: tuple[TestServer, Requests]) -> None:
    server, _ = api

    async with ESPNClient(base_url=server.make_url("/wrong-shape/")) as client:
        with pytest.raises(ValidationError):
            await client.scoreboard(Sport.FOOTBALL, "nfl")


async def test_reads_the_status_of_a_watched_game(api: tuple[TestServer, Requests]) -> None:
    server, _ = api

    async with ESPNClient(base_url=server.make_url("/apis/")) as client:
        board = await client.scoreboard(Sport.FOOTBALL, "nfl")

    event = board.event("401873065")
    assert event is not None and event.status is not None and event.status.state is State.PRE
    assert board.event("nonexistent") is None
