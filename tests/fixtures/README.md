# Fixtures

Responses from ESPN's API, chosen so the tests cover each shape the API takes, and trimmed to keep them small: fewer
events, competitors, plays, articles and table rows, and summaries without the sections the models don't read (win
probability, rosters, odds, videos and so on). Every object kept is as ESPN served it. Each path below is relative to
`https://site.api.espn.com/apis/`, and every file was served on 2026-11-16; a time is given where it matters.

## Scoreboards

| File | Path | Shows |
| --- | --- | --- |
| `scoreboard-australian-football-afl.json` | `site/v2/sports/australian-football/afl/scoreboard` | The AFL Grand Final, finished, out of season |
| `scoreboard-baseball-mlb.json` | `site/v2/sports/baseball/mlb/scoreboard` | World Series Game 5, finished: a series, leaders and a recap headline |
| `scoreboard-basketball-nba.json` | `site/v2/sports/basketball/nba/scoreboard`, 20:18 UTC | Two of the night's games, before tip-off |
| `scoreboard-basketball-nba-development-live.json` | `site/v2/sports/basketball/nba-development/scoreboard`, 20:21 UTC | A G League game in its third quarter, with its last play as the situation |
| `scoreboard-basketball-mens-college-basketball-groups-50.json` | `site/v2/sports/basketball/mens-college-basketball/scoreboard?groups=50&limit=500`, 20:16 UTC | Three of the day's Division I games, one under way |
| `scoreboard-field-hockey-womens-college-field-hockey.json` | `site/v2/sports/field-hockey/womens-college-field-hockey/scoreboard` | Two NCAA tournament games, finished, with ranked teams |
| `scoreboard-football-nfl.json` | `site/v2/sports/football/nfl/scoreboard`, 20:18 UTC | Week 10: two finished games and Monday night's, with odds and weather; the teams on bye |
| `scoreboard-golf-pga.json` | `site/v2/sports/golf/pga/scoreboard`, 20:18 UTC | A final round under way: the top five, with the first round hole by hole |
| `scoreboard-hockey-nhl.json` | `site/v2/sports/hockey/nhl/scoreboard` | Two of the night's games, before puck drop |
| `scoreboard-lacrosse-mens-college-lacrosse.json` | `site/v2/sports/lacrosse/mens-college-lacrosse/scoreboard` | May's NCAA final between ranked teams, out of season |
| `scoreboard-mma-ufc.json` | `site/v2/sports/mma/ufc/scoreboard?dates=202611` | A finished card and the next, three fights of each; each finished fight's first five details |
| `scoreboard-mma-affliction.json` | `site/v2/sports/mma/affliction/scoreboard` | A long-defunct promotion's last card, with neither status nor fights |
| `scoreboard-racing-f1.json` | `site/v2/sports/racing/f1/scoreboard?dates=202611` | A finished Grand Prix weekend, the top five of each session, and the next, whose sessions have no drivers yet |
| `scoreboard-rugby-180659.json` | `site/v2/sports/rugby/180659/scoreboard` | A Six Nations match, finished, with its tries, kicks and cards as details |
| `scoreboard-rugby-league-3.json` | `site/v2/sports/rugby-league/3/scoreboard` | An NRL match, finished, with its tries, kicks and cards as details |
| `scoreboard-soccer-eng.1.json` | `site/v2/sports/soccer/eng.1/scoreboard` | Two Premier League games, scheduled |
| `scoreboard-soccer-concacaf.nations.league-live.json` | `site/v2/sports/soccer/concacaf.nations.league/scoreboard`, 20:35 UTC | Two games in their second half, with their goals and cards as details |
| `scoreboard-tennis-atp.json` | `site/v2/sports/tennis/atp/scoreboard`, 20:17 UTC | The ATP Finals: three matches from each of two draws, doubles pairs, and a singles match under way |
| `scoreboard-volleyball-womens-college-volleyball.json` | `site/v2/sports/volleyball/womens-college-volleyball/scoreboard` | Two of the night's games, scheduled |
| `scoreboard-water-polo-mens-college-water-polo.json` | `site/v2/sports/water-polo/mens-college-water-polo/scoreboard` | An NCAA tournament game between teams still to be decided |

## Game summaries

| File | Path | Shows |
| --- | --- | --- |
| `summary-football-nfl.json` | `site/v2/sports/football/nfl/summary?event=401873064` | A finished game: its scoring plays, and its first three drives |
| `summary-basketball-nba.json` | `site/v2/sports/basketball/nba/summary?event=401909993` | Part of a finished game's play-by-play: the first twelve plays, the first twenty scoring plays and the last two |
| `summary-hockey-nhl.json` | `site/v2/sports/hockey/nhl/summary?event=401892725` | A finished game's play-by-play, with every goal |
| `summary-baseball-mlb.json` | `site/v2/sports/baseball/mlb/summary?event=401908046` | World Series Game 5's play-by-play, with every run; the box score, which groups its statistics, left out |
| `summary-soccer-eng.1.json` | `site/v2/sports/soccer/eng.1/summary?event=401879240` | A finished 4-4 draw: its key events and the start of its commentary |
| `summary-soccer-concacaf.nations.league-live.json` | `site/v2/sports/soccer/concacaf.nations.league/summary?event=401929707`, 20:33 UTC | A game in its second half |
| `summary-australian-football-afl.json` | `site/v2/sports/australian-football/afl/summary?event=1133711` | Part of the Grand Final's plays, every one a score, though none says so |
| `summary-rugby-270559.json` | `site/v2/sports/rugby/270559/summary?event=604419` | A finished Top 14 match, with its tries, kicks and cards as the competition's details |

## Everything else

| File | Path | Shows |
| --- | --- | --- |
| `leagues-soccer.json` | `site/v2/leagues/dropdown?sport=soccer&limit=500` | The first five of soccer's 220 leagues |
| `leagues-rugby.json` | `site/v2/leagues/dropdown?sport=rugby&limit=500` | Every rugby league, each with a number as its slug |
| `teams-football-nfl.json` | `site/v2/sports/football/nfl/teams` | Four of the NFL's teams |
| `team-football-nfl.json` | `site/v2/sports/football/nfl/teams/22` | A team with its records, standing and last game |
| `schedule-football-nfl.json` | `site/v2/sports/football/nfl/teams/22/schedule` | A team's first two games of the season |
| `standings-football-nfl.json` | `v2/sports/football/nfl/standings?level=3` | Two divisions of each conference, two teams of each |
| `standings-soccer-eng.1.json` | `v2/sports/soccer/eng.1/standings` | The top five of the Premier League, with what their places earn |
| `standings-racing-f1.json` | `v2/sports/racing/f1/standings` | The top three drivers and constructors |
| `standings-golf-pga.json` | `v2/sports/golf/pga/standings` | No standings |
| `news-football-nfl.json` | `site/v2/sports/football/nfl/news` | Three articles: a video, a headline and a story |
| `news-rugby-270559.json` | `site/v2/sports/rugby/270559/news` | No articles |
| `rankings-football-college-football.json` | `site/v2/sports/football/college-football/rankings` | The AP and coaches' polls, the top three and two others receiving votes of each |
| `rankings-tennis-atp.json` | `site/v2/sports/tennis/atp/rankings` | The ATP's top three |
| `rankings-mma-ufc.json` | `site/v2/sports/mma/ufc/rankings` | The men's pound-for-pound top three |

No fixture shows a live football or baseball game, so none shows the down and distance or the count and runners that
their situations carry; `Situation` names those fields as ESPN has in past seasons.

The live tests (`pytest -m live`) check the models against what ESPN serves now.
