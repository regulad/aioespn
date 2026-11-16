"""Models for a league's scoreboard, ``/apis/site/v2/sports/{sport}/{league}/scoreboard``: its events and their status.

An event is a game, a match, a race weekend, a golf tournament, a fight card or a tennis tournament. Its competitions
are what is played: one game in team sports, each session of a race weekend, each fight of a card. A tennis
tournament keeps its matches in :attr:`Event.groupings`, one grouping per draw. Team schedules and a team's next event
use the same models.
"""

import datetime as dt
from enum import StrEnum
from typing import Annotated, Any

from pydantic import AliasChoices, AwareDatetime, BeforeValidator, Field, model_validator

from aioespn._base import Athlete, DisplayValue, ESPNModel, Items, Link, Season, Stat, Team, Venue, find_link
from aioespn.plays import Play
from aioespn.sports import League


class State(StrEnum):
    """Whether a game is yet to start, under way or over."""

    PRE = "pre"
    IN = "in"
    POST = "post"


class StatusType(ESPNModel):
    """A game's state, and ESPN's words for it."""

    id: str | None = None
    name: str
    """ESPN's name for the status, such as ``STATUS_SCHEDULED``, ``STATUS_IN_PROGRESS``, ``STATUS_HALFTIME``,
    ``STATUS_FINAL``, ``STATUS_FULL_TIME``, ``STATUS_FINAL_PEN``, ``STATUS_POSTPONED`` or ``STATUS_CANCELED``."""
    state: State
    completed: bool = False
    description: str | None = None
    """The status in a word or two, such as "Scheduled", "In Progress", "Halftime" or "Final"."""
    detail: str | None = None
    """The status in full, such as "Mon, November 16th at 8:15 PM EST", "12:00 - 3rd Quarter" or "Final/OT"."""
    short_detail: str | None = None
    """The status in brief, such as "11/16 - 8:15 PM EST", "12:00 - 3rd" or "33'"."""
    alt_detail: str | None = None
    """How a finished game ended, where it went beyond regulation, such as "OT" or "SO"."""


class Status(ESPNModel):
    """Where a game stands: its state, period and clock."""

    clock: float | None = None
    """The clock in seconds. Golf and tennis have none."""
    display_clock: str | None = None
    """The clock as ESPN shows it, such as "4:57" or "33'"."""
    period: int | None = None
    """The current period: the quarter, half, inning, set, round or lap."""
    type: StatusType

    @property
    def state(self) -> State:
        return self.type.state


class Record(ESPNModel):
    """A win-loss record, such as a team's overall record or its record at home."""

    name: str | None = None
    type: str | None = None
    """Which record it is: ``total``, ``home``, ``road`` and so on."""
    abbreviation: str | None = None
    description: str | None = None
    summary: str = Field(validation_alias=AliasChoices("summary", "displayValue"))
    """The record, such as "4-5" or, in soccer, wins, draws and losses as "2-2-1"."""

    @model_validator(mode="before")
    @classmethod
    def _from_summary(cls, value: Any) -> Any:
        # Some college scoreboards also give a team's overall record as a bare "record": "1-2".
        if isinstance(value, str):
            return {"summary": value, "type": "total"}
        return value


def _records(value: Any) -> Any:
    if isinstance(value, str):
        return [value]
    return value


type Records = Annotated[tuple[Record, ...], BeforeValidator(_records)]


class LineScore(ESPNModel):
    """A competitor's score in one period: a quarter, an inning, a set, or one round of a golf tournament."""

    value: float | None = None
    display_value: str | None = None
    """The score as shown. Golf gives each round's score to par here, such as "-4", and its strokes as :attr:`value`."""
    period: int | None = None
    winner: bool | None = None
    """Whether the competitor won the set, in tennis."""
    tiebreak: int | None = None
    """The competitor's points in the set's tiebreak, in tennis."""
    linescores: tuple["LineScore", ...] = ()
    """Golf's hole-by-hole scores for the round."""


class CuratedRank(ESPNModel):
    current: int | None = None
    """The rank, where 99 means unranked."""


