"""The sports ESPN serves, and their leagues: what https://site.api.espn.com/apis/site/v2/leagues/dropdown lists."""

from enum import IntEnum, StrEnum

from aioespn._base import ESPNModel, Link, Logo, Season, find_link, pick_logo


class Sport(StrEnum):
    """Every sport that ESPN's site API serves, by the slug its URLs use.

    Cricket isn't among them: ESPN serves it through ESPNcricinfo's own API instead.
    """

    AUSTRALIAN_FOOTBALL = "australian-football"
    BASEBALL = "baseball"
    """Baseball and softball."""
    BASKETBALL = "basketball"
    FIELD_HOCKEY = "field-hockey"
    FOOTBALL = "football"
    """American and Canadian football."""
    GOLF = "golf"
    HOCKEY = "hockey"
    """Ice hockey."""
    LACROSSE = "lacrosse"
    MMA = "mma"
    RACING = "racing"
    """Formula 1, IndyCar and NASCAR."""
    RUGBY = "rugby"
    """Rugby union, whose league slugs are numbers, such as ``270559`` for the French Top 14."""
    RUGBY_LEAGUE = "rugby-league"
    SOCCER = "soccer"
    TENNIS = "tennis"
    VOLLEYBALL = "volleyball"
    WATER_POLO = "water-polo"


class SeasonType(IntEnum):
    """The parts of a season that most sports number alike, for :meth:`~aioespn.ESPNClient.scoreboard`.

    Soccer numbers the parts of its seasons in its own way, such as 14105 for a league phase; pass those as plain ints.
    """

    PRESEASON = 1
    REGULAR_SEASON = 2
    POSTSEASON = 3
    OFF_SEASON = 4


class League(ESPNModel):
    """A league, competition or tour: the NFL, the Premier League, the PGA Tour, the UFC and so on."""

    id: str
    uid: str | None = None
    slug: str
    """The league's slug, which the client's methods take: ``nfl``, ``eng.1``, ``pga``, or for rugby a number."""
    name: str
    """The league's full name, such as "National Football League"."""
    abbreviation: str | None = None
    short_name: str | None = None
    midsize_name: str | None = None
    alternate_id: str | None = None
    has_standings: bool | None = None
    """Whether ESPN keeps standings for the league. :meth:`~aioespn.ESPNClient.standings` returns none for the rest."""
    season: Season | None = None
    logos: tuple[Logo, ...] = ()
    links: tuple[Link, ...] = ()

    @property
    def logo_url(self) -> str | None:
        """The address of the league's default logo."""
        return pick_logo(self.logos)

    @property
    def url(self) -> str | None:
        """The league's page on espn.com."""
        return find_link(self.links, "index", "desktop")


class _LeaguesFeed(ESPNModel):
    leagues: tuple[League, ...] = ()


__all__ = ["League", "SeasonType", "Sport"]
