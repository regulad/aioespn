import re
from collections.abc import Mapping
from datetime import date
from types import TracebackType
from typing import Self

from aiohttp import ClientSession, ClientTimeout
from yarl import URL

from aioespn._base import Team
from aioespn.news import News
from aioespn.rankings import Ranking, _RankingsFeed
from aioespn.scoreboard import Scoreboard
from aioespn.sports import League, SeasonType, Sport, _LeaguesFeed
from aioespn.standings import Standings
from aioespn.summary import Summary
from aioespn.teams import TeamDetail, TeamSchedule, _TeamFeed, _TeamsFeed

DEFAULT_BASE_URL = URL("https://site.api.espn.com/apis/")
DEFAULT_USER_AGENT = "aioespn/0.1 (+https://github.com/regulad/aioespn)"

type Dates = date | str
"""The dates a scoreboard shows: a day, or a string in one of ESPN's own forms, such as a month as ``"YYYYMM"``."""

_SLUG = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


def _segment(kind: str, value: str) -> str:
    # League slugs and IDs go into the URL's path; refuse anything that could step out of it.
    if not _SLUG.fullmatch(value):
        raise ValueError(f"not a valid {kind}: {value!r}")
    return value


def _dates(dates: Dates) -> str:
    if isinstance(dates, date):
        return f"{dates:%Y%m%d}"
    return dates


