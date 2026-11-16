"""An asyncio client for ESPN's public JSON API, with typed models of its scoreboards, game summaries, teams,
standings, news and rankings.

>>> async with ESPNClient() as client:
...     scoreboard = await client.scoreboard(Sport.FOOTBALL, "nfl")

The models live in :mod:`aioespn.sports`, :mod:`aioespn.scoreboard`, :mod:`aioespn.plays`, :mod:`aioespn.summary`,
:mod:`aioespn.teams`, :mod:`aioespn.standings`, :mod:`aioespn.news` and :mod:`aioespn.rankings`.
"""

from aioespn._base import Athlete, Link, Logo, Season, Stat, Team, Venue
from aioespn._client import DEFAULT_BASE_URL, DEFAULT_USER_AGENT, Dates, ESPNClient
from aioespn.news import Article, News
from aioespn.plays import Play
from aioespn.rankings import Rank, Ranking
from aioespn.scoreboard import Competition, Competitor, Event, Scoreboard, Situation, State, Status
from aioespn.sports import League, SeasonType, Sport
from aioespn.standings import Standings, StandingsEntry, StandingsGroup
from aioespn.summary import Summary
from aioespn.teams import TeamDetail, TeamSchedule

__all__ = [
    "DEFAULT_BASE_URL",
    "DEFAULT_USER_AGENT",
    "Article",
    "Athlete",
    "Competition",
    "Competitor",
    "Dates",
    "ESPNClient",
    "Event",
    "League",
    "Link",
    "Logo",
    "News",
    "Play",
    "Rank",
    "Ranking",
    "Scoreboard",
    "Season",
    "SeasonType",
    "Situation",
    "Sport",
    "Standings",
    "StandingsEntry",
    "StandingsGroup",
    "Stat",
    "State",
    "Status",
    "Summary",
    "Team",
    "TeamDetail",
    "TeamSchedule",
    "Venue",
]
