"""Models for a league's teams, ``/apis/site/v2/sports/{sport}/{league}/teams``, one team's detail, ``teams/{id}``, and
its schedule, ``teams/{id}/schedule``."""

from typing import Annotated, Any

from pydantic import BeforeValidator

from aioespn._base import ESPNModel, Season, Team
from aioespn.scoreboard import Event, Record


def _items(value: Any) -> Any:
    # A team's record comes as {"items": [...]}.
    if isinstance(value, dict):
        return value.get("items", [])
    return value


class TeamDetail(Team):
    """A team, with its record, standing and next game."""

    record: Annotated[tuple[Record, ...], BeforeValidator(_items)] = ()
    """The team's records this season: overall (``total``), at ``home``, on the ``road`` and so on."""
    record_summary: str | None = None
    standing_summary: str | None = None
    """Where the team stands, such as "4th in NFC West"."""
    next_event: tuple[Event, ...] = ()
    """The team's next game, or its last while it has none scheduled."""

    def record_of(self, kind: str = "total") -> str | None:
        """The team's record of one kind, such as ``total`` or ``home``, if given."""
        return next((record.summary for record in self.record if record.type == kind), None)


class _TeamFeed(ESPNModel):
    team: TeamDetail


class _TeamEntry(ESPNModel):
    team: Team


class _TeamsLeague(ESPNModel):
    teams: tuple[_TeamEntry, ...] = ()


class _TeamsSport(ESPNModel):
    leagues: tuple[_TeamsLeague, ...] = ()


class _TeamsFeed(ESPNModel):
    sports: tuple[_TeamsSport, ...] = ()

    @property
    def teams(self) -> tuple[Team, ...]:
        return tuple(entry.team for sport in self.sports for league in sport.leagues for entry in league.teams)


class TeamSchedule(ESPNModel):
    """A team's games in one season."""

    team: TeamDetail
    season: Season | None = None
    events: tuple[Event, ...] = ()
    """The team's games, each with one competition whose status and score are given; the events have no status of
    their own (see :attr:`~aioespn.scoreboard.Event.current_status`)."""
    bye_week: int | None = None


__all__ = ["TeamDetail", "TeamSchedule"]