class Leader(ESPNModel):
    """An athlete leading a statistical category in a game or season."""

    display_value: str | None = None
    """The athlete's figures, such as "20/39, 151 YDS, 3 INT"."""
    value: float | None = None
    athlete: Athlete | None = None


class LeaderCategory(ESPNModel):
    """The leaders in one statistical category, such as passing yards."""

    name: str | None = None
    display_name: str | None = None
    short_display_name: str | None = None
    abbreviation: str | None = None
    leaders: tuple[Leader, ...] = ()


class Roster(ESPNModel):
    """The pair of a tennis doubles team."""

    display_name: str
    """Both players' names, such as "Orlando Luz / Rafael Matos"."""
    short_display_name: str | None = None
    athletes: tuple[Athlete, ...] = ()


class Competitor(ESPNModel):
    """One side of a competition: a team, or in golf, racing, MMA and tennis singles an athlete.

    A team sport's competitor has :attr:`team`, an individual sport's has :attr:`athlete`, and a tennis doubles pair
    has :attr:`roster`. :attr:`display_name` works for all three.
    """

    id: str
    uid: str | None = None
    type: str | None = None
    """``team`` or ``athlete``. Tennis doubles pairs are ``team`` too, though they have a :attr:`roster`."""
    order: int | None = None
    """The competitor's place in the listing. In golf and racing this is their position."""
    home_away: str | None = None
    """``home`` or ``away``, in team sports and tennis."""
    winner: bool | None = None
    score: DisplayValue = None
    """The score, as a string: "21", or in golf the score to par, such as "-19" or "E". MMA and racing have none."""
    team: Team | None = None
    athlete: Athlete | None = None
    roster: Roster | None = None
    name: str | None = None
    linescores: tuple["LineScore", ...] = ()
    records: Records = Field(default=(), validation_alias=AliasChoices("records", "record"))
    statistics: tuple[Stat, ...] = ()
    leaders: Items[LeaderCategory] = ()
    curated_rank: CuratedRank | None = None
    rank: int | None = None
    """The team's rank, as a game summary gives it. Scoreboards give :attr:`curated_rank` instead."""
    form: str | None = None
    """The team's last five results, newest last, such as "WDWLD", in soccer and rugby."""
    aggregate_score: float | None = None
    """The team's aggregate over both legs of a two-legged soccer tie."""
    shootout_score: int | None = None
    advance: bool | None = None
    hits: int | None = None
    errors: int | None = None
    possession: bool | None = None

    @property
    def display_name(self) -> str:
        """The team's, athlete's or doubles pair's name."""
        if self.team is not None:
            return self.team.display_name
        if self.athlete is not None and self.athlete.name:
            return self.athlete.name
        if self.roster is not None:
            return self.roster.display_name
        return self.name or self.id

    @property
    def short_display_name(self) -> str:
        """A shorter name, such as "Ravens", "C. Ramey" or "O. Luz / R. Matos"."""
        if self.team is not None:
            return self.team.short_display_name or self.team.abbreviation or self.team.display_name
        if self.athlete is not None and (self.athlete.short_name or self.athlete.name):
            return self.athlete.short_name or self.athlete.name or self.id
        if self.roster is not None:
            return self.roster.short_display_name or self.roster.display_name
        return self.display_name

    @property
    def ranking(self) -> int | None:
        """The team's rank in the poll ESPN features, such as the AP Top 25, or None if it's unranked."""
        rank = self.rank if self.rank is not None else self.curated_rank.current if self.curated_rank else None
        return rank if rank is not None and rank < 99 else None

    def record(self, kind: str = "total") -> str | None:
        """The competitor's record of one kind, such as ``total`` or ``home``, if given."""
        return next((record.summary for record in self.records if record.type == kind), None)


class Situation(ESPNModel):
    """The state of play in a game under way. Scoreboards give it only while a game is live.

    Basketball gives just the last play. Football adds the down and distance, and baseball the count and runners.
    """

    last_play: Play | None = None
    down: int | None = None
    distance: int | None = None
    yard_line: int | None = None
    down_distance_text: str | None = None
    """Such as "2nd & 2 at KC 35"."""
    short_down_distance_text: str | None = None
    possession_text: str | None = None
    possession: str | None = None
    """The ID of the team with the ball."""
    is_red_zone: bool | None = None
    home_timeouts: int | None = None
    away_timeouts: int | None = None
    balls: int | None = None
    strikes: int | None = None
    outs: int | None = None
    on_first: bool | None = None
    on_second: bool | None = None
    on_third: bool | None = None


