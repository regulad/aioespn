"""Models for a game's summary, ``/apis/site/v2/sports/{sport}/{league}/summary?event={id}``.

ESPN serves summaries for team sports. Which play lists a summary has depends on the sport:

- basketball, hockey, baseball and Australian rules have the play-by-play as :attr:`Summary.plays`;
- football has its scoring plays as :attr:`Summary.scoring_plays`, and every play inside :attr:`Summary.drives`;
- soccer has the goals, cards and substitutions as :attr:`Summary.key_events`, and a running :attr:`Summary.commentary`;
- rugby and rugby league keep their tries, kicks and cards as the competition's
  :attr:`~HeaderCompetition.details`, as their scoreboards do;
- volleyball, field hockey and lacrosse have no plays, only the score and box score.

Golf, racing, MMA and tennis have no summaries: their scoreboards carry everything ESPN gives about their events.
"""

from typing import Any

from pydantic import AwareDatetime, model_validator

from aioespn._base import ESPNModel, Link, Season, Stat, Team, Venue, find_link
from aioespn.news import News
from aioespn.plays import Clock, Play
from aioespn.scoreboard import Competitor, Format, LeaderCategory, Status, Weather
from aioespn.sports import League


class HeaderCompetition(ESPNModel):
    """The game itself, as a summary's header gives it, with its competitors' scores and status."""

    id: str
    uid: str | None = None
    date: AwareDatetime | None = None
    status: Status | None = None
    competitors: tuple[Competitor, ...] = ()
    neutral_site: bool | None = None
    conference_competition: bool | None = None
    details: tuple[Play, ...] = ()
    """Soccer's goals and cards, and rugby's tries, kicks and cards."""

    @property
    def home(self) -> Competitor | None:
        return next((c for c in self.competitors if c.home_away == "home"), None)

    @property
    def away(self) -> Competitor | None:
        return next((c for c in self.competitors if c.home_away == "away"), None)


class SummaryHeader(ESPNModel):
    id: str
    uid: str | None = None
    season: Season | None = None
    week: int | None = None
    league: League | None = None
    competitions: tuple[HeaderCompetition, ...] = ()
    game_note: str | None = None
    """Such as "World Series - Game 5"."""
    links: tuple[Link, ...] = ()

    @property
    def competition(self) -> HeaderCompetition | None:
        return self.competitions[0] if self.competitions else None

    @property
    def url(self) -> str | None:
        """The game's page on espn.com."""
        return find_link(self.links, "desktop", "event")


class Commentary(ESPNModel):
    """One line of soccer's running commentary."""

    sequence: int | None = None
    time: Clock | None = None
    text: str
    play: Play | None = None


class Drive(ESPNModel):
    """A football team's possession, and its plays."""

    id: str | None = None
    description: str | None = None
    """Such as "13 plays, 80 yards, 6:04"."""
    team: Team | None = None
    result: str | None = None
    """How the drive ended, such as ``TD``, ``FG`` or ``PUNT``."""
    display_result: str | None = None
    short_display_result: str | None = None
    is_score: bool | None = None
    yards: int | None = None
    offensive_plays: int | None = None
    time_elapsed: Clock | None = None
    plays: tuple[Play, ...] = ()


class Drives(ESPNModel):
    previous: tuple[Drive, ...] = ()
    """The finished drives, in order."""
    current: Drive | None = None
    """The drive under way, while the game is."""


class BoxscoreTeam(ESPNModel):
    """A team's statistics for the game."""

    team: Team
    home_away: str | None = None
    statistics: tuple[Stat, ...] = ()
    """Such as fouls, yellow cards and possession, each with a ``label`` and ``display_value``. Rugby league groups its
    statistics instead, and those aren't modelled."""


class Boxscore(ESPNModel):
    teams: tuple[BoxscoreTeam, ...] = ()


class Official(ESPNModel):
    """A referee, umpire or other official."""

    display_name: str
    position: str | None = None
    """Such as "Referee" or "Down Judge"."""

    @model_validator(mode="before")
    @classmethod
    def _flatten_position(cls, value: Any) -> Any:
        # Each official's position comes as {"name": "Referee", "displayName": "Referee", "id": "114"}.
        if isinstance(value, dict) and isinstance(value.get("position"), dict):
            position = value["position"]
            return {**value, "position": position.get("displayName") or position.get("name")}
        return value


class GameInfo(ESPNModel):
    venue: Venue | None = None
    attendance: int | None = None
    officials: tuple[Official, ...] = ()
    weather: Weather | None = None


class TeamLeaders(ESPNModel):
    """A team's leaders in the game, by statistical category."""

    team: Team
    leaders: tuple[LeaderCategory, ...] = ()


class Summary(ESPNModel):
    """A game's summary: its header, play lists, box score and news."""

    header: SummaryHeader
    plays: tuple[Play, ...] = ()
    scoring_plays: tuple[Play, ...] = ()
    """Football's scoring plays."""
    key_events: tuple[Play, ...] = ()
    """Soccer's key events: kick-off, goals, cards, substitutions, half-time and full time. They carry no score."""
    commentary: tuple[Commentary, ...] = ()
    drives: Drives | None = None
    boxscore: Boxscore | None = None
    game_info: GameInfo | None = None
    format: Format | None = None
    leaders: tuple[TeamLeaders, ...] = ()
    news: News | None = None

    @property
    def competition(self) -> HeaderCompetition | None:
        """The game, with its competitors and status."""
        return self.header.competition

    @property
    def scoring_summary(self) -> tuple[Play, ...]:
        """The game's scoring plays in order, from whichever list the sport keeps them in.

        That's :attr:`scoring_plays` for football, and the plays that scored among :attr:`plays` or soccer's
        :attr:`key_events` elsewhere. Where a play doesn't say whether it scored, as in Australian rules, it scored if
        it changed the score. Rugby's are in the competition's :attr:`~HeaderCompetition.details`, which mix in cards
        and aren't included.
        """
        if self.scoring_plays:
            return self.scoring_plays
        scoring: list[Play] = []
        last: tuple[int | None, int | None] = (0, 0)
        for play in self.plays + self.key_events:
            score = (play.away_score, play.home_score)
            if play.scoring_play is not None or play.score_value is not None:
                scored = play.is_scoring
            else:
                scored = None not in score and score != last
            if None not in score:
                last = score
            if scored:
                scoring.append(play)
        return tuple(scoring)

    @property
    def all_plays(self) -> tuple[Play, ...]:
        """Every play of the game in order: :attr:`plays`, or football's plays from its :attr:`drives`, or soccer's
        :attr:`key_events`."""
        if self.plays:
            return self.plays
        if self.drives is not None:
            drives = self.drives.previous + ((self.drives.current,) if self.drives.current is not None else ())
            seen: set[str | None] = set()
            plays: list[Play] = []
            for play in (play for drive in drives for play in drive.plays):
                # Count each play once, should the current drive also be listed among the finished ones.
                if play.id is None or play.id not in seen:
                    seen.add(play.id)
                    plays.append(play)
            return tuple(plays)
        return self.key_events


__all__ = [
    "Boxscore",
    "BoxscoreTeam",
    "Commentary",
    "Drive",
    "Drives",
    "GameInfo",
    "HeaderCompetition",
    "Official",
    "Summary",
    "SummaryHeader",
    "TeamLeaders",
]
