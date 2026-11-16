"""The pieces every ESPN model shares."""

from collections.abc import Iterable
from typing import Annotated, Any

from pydantic import AliasChoices, AwareDatetime, BaseModel, BeforeValidator, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel


class ESPNModel(BaseModel):
    """Base of every model: immutable, and read from the API's camelCase keys.

    Fields the models don't declare are ignored, so ESPN can add fields without breaking anything. Models can also be
    built by their Python field names, as tests that make their own data do.
    """

    model_config = ConfigDict(alias_generator=to_camel, frozen=True, validate_by_name=True)


def _display_value(value: Any) -> Any:
    # Scoreboards give a score as a string, team schedules as {"value": 21.0, "displayValue": "21"}.
    if isinstance(value, dict):
        return value.get("displayValue")
    return value


type DisplayValue = Annotated[str | None, BeforeValidator(_display_value)]
"""A string that some endpoints give bare and others as the ``displayValue`` of an object."""


def _href(value: Any) -> Any:
    # Some endpoints give an image as its URL, others as {"href": ...}.
    if isinstance(value, dict):
        return value.get("href")
    return value


type Href = Annotated[str | None, BeforeValidator(_href)]
"""A URL that some endpoints give bare and others as the ``href`` of an object."""


def _items(value: Any) -> Any:
    # A few lists, such as soccer's odds, can hold nulls among their objects, and a few are sometimes given as their
    # only object, such as a hockey team's leaders in its schedule.
    if isinstance(value, list):
        return [item for item in value if item is not None]
    if isinstance(value, dict):
        return [value]
    return value


type Items[T] = Annotated[tuple[T, ...], BeforeValidator(_items)]
"""A list of objects, read as a tuple, leaving out any nulls in it. A lone object is read as a list of one."""


class Link(ESPNModel):
    """A link to a page on espn.com or in ESPN's app, labelled by its ``rel``."""

    href: str
    text: str | None = None
    short_text: str | None = None
    rel: tuple[str, ...] = ()


def find_link(links: Iterable[Link], *rel: str) -> str | None:
    """The address of the first link whose ``rel`` has every one of ``rel``, such as ``("desktop", "event")``."""
    return next((link.href for link in links if all(r in link.rel for r in rel)), None)


class Logo(ESPNModel):
    """A logo, in one of the variants that its ``rel`` names: ``default``, ``dark``, ``scoreboard`` and so on."""

    href: str
    width: int | None = None
    height: int | None = None
    alt: str | None = None
    rel: tuple[str, ...] = ()


def pick_logo(logos: Iterable[Logo]) -> str | None:
    """The address of the default logo among ``logos``, or else the first."""
    logos = tuple(logos)
    return next((logo.href for logo in logos if "default" in logo.rel), logos[0].href if logos else None)


class Address(ESPNModel):
    city: str | None = None
    state: str | None = None
    country: str | None = None
    zip_code: str | None = None


class Venue(ESPNModel):
    """Where a game is played. A racing circuit and an MMA card's arena are venues too."""

    id: str | None = None
    full_name: str | None = Field(default=None, validation_alias=AliasChoices("fullName", "displayName", "full_name"))
    """The venue's name, such as "M&T Bank Stadium". Tennis gives the city here and the arena as :attr:`court`."""
    short_name: str | None = None
    address: Address | None = None
    indoor: bool | None = None
    court: str | None = None
    """The court, at a tennis tournament."""


class Flag(ESPNModel):
    """A country's flag, shown beside an athlete."""

    href: str
    alt: str | None = None
    """The country's name, such as "New Zealand"."""

    @model_validator(mode="before")
    @classmethod
    def _from_href(cls, value: Any) -> Any:
        # Rankings give a flag as its bare URL.
        if isinstance(value, str):
            return {"href": value}
        return value


class Position(ESPNModel):
    abbreviation: str | None = None
    name: str | None = None
    display_name: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _from_abbreviation(cls, value: Any) -> Any:
        # Soccer's scoreboard details give a position as its bare abbreviation, such as "AM-R".
        if isinstance(value, str):
            return {"abbreviation": value}
        return value