class ESPNClient:
    """Reads ESPN's public JSON API, the one that espn.com and ESPN's apps use.

    The API is undocumented and unofficial: ESPN can change or withdraw it at any time. It needs no key. ESPN serves
    scoreboards with ``Cache-Control: max-age=10``, so there's nothing to gain from fetching one more often than that.

    Each method raises :class:`aiohttp.ClientResponseError` when ESPN answers with an error, such as a 400 for an
    unknown league or a 404 for an unknown event, :class:`aiohttp.ClientError` when a request fails otherwise, and
    :class:`pydantic.ValidationError` when a response doesn't have the shape the models expect. League slugs and IDs
    that couldn't be ESPN's raise :class:`ValueError` before any request is made.
    """

    def __init__(
        self,
        *,
        user_agent: str = DEFAULT_USER_AGENT,
        session: ClientSession | None = None,
        base_url: URL | str = DEFAULT_BASE_URL,
    ) -> None:
        """
        :param user_agent: Sent with every request. The default names this library and its repository; an
            application can name itself instead, such as ``"MyBot/1.0 (+https://github.com/me/mybot)"``.
        :param session: A session to make requests with, which the caller keeps and closes. Without one, the client
            opens its own on the first request and closes it in :meth:`close`.
        :param base_url: Where the API is served from, up to and including ``/apis/``.
        """
        self.user_agent = user_agent
        self.base_url = URL(base_url)
        self._session = session
        self._owns_session = session is None

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the session the client opened, if it opened one."""
        if self._owns_session and self._session is not None:
            await self._session.close()
            self._session = None

    async def _get(self, path: str, query: Mapping[str, str | int | None] | None = None) -> bytes:
        if self._session is None:
            self._session = ClientSession(timeout=ClientTimeout(total=30))
        params = {key: str(value) for key, value in (query or {}).items() if value is not None}
        url = (self.base_url / path).with_query(params)
        async with self._session.get(url, headers={"User-Agent": self.user_agent}) as response:
            response.raise_for_status()
            return await response.read()

    @staticmethod
    def _league_path(sport: Sport, league: str) -> str:
        return f"{Sport(sport).value}/{_segment('league slug', league)}"

    async def leagues(self, sport: Sport) -> tuple[League, ...]:
        """Fetch every league ESPN has for a sport, with its names, in one request.

        This is ESPN's own list for its menus: it lacks a few minor competitions, such as some of rugby's.
        """
        feed = await self._get("site/v2/leagues/dropdown", {"sport": Sport(sport).value, "limit": 1000})
        return _LeaguesFeed.model_validate_json(feed).leagues

    async def scoreboard(
        self,
        sport: Sport,
        league: str,
        *,
        dates: Dates | None = None,
        groups: int | str | None = None,
        limit: int | None = None,
        week: int | None = None,
        season_type: SeasonType | int | None = None,
    ) -> Scoreboard:
        """Fetch a league's scoreboard: its events, their status, competitors and scores.

        Without ``dates`` or ``week``, ESPN picks the day or week to show: today's, or out of season the nearest one
        with events, which can be months away.

        :param league: The league's slug, such as ``nfl``, ``eng.1`` or ``pga``.
        :param dates: The day to show, or a month as ``"YYYYMM"`` or a year as ``"YYYY"``. ESPN refuses a range of
            days (``"YYYYMMDD-YYYYMMDD"``) with a 400, which raises :class:`aiohttp.ClientResponseError`: fetch each
            day, or the month, instead.
        :param groups: Which group's games to show. College scoreboards show only featured games without one: ``50``
            shows all of Division I men's basketball and ``80`` all of FBS football.
        :param limit: The most events to return. ESPN returns at most 100 without one.
        :param week: The week to show, in sports that go by weeks, such as football. Pair it with ``season_type``.
        :param season_type: The part of the season, such as :attr:`SeasonType.POSTSEASON`.
        """
        query = {
            "dates": _dates(dates) if dates is not None else None,
            "groups": groups,
            "limit": limit,
            "week": week,
            "seasontype": int(season_type) if season_type is not None else None,
        }
        feed = await self._get(f"site/v2/sports/{self._league_path(sport, league)}/scoreboard", query)
        return Scoreboard.model_validate_json(feed)

    async def summary(self, sport: Sport, league: str, event_id: str) -> Summary:
        """Fetch a game's summary: its play-by-play, scoring plays or key events, box score and news.

        ESPN has summaries for team sports only. It answers golf, racing and MMA events with a 404 and tennis matches
        with a 400, which raise :class:`aiohttp.ClientResponseError`; their scoreboards carry what ESPN gives instead.

        :param event_id: The event's :attr:`~aioespn.scoreboard.Event.id`, from a scoreboard.
        """
        path = f"site/v2/sports/{self._league_path(sport, league)}/summary"
        feed = await self._get(path, {"event": _segment("event ID", event_id)})
        return Summary.model_validate_json(feed)

    async def teams(self, sport: Sport, league: str, *, limit: int | None = 1000) -> tuple[Team, ...]:
        """Fetch a league's teams. Individual sports, such as golf and tennis, have none.

        :param limit: The most teams to return. ESPN returns only 50 without one, which leaves out most of a college
            league's.
        """
        feed = await self._get(f"site/v2/sports/{self._league_path(sport, league)}/teams", {"limit": limit})
        return _TeamsFeed.model_validate_json(feed).teams

    async def team(self, sport: Sport, league: str, team_id: str) -> TeamDetail:
        """Fetch a team, with its record, standing and next game."""
        path = f"site/v2/sports/{self._league_path(sport, league)}/teams/{_segment('team ID', team_id)}"
        return _TeamFeed.model_validate_json(await self._get(path)).team

    async def schedule(
        self,
        sport: Sport,
        league: str,
        team_id: str,
        *,
        season: int | None = None,
        season_type: SeasonType | int | None = None,
    ) -> TeamSchedule:
        """Fetch a team's games in a season, by default the current one.

        :param season: The year the season starts in.
        :param season_type: The part of the season, such as :attr:`SeasonType.POSTSEASON`.
        """
        path = f"site/v2/sports/{self._league_path(sport, league)}/teams/{_segment('team ID', team_id)}/schedule"
        query = {"season": season, "seasontype": int(season_type) if season_type is not None else None}
        return TeamSchedule.model_validate_json(await self._get(path, query))

    async def standings(
        self,
        sport: Sport,
        league: str,
        *,
        season: int | None = None,
        level: int | None = None,
        group: int | str | None = None,
    ) -> Standings:
        """Fetch a league's standings, as a tree of conferences and divisions.

        :param season: The year the season starts in. Without one, the current season.
        :param level: How deep to split the league. Without one, the NFL's standings split into its two conferences;
            ``3`` splits each into its divisions.
        :param group: The group to show, where a league has several, such as ``80`` for FBS college football.
        """
        path = f"v2/sports/{self._league_path(sport, league)}/standings"
        query = {"season": season, "level": level, "group": group}
        return Standings.model_validate_json(await self._get(path, query))

    async def news(self, sport: Sport, league: str, *, limit: int | None = None) -> News:
        """Fetch a league's latest news.

        :param limit: The most articles to return. ESPN returns 6 without one.
        """
        path = f"site/v2/sports/{self._league_path(sport, league)}/news"
        return News.model_validate_json(await self._get(path, {"limit": limit}))

    async def rankings(self, sport: Sport, league: str) -> tuple[Ranking, ...]:
        """Fetch a league's polls or rankings: college sports' polls, tennis's ATP and WTA rankings and the UFC's
        rankings. Other leagues have none."""
        feed = await self._get(f"site/v2/sports/{self._league_path(sport, league)}/rankings")
        return _RankingsFeed.model_validate_json(feed).rankings


__all__ = ["DEFAULT_BASE_URL", "DEFAULT_USER_AGENT", "Dates", "ESPNClient"]