class Note(ESPNModel):
    """A note on a game, such as which round of a tournament it is, or a tennis match's score in words."""

    type: str | None = None
    headline: str | None = None
    text: str | None = None


class Headline(ESPNModel):
    """A game's preview or recap headline."""

    type: str | None = None
    """``Preview`` or ``Recap``."""
    description: str | None = None
    short_link_text: str | None = None


class Broadcast(ESPNModel):
    """Who shows a game, in one market."""

    market: str | None = None
    """``national``, ``home`` or ``away``."""
    names: tuple[str, ...] = ()
    """The networks or services, such as ``("ESPN",)``."""

    @model_validator(mode="before")
    @classmethod
    def _from_media(cls, value: Any) -> Any:
        # Team schedules give one network per broadcast: {"market": {"type": "National"}, "media": {"shortName": ...}}.
        if isinstance(value, dict) and isinstance(value.get("media"), dict) and "names" not in value:
            market, name = value.get("market"), value["media"].get("shortName")
            if isinstance(market, dict):
                market = str(market.get("type") or "").lower() or None
            return {"market": market, "names": [name] if name else []}
        return value


class PeriodCount(ESPNModel):
    periods: int | None = None


class Format(ESPNModel):
    """How many periods a game has."""

    regulation: PeriodCount | None = None
    overtime: PeriodCount | None = None


class CompetitionType(ESPNModel):
    """What kind of competition it is. Racing names each session (FP1, Qual, Race), and MMA each fight's weight class.
    Tennis names each match's draw, such as "Men's Doubles"."""

    id: str | None = None
    abbreviation: str | None = None
    text: str | None = None
    slug: str | None = None


class Round(ESPNModel):
    id: str | None = None
    display_name: str | None = None
    """Such as "Group Stage" or "Quarterfinals"."""


class Series(ESPNModel):
    """A playoff series or two-legged tie that a game belongs to."""

    type: str | None = None
    title: str | None = None
    summary: str | None = None
    """Such as "MIL wins series 4-1"."""
    completed: bool | None = None
    total_competitions: int | None = None


class Odds(ESPNModel):
    """A sportsbook's line on a game."""

    details: str | None = None
    """The spread in words, such as "BAL -4.5"."""
    over_under: float | None = None
    spread: float | None = None


class Weather(ESPNModel):
    display_value: str | None = None
    """Such as "Clear"."""
    temperature: int | None = None
    """In degrees Fahrenheit."""
    high_temperature: int | None = None


class Competition(ESPNModel):
    """What is played at an event: a game, a fight, a race session or a tennis match."""

    id: str
    uid: str | None = None
    date: AwareDatetime | None = None
    start_date: AwareDatetime | None = None
    end_date: AwareDatetime | None = None
    status: Status | None = None
    competitors: tuple[Competitor, ...] = ()
    """The two sides, or a golf tournament's or race's field. A race session not yet run has none."""
    type: CompetitionType | None = None
    venue: Venue | None = None
    attendance: int | None = None
    neutral_site: bool | None = None
    conference_competition: bool | None = None
    play_by_play_available: bool | None = None
    notes: tuple[Note, ...] = ()
    broadcast: str | None = None
    """Every network showing the game, in one string, such as "ESPN+/Golf Chnl"."""
    broadcasts: tuple[Broadcast, ...] = ()
    format: Format | None = None
    details: tuple[Play, ...] = ()
    """The goals, tries and cards so far, with their clocks and athletes, in soccer and rugby."""
    situation: Situation | None = None
    leaders: Items[LeaderCategory] = ()
    headlines: tuple[Headline, ...] = ()
    series: Series | None = None
    odds: Items[Odds] = ()
    round: Round | None = None
    """The round of a tennis tournament that a match belongs to."""
    tournament_id: int | None = None

    @property
    def home(self) -> Competitor | None:
        """The home side, in team sports and tennis."""
        return next((c for c in self.competitors if c.home_away == "home"), None)

    @property
    def away(self) -> Competitor | None:
        """The away side, in team sports and tennis."""
        return next((c for c in self.competitors if c.home_away == "away"), None)