class Athlete(ESPNModel):
    """A player, driver or fighter.

    Which fields are filled depends on where the athlete appears: play-by-play often gives only an ``id``, and the
    athletes in scoreboards' golf, racing, MMA and tennis competitors have no ``id`` of their own (their competitor's
    is the athlete's).
    """

    id: str | None = None
    uid: str | None = None
    display_name: str | None = None
    full_name: str | None = None
    short_name: str | None = Field(default=None, validation_alias=AliasChoices("shortName", "shortname", "short_name"))
    first_name: str | None = None
    last_name: str | None = None
    jersey: str | None = None
    position: Position | None = None
    headshot: Href = None
    flag: Flag | None = None
    links: tuple[Link, ...] = ()

    @property
    def name(self) -> str | None:
        """The athlete's full name, from whichever field this endpoint gave."""
        return self.display_name or self.full_name or self.short_name


class Team(ESPNModel):
    """A team, as most endpoints give it. Scoreboards also give each team's colours and one logo."""

    id: str
    uid: str | None = None
    slug: str | None = None
    location: str | None = None
    """The team's place, such as "Baltimore", or for a college its school, such as "Georgia"."""
    name: str | None = None
    """The team's name without its place, such as "Ravens"."""
    nickname: str | None = None
    abbreviation: str | None = None
    display_name: str
    """The team's full name, such as "Baltimore Ravens"."""
    short_display_name: str | None = None
    color: str | None = None
    """The team's colour, as six hex digits without a ``#``."""
    alternate_color: str | None = None
    is_active: bool | None = None
    logo: Href = None
    """The address of the team's logo, where the endpoint gives just one. See :attr:`logo_url`."""
    logos: tuple[Logo, ...] = ()
    links: tuple[Link, ...] = ()

    @model_validator(mode="before")
    @classmethod
    def _fill_display_name(cls, value: Any) -> Any:
        # Rankings leave out displayName; elsewhere it's the place followed by the name.
        if isinstance(value, dict) and "displayName" not in value and "display_name" not in value:
            parts = [value.get("location"), value.get("name")]
            name = " ".join(part for part in parts if part) or value.get("abbreviation") or value.get("id")
            return {**value, "displayName": name}
        return value

    @property
    def logo_url(self) -> str | None:
        """The address of the team's logo: the one the endpoint gave, or the default among its logos."""
        return self.logo or pick_logo(self.logos)

    @property
    def url(self) -> str | None:
        """The team's page on espn.com."""
        return find_link(self.links, "clubhouse", "desktop")


class Season(ESPNModel):
    """A season, or the part of one that an event belongs to."""

    year: int | None = None
    type: int | None = None
    """The part of the season: in most sports 1 for the preseason, 2 for the regular season and 3 for the postseason
    (see :class:`~aioespn.SeasonType`). Soccer numbers its own, such as 14105 for a league phase."""
    slug: str | None = None
    """The part of the season, such as ``regular-season``."""
    display_name: str | None = None
    start_date: AwareDatetime | None = None
    end_date: AwareDatetime | None = None

    @model_validator(mode="before")
    @classmethod
    def _flatten_type(cls, value: Any) -> Any:
        # Leagues give the part of the season as an object: {"id": "2", "type": 2, "name": "Regular Season", ...}.
        if isinstance(value, dict) and isinstance(value.get("type"), dict):
            kind = value["type"]
            return {**value, "type": kind.get("type", kind.get("id"))}
        return value


class Stat(ESPNModel):
    """One statistic, such as a team's points for or a player's yards, with ESPN's labels and formatted value."""

    name: str | None = None
    abbreviation: str | None = None
    display_name: str | None = None
    short_display_name: str | None = None
    description: str | None = None
    label: str | None = None
    type: str | None = None
    value: float | str | None = None
    display_value: str | None = None


__all__ = [
    "Address",
    "Athlete",
    "DisplayValue",
    "ESPNModel",
    "Flag",
    "Href",
    "Items",
    "Link",
    "Logo",
    "Position",
    "Season",
    "Stat",
    "Team",
    "Venue",
    "find_link",
    "pick_logo",
]
