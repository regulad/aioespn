"""Models for a league's rankings, ``/apis/site/v2/sports/{sport}/{league}/rankings``.

ESPN keeps rankings for college sports (the AP Top 25 and coaches' polls), for tennis (the ATP and WTA rankings) and for
MMA (its pound-for-pound and weight-class rankings). Other leagues return none.
"""

from pydantic import AwareDatetime

from aioespn._base import Athlete, ESPNModel, Team


class Rank(ESPNModel):
    """A team's or athlete's place in a ranking."""

    current: int
    previous: int | None = None
    points: float | None = None
    first_place_votes: int | None = None
    trend: str | None = None
    """The change since the last ranking, such as "+1", "-2" or "-"."""
    record_summary: str | None = None
    team: Team | None = None
    athlete: Athlete | None = None

    @property
    def display_name(self) -> str:
        if self.team is not None:
            return self.team.display_name
        if self.athlete is not None and self.athlete.name:
            return self.athlete.name
        return ""


class Ranking(ESPNModel):
    """One poll or ranking, such as the AP Top 25 or the ATP rankings."""

    id: str | None = None
    name: str
    short_name: str | None = None
    type: str | None = None
    date: AwareDatetime | None = None
    headline: str | None = None
    ranks: tuple[Rank, ...] = ()
    others: tuple[Rank, ...] = ()
    """Teams receiving votes, outside the top places."""


class _RankingsFeed(ESPNModel):
    rankings: tuple[Ranking, ...] = ()


__all__ = ["Rank", "Ranking"]
