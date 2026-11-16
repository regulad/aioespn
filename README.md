# aioespn

An asyncio client for ESPN's public JSON API, the one that espn.com and ESPN's apps read their scores from, with
typed, immutable [pydantic](https://docs.pydantic.dev/) models of its scoreboards, game summaries, teams, standings,
news and rankings. It covers every sport the API serves, from the NFL to Formula 1 to the Premier League.

```python
from aioespn import ESPNClient, Sport, State

async with ESPNClient() as client:
    scoreboard = await client.scoreboard(Sport.FOOTBALL, "nfl")
    for event in scoreboard.events:
        status, game = event.current_status, event.competition
        if status is None or game is None:
            continue
        print(event.short_name, status.type.short_detail, [(c.short_display_name, c.score) for c in game.competitors])
        if status.state is State.IN:
            summary = await client.summary(Sport.FOOTBALL, "nfl", event.id)
            for play in summary.scoring_summary:
                print(play.clock.display_value if play.clock else "", play.text)
```

## Endpoints

| Method | Path under `https://site.api.espn.com/apis/` | Returns |
| --- | --- | --- |
| `leagues(sport)` | `site/v2/leagues/dropdown?sport=…` | Every league of a sport, with its slug and names |
| `scoreboard(sport, league, *, dates, groups, limit, week, season_type)` | `site/v2/sports/{sport}/{league}/scoreboard` | A day's or week's events: their status, clock, competitors, scores and, while live, the situation |
| `summary(sport, league, event_id)` | `site/v2/sports/{sport}/{league}/summary?event=…` | A game's play-by-play, scoring plays or key events, box score, officials and news |
| `teams(sport, league)` | `site/v2/sports/{sport}/{league}/teams` | A league's teams |
| `team(sport, league, team_id)` | `site/v2/sports/{sport}/{league}/teams/{id}` | A team's records, standing and next game |
| `schedule(sport, league, team_id, *, season, season_type)` | `site/v2/sports/{sport}/{league}/teams/{id}/schedule` | A team's games in a season |
| `standings(sport, league, *, season, level, group)` | `v2/sports/{sport}/{league}/standings` | A league's tables, as a tree of conferences and divisions |
| `news(sport, league, *, limit)` | `site/v2/sports/{sport}/{league}/news` | A league's latest articles |
| `rankings(sport, league)` | `site/v2/sports/{sport}/{league}/rankings` | College polls, and tennis's and the UFC's rankings |

A league is named by its slug: `nfl`, `college-football`, `nba`, `mens-college-basketball`, `mlb`, `nhl`, `eng.1`,
`usa.1`, `uefa.champions`, `pga`, `atp`, `f1`, `ufc`, `afl`. Rugby's slugs are numbers, such as `270559` for the French
Top 14, and rugby league's is `3`. `leagues()` lists them all.

The models follow ESPN's field names in snake_case, so `shortDisplayName` becomes `short_display_name`, and leave out
the fields a client is unlikely to show, such as betting lines beyond the spread, win probabilities and video. Fields
the models don't know are ignored. Each method raises `aiohttp.ClientResponseError` when ESPN answers with an error,
`aiohttp.ClientError` when a request fails otherwise, and `pydantic.ValidationError` when a response has a shape the
models don't expect.

### How the sports differ

An event is a game, a race weekend, a golf or tennis tournament, or a fight card. Its competitions are what is played:
the game itself in team sports, each session of a race weekend, each fight of a card. A tennis tournament keeps its
matches in `event.groupings`, one per draw, and `event.all_competitions` lists every competition of any event.

A competitor is a team in team sports and an athlete in golf, racing, MMA and tennis singles; a tennis doubles pair has
a `roster`. `competitor.display_name` works for each. Scores are strings, since golf's are to par, such as `"-19"`
or `"E"`. MMA and racing have none.

`summary()` works for team sports. ESPN answers golf, racing and MMA events with a 404 and tennis matches with a 400,
whichever ID they're given: the scoreboard carries everything ESPN gives about those. Which list of plays a summary has
depends on the sport:

- basketball, hockey, baseball and Australian rules have the play-by-play as `plays`;
- football has `scoring_plays`, with every play inside `drives`;
- soccer has `key_events` (goals, cards and substitutions) and `commentary`;
- rugby and rugby league have their tries, kicks and cards as the competition's `details`, as their scoreboards do;
- volleyball, field hockey and lacrosse have no plays, only the score and box score.

`summary.scoring_summary` and `summary.all_plays` read whichever list the sport fills. Soccer's and rugby's scoreboards
also list each game's goals, tries and cards as `competition.details`, so a client can follow them from the scoreboard
alone.

### Following a league

ESPN serves scoreboards with `Cache-Control: max-age=10`, so there's nothing to gain from polling one more often. A
game's `status.state` moves from `State.PRE` to `State.IN` to `State.POST`, and `status.type.name` says more, such as
`STATUS_HALFTIME`, `STATUS_FINAL`, `STATUS_POSTPONED` or `STATUS_CANCELED`. Each play has an `id`, which a client can
remember so that it reports each play once.

Out of season, most leagues' scoreboards show the nearest day with events, which can be months away, rather than an
empty day. College scoreboards show only featured games unless given a group: `groups=50` is all of Division I men's
basketball, and `groups=80` all of FBS football.

On 2026-11-16 ESPN refused every scoreboard asked for a range of dates (`dates=(start, end)`) with a 400, though it
took a single day, a month (`dates="202611"`) and a year (`dates="2026"`).

## Sports

All 16 that the API serves, as `Sport`: Australian rules football, baseball (and softball), basketball, field hockey,
football (American and Canadian), golf, ice hockey, lacrosse, MMA, racing (Formula 1, IndyCar and NASCAR), rugby union,
rugby league, soccer, tennis, volleyball and water polo.

Cricket isn't among them: ESPN serves it through ESPNcricinfo's own API instead.

## Using ESPN's API

The API is ESPN's own, for its website and apps. It's undocumented and unofficial, needs no key, and can change or
disappear without notice; this library isn't affiliated with or endorsed by ESPN. The client sends a User-Agent naming
this library, `aioespn/0.1 (+https://github.com/regulad/aioespn)`, which an application can replace with its own. Keep
the load light: cache what you fetch, and don't poll faster than you need.

## Installing

It isn't on PyPI. Install it from git, pinned to a commit:

```sh
poetry add "git+https://github.com/regulad/aioespn.git#<commit>"
```

## Developing

```sh
poetry install --with type
poetry run pytest              # against the snapshots in tests/fixtures
poetry run pytest -m live      # against ESPN's API as it is now
poetry run mypy src tests
poetry run pre-commit run --all-files
```

## License

AGPL-3.0. The data belongs to ESPN and the leagues it reports on.