class Grouping(ESPNModel):
    """A draw of a tennis tournament, such as men's singles, and its matches."""

    id: str | None = None
    slug: str | None = None
    """Such as ``mens-singles`` or ``womens-doubles``."""
    display_name: str | None = None
    competitions: tuple[Competition, ...] = ()

    @model_validator(mode="before")
    @classmethod
    def _flatten_grouping(cls, value: Any) -> Any:
        # Each grouping is {"grouping": {"id", "slug", "displayName"}, "competitions": [...]}.
        if isinstance(value, dict) and isinstance(value.get("grouping"), dict):
            return {**value["grouping"], "competitions": value.get("competitions", [])}
        return value


class Week(ESPNModel):
    number: int | None = None
    text: str | None = None
    teams_on_bye: tuple[Team, ...] = ()


class Event(ESPNModel):
    """An event on a scoreboard or a team's schedule: a game, a race weekend, a tournament or a fight card."""

    id: str
    uid: str | None = None
    date: AwareDatetime
    end_date: AwareDatetime | None = None
    """When a golf or tennis tournament or a race weekend ends."""
    name: str
    """Such as "Los Angeles Chargers at Baltimore Ravens"."""
    short_name: str
    """Such as "LAC @ BAL"."""
    season: Season | None = None
    week: Week | None = None
    status: Status | None = None
    """The event's status. Team schedules give only each competition's, and long-defunct MMA promotions' cards have
    neither."""
    competitions: tuple[Competition, ...] = ()
    groupings: tuple[Grouping, ...] = ()
    """A tennis tournament's draws, each with its matches. Tennis events have no :attr:`competitions` of their own."""
    venue: Venue | None = None
    venues: tuple[Venue, ...] = ()
    """An MMA card's arena."""
    circuit: Venue | None = None
    """A race weekend's circuit."""
    weather: Weather | None = None
    links: tuple[Link, ...] = ()

    @property
    def competition(self) -> Competition | None:
        """The event's first competition: in team sports, the game itself."""
        return self.competitions[0] if self.competitions else None

    @property
    def all_competitions(self) -> tuple[Competition, ...]:
        """Every competition of the event, including each tennis match from every draw."""
        return self.competitions + tuple(match for grouping in self.groupings for match in grouping.competitions)

    @property
    def current_status(self) -> Status | None:
        """The event's status, or its first competition's where the event has none of its own."""
        if self.status is not None:
            return self.status
        return next((c.status for c in self.all_competitions if c.status is not None), None)

    @property
    def url(self) -> str | None:
        """The event's page on espn.com, its Gamecast or leaderboard."""
        return find_link(self.links, "desktop", "event")


class Day(ESPNModel):
    date: dt.date


class Scoreboard(ESPNModel):
    """A league's scoreboard for a day, a week, a month or a year."""

    events: tuple[Event, ...] = ()
    leagues: tuple[League, ...] = ()
    season: Season | None = None
    day: Day | None = None
    """The day the scoreboard shows, in sports that go by days."""
    week: Week | None = None
    """The week the scoreboard shows, in sports that go by weeks: football, Australian rules, rugby league and golf."""

    @property
    def league(self) -> League | None:
        return self.leagues[0] if self.leagues else None

    def event(self, event_id: str) -> Event | None:
        """The event with this ID, if it's on the scoreboard."""
        return next((event for event in self.events if event.id == event_id), None)


__all__ = [
    "Broadcast",
    "Competition",
    "CompetitionType",
    "Competitor",
    "CuratedRank",
    "Day",
    "Event",
    "Format",
    "Grouping",
    "Headline",
    "Leader",
    "LeaderCategory",
    "LineScore",
    "Note",
    "Odds",
    "PeriodCount",
    "Record",
    "Records",
    "Roster",
    "Round",
    "Scoreboard",
    "Series",
    "Situation",
    "State",
    "Status",
    "StatusType",
    "Week",
    "Weather",
]
