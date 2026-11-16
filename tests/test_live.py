"""Check the models against what ESPN serves now. Run with ``pytest -m live``.

The requests go one at a time, with a pause between them, to keep the load on ESPN light.
"""

import asyncio

import pytest

from aioespn import ESPNClient, Sport

pytestmark = pytest.mark.live

USER_AGENT = "aioespn-tests/0.1 (+https://github.com/regulad/aioespn)"
PAUSE = 0.5

# One league of each sport, chosen for having events most of the year.
LEAGUES = {
    Sport.AUSTRALIAN_FOOTBALL: "afl",
    Sport.BASEBALL: "mlb",
    Sport.BASKETBALL: "nba",
    Sport.FIELD_HOCKEY: "womens-college-field-hockey",
    Sport.FOOTBALL: "nfl",
    Sport.GOLF: "pga",
    Sport.HOCKEY: "nhl",
    Sport.LACROSSE: "mens-college-lacrosse",
    Sport.MMA: "ufc",
    Sport.RACING: "f1",
    Sport.RUGBY: "270559",
    Sport.RUGBY_LEAGUE: "3",
    Sport.SOCCER: "eng.1",
    Sport.TENNIS: "atp",
    Sport.VOLLEYBALL: "womens-college-volleyball",
    Sport.WATER_POLO: "mens-college-water-polo",
}


@pytest.mark.parametrize("sport", list(Sport))
async def test_every_sport(sport: Sport) -> None:
    async with ESPNClient(user_agent=USER_AGENT) as client:
        leagues = await client.leagues(sport)
        await asyncio.sleep(PAUSE)
        board = await client.scoreboard(sport, LEAGUES[sport])
        await asyncio.sleep(PAUSE)

    assert LEAGUES[sport] in {league.slug for league in leagues}
    assert board.league is not None and board.league.slug == LEAGUES[sport]
    for event in board.events:
        assert event.name
        for competition in event.all_competitions:
            assert all(competitor.display_name for competitor in competition.competitors)


async def test_everything_else() -> None:
    async with ESPNClient(user_agent=USER_AGENT) as client:
        board = await client.scoreboard(Sport.SOCCER, "eng.1")
        await asyncio.sleep(PAUSE)
        summary = await client.summary(Sport.SOCCER, "eng.1", board.events[0].id)
        await asyncio.sleep(PAUSE)
        teams = await client.teams(Sport.FOOTBALL, "nfl")
        await asyncio.sleep(PAUSE)
        team = await client.team(Sport.FOOTBALL, "nfl", teams[0].id)
        await asyncio.sleep(PAUSE)
        schedule = await client.schedule(Sport.FOOTBALL, "nfl", teams[0].id)
        await asyncio.sleep(PAUSE)
        standings = await client.standings(Sport.FOOTBALL, "nfl", level=3)
        await asyncio.sleep(PAUSE)
        news = await client.news(Sport.FOOTBALL, "nfl")
        await asyncio.sleep(PAUSE)
        rankings = await client.rankings(Sport.FOOTBALL, "college-football")

    assert summary.header.id == board.events[0].id
    assert len(teams) == 32
    assert team.id == teams[0].id
    assert schedule.team.id == teams[0].id
    assert len(list(standings.tables())) == 8
    assert news.articles
    assert rankings and rankings[0].ranks
