"""Models for a league's standings, ``/apis/v2/sports/{sport}/{league}/standings``.

Standings form a tree of groups: a league holds conferences, which can hold divisions. Each group at the bottom holds a
table. Golf, MMA, tennis and some college leagues have none, and come back as a group with neither children nor table.
"""

from collections.abc import Iterator

from aioespn._base import Athlete, ESPNModel, Season, Stat, Team


class StandingsNote(ESPNModel):
    """What a place in the table earns, such as "Champions League"."""

    color: str | None = None
    """A CSS colour, such as ``#81D6AC``."""
    description: str | None = None
    rank: int | None = None


class StandingsEntry(ESPNModel):
    """A team's or, in racing, a driver's row in a table."""

    team: Team | None = None
    athlete: Athlete | None = None
    note: StandingsNote | None = None
    stats: tuple[Stat, ...] = ()
    """The row's columns: such as ``wins``, ``losses``, ``winPercent``, ``points``, ``gamesBehind`` and ``streak``.
    Which there are depends on the sport."""

    @property
    def display_name(self) -> str:
        if self.team is not None:
            return self.team.display_name
        if self.athlete is not None and self.athlete.name:
            return self.athlete.name
        return ""

    def stat(self, name: str) -> Stat | None:
        """The column with this name, such as ``wins`` or ``points``, if the table has it."""
        return next((stat for stat in self.stats if stat.name == name), None)


class StandingsTable(ESPNModel):
    id: str | None = None
    name: str | None = None
    display_name: str | None = None
    season: int | None = None
    season_type: int | None = None
    entries: tuple[StandingsEntry, ...] = ()


class StandingsGroup(ESPNModel):
    """A league, conference or division, and either its subgroups or its table."""

    id: str | None = None
    uid: str | None = None
    name: str | None = None
    """Such as "National Football League", "AFC East" or "Driver Standings"."""
    abbreviation: str | None = None
    short_name: str | None = None
    is_conference: bool | None = None
    children: tuple["StandingsGroup", ...] = ()
    standings: StandingsTable | None = None

    @property
    def entries(self) -> tuple[StandingsEntry, ...]:
        """The group's own table, or nothing if its subgroups hold the tables."""
        return self.standings.entries if self.standings is not None else ()

    def tables(self) -> Iterator["StandingsGroup"]:
        """Every group in the tree, this one included, that has a table, in order."""
        if self.standings is not None:
            yield self
        for child in self.children:
            yield from child.tables()


class Standings(StandingsGroup):
    """A league's standings: the root of the tree of groups."""

    season: Season | None = None


__all__ = ["Standings", "StandingsEntry", "StandingsGroup", "StandingsNote", "StandingsTable"]
