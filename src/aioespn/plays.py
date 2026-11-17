"""Plays: what happens in a game, as summaries' play-by-play, scoring plays and key events, and scoreboards' details.

Every sport gives its plays in one shape, though each fills in different parts of it. Soccer's and rugby's scoreboards
list each goal, try and card as a competition's :attr:`~aioespn.scoreboard.Competition.details`, which are plays too.
"""

from typing import Any

from pydantic import AwareDatetime, model_validator

from aioespn._base import Athlete, ESPNModel, Href


class PlayType(ESPNModel):
    """What kind of play it was, such as "Field Goal Good", "Jump Shot", "Goal - Header" or "Yellow Card"."""

    id: str | None = None
    text: str | None = None
    abbreviation: str | None = None
    type: str | None = None
    """A slug for the kind of play, such as ``goal`` or ``yellow-card``. Soccer and baseball give one."""
    penalty_type: str | None = None
    """A hockey penalty's kind, such as "Minor", "Major" or "Misconduct". Hockey names a penalty's play after the
    infraction, such as "Tripping", and gives it this and :attr:`penalty_minutes`."""
    penalty_minutes: int | None = None
    """How long a hockey penalty is, in minutes."""

    @property
    def is_penalty(self) -> bool:
        """Whether the play is a hockey penalty."""
        return self.penalty_type is not None or self.penalty_minutes is not None


class Period(ESPNModel):
    """A period of play: a quarter, half, inning, set or round."""

    number: int | None = None
    display_value: str | None = None
    """The period's name, such as "4th Quarter" or "2nd Inning"."""
    type: str | None = None
    """For baseball, which half of the inning: "Top" or "Bottom"."""


class Clock(ESPNModel):
    """A game clock reading."""

    value: float | None = None
    """The clock in seconds. Soccer's and rugby's count up from the start of the match; most others count down."""
    display_value: str | None = None
    """The clock as ESPN shows it, such as "8:56" or "33'"."""


class PlayTeam(ESPNModel):
    """The team a play belongs to. Most plays give only its ``id``; match it against the competitors."""

    id: str | None = None
    display_name: str | None = None
    abbreviation: str | None = None
    logo: Href = None


class Participant(ESPNModel):
    """An athlete involved in a play, and their part in it."""

    athlete: Athlete
    type: str | None = None
    """The athlete's part in the play, such as ``scorer``, ``assister``, ``batter`` or ``pitcher``, where given."""


class ScoringType(ESPNModel):
    """How a football scoring play scored, such as "Touchdown" or "Field Goal"."""

    name: str | None = None
    display_name: str | None = None
    abbreviation: str | None = None


class Play(ESPNModel):
    """One play, event or detail of a game.

    Which fields are given depends on the sport and on the list the play comes from: soccer's key events have no
    running score, basketball's plays name their athletes only by ID, and so on. :attr:`text` describes the play in
    every sport.
    """

    id: str | None = None
    sequence_number: str | None = None
    type: PlayType | None = None
    text: str | None = None
    """The play, described in a sentence."""
    short_text: str | None = None
    short_description: str | None = None
    away_score: int | None = None
    """The away side's score after the play."""
    home_score: int | None = None
    """The home side's score after the play."""
    period: Period | None = None
    clock: Clock | None = None
    scoring_play: bool | None = None
    score_value: int | None = None
    """The points the play scored."""
    scoring_type: ScoringType | None = None
    team: PlayTeam | None = None
    participants: tuple[Participant, ...] = ()
    wallclock: AwareDatetime | None = None
    """When the play happened."""
    red_card: bool | None = None
    yellow_card: bool | None = None
    penalty_kick: bool | None = None
    own_goal: bool | None = None
    shootout: bool | None = None
    """Whether the play was part of a penalty shootout."""

    @model_validator(mode="before")
    @classmethod
    def _participants_from_athletes(cls, value: Any) -> Any:
        # Scoreboards' details list their athletes as "athletesInvolved" rather than as participants.
        if isinstance(value, dict) and "participants" not in value and "athletesInvolved" in value:
            athletes = value["athletesInvolved"] or []
            return {**value, "participants": [{"athlete": athlete} for athlete in athletes]}
        return value

    @property
    def is_scoring(self) -> bool:
        """Whether the play scored, by ESPN's flag or else by the points it was worth."""
        if self.scoring_play is not None:
            return self.scoring_play
        return bool(self.score_value)


__all__ = ["Clock", "Participant", "Period", "Play", "PlayTeam", "PlayType", "ScoringType"]
