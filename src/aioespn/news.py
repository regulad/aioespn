"""Models for a league's news, ``/apis/site/v2/sports/{sport}/{league}/news``, which game summaries also carry."""

from pydantic import AwareDatetime

from aioespn._base import ESPNModel


class ArticleImage(ESPNModel):
    url: str
    name: str | None = None
    caption: str | None = None
    alt: str | None = None
    width: int | None = None
    height: int | None = None


class ArticleLink(ESPNModel):
    href: str


class ArticleLinks(ESPNModel):
    web: ArticleLink | None = None
    mobile: ArticleLink | None = None


class Article(ESPNModel):
    """A story, headline or video on espn.com."""

    id: int | None = None
    type: str | None = None
    """Such as ``Story``, ``HeadlineNews``, ``Preview``, ``Recap`` or ``Media`` (a video)."""
    headline: str
    description: str | None = None
    byline: str | None = None
    published: AwareDatetime | None = None
    last_modified: AwareDatetime | None = None
    premium: bool | None = None
    """Whether the story is for ESPN+ subscribers only."""
    images: tuple[ArticleImage, ...] = ()
    links: ArticleLinks | None = None

    @property
    def url(self) -> str | None:
        """The article's page on espn.com."""
        return self.links.web.href if self.links is not None and self.links.web is not None else None

    @property
    def image_url(self) -> str | None:
        return self.images[0].url if self.images else None


class News(ESPNModel):
    """A list of the latest articles."""

    header: str | None = None
    """The list's title, such as "NFL News"."""
    articles: tuple[Article, ...] = ()


__all__ = ["Article", "ArticleImage", "ArticleLink", "ArticleLinks", "News"]
