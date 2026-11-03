# predict-brasileirao

**🌐 Live site: <https://predict-brasileirao.vercel.app>** (Português / English)

Predicts the final table of the **Brasileirão Série A 2026**, focusing on:

- **Top 6** → Libertadores
- **Bottom 4** → relegation to Série B

How it works, in one line: each team gets a strength score from past results, scores or betting odds, then the
remaining games are "played" 20,000 times on the computer, and we count how often each team finishes in each
position. The site's "How it works" page explains it in plain language.

## How the site stays up to date

```
GitHub Actions (twice a day)          this repo                       Vercel
python -m brasileirao.export  ──▶  web/public/data/*.json  ──push──▶  rebuilds the static site
(runs the models, writes JSON)      (committed only if changed)        (web/, Next.js)
```

- [`.github/workflows/update-data.yml`](.github/workflows/update-data.yml) runs at 00:30 and 12:00 (Brasília time)
  and can be started by hand from the Actions tab ("Run workflow"; tick *accuracy* to re-run the backtest).
- [`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs the Python and web tests on every push.
- The website lives in [`web/`](web/README.md).

## 1. Setup (once)

You need [Anaconda](https://www.anaconda.com/download) or Miniconda installed.
Open the **Anaconda Prompt** (or any terminal where `conda` works) in this folder and run:

```bash
conda env create -f environment.yml
```

This creates an environment called `brasileirao` with all the libraries and installs this project in it.

If `environment.yml` changes later, update the environment with:

```bash
conda env update -f environment.yml --prune
```

## 2. Run the prediction

```bash
conda activate brasileirao
python -m brasileirao.predict --refresh
```

- `--refresh` downloads the latest results. The main source is [football-data.co.uk](https://www.football-data.co.uk/brazil.php)
  (all seasons since 2012, with betting odds), but it is only updated a couple of times a week, so the games
  played since its last update are added from ESPN's public scoreboard.
  Leave `--refresh` out to reuse the copies already downloaded in `data/raw/`.
- `--sims 50000` changes the number of simulated seasons (default 20,000; more = more precise, but slower).
- `--model poisson` (or `dixon-coles`, `market`) picks the match model (default `elo`):
  - `elo` – team strength learned from results
  - `poisson` / `dixon-coles` – attack and defence learned from scores
  - `market` – team strength learned from bookmakers' odds of recent games (best in the backtest)

  Results are saved per model, e.g. `outputs/predictions_2026_market.csv`.

It prints a table like this (one row per team):

| column | meaning |
|---|---|
| `current_position`, `current_points` | the table today |
| `elo` / `attack`, `defence` / `market_rating` | team strength for the chosen model (Elo: 1500 = average; Poisson: 1.0 = average; market: 0 = average; higher = better) |
| `expected_points`, `expected_position` | average over all simulated seasons |
| `p_title` | chance of winning the league |
| `p_top6` | chance of finishing 1st–6th (Libertadores) |
| `p_relegation` | chance of finishing 17th–20th (Série B) |

The results are also saved in `outputs/`:

- `predictions_2026_elo.csv` – the table above (one file per model)
- `positions_2026_elo.csv` – the chance of each team finishing in each position (1 to 20)

### Next games of the relegation fight

```bash
python -m brasileirao.next_games
```

For every team with a relegation risk of 5% or more, it shows the team's **next game** (from ESPN's schedule),
the chance of a home win / draw / away win, and the team's relegation risk **today** and **if it wins, draws
or loses** that game. Example:

```
Wed 04/11 19:30   Flamengo RJ (73 pts, 1st)  x  Gremio (37 pts, 15th)
  Chance:  Flamengo RJ win 78%  |  draw 15%  |  Gremio win 8%
  Relegation risk   today   if win  if draw  if lose
  Gremio              45%      15%      40%      49%
```

How "if win" is computed: out of the 20,000 simulated seasons, keep only those in which Grêmio won this game,
and count how often Grêmio was relegated in them.

Options: `--model`, `--sims`, `--refresh` (same as above), `--min-risk 10` (only teams with risk ≥ 10%),
`--days 21` (how far ahead to look for games; default 14).

## 3. Check how good the model is (optional)

```bash
python -m brasileirao.backtest
```

This pretends we are in the past: it picks the model settings using 2015–2018, then predicts every game of
2019–2025 and compares the predictions with what really happened. Lower numbers = better predictions.

## 4. Notebooks (local only)

The `notebooks/` folder is git-ignored: it's a personal space for exploration, not part of the repository.
Open it with `jupyter lab`, or in VS Code pick the **brasileirao** kernel (top right). If the kernel crashes or
you get `name 'np' is not defined`, click **Restart** and run the cells again from the top.

## 5. Update the website data by hand (optional)

```bash
python -m brasileirao.export --refresh
```

Writes the JSON files the site reads to `web/public/data/` (current chances for each model, remaining games,
weekly history, accuracy). Files are only rewritten when something changed. Options: `--accuracy` (re-run the
backtest), `--rebuild-history`, `--sims N`, `--no-schedule`. To preview the site locally see [web/README.md](web/README.md).

## 6. Tests

```bash
pytest
```

## Project layout

```
src/brasileirao/
  data.py          download and clean the match data
  fixtures.py      league table + list of remaining games
  models/elo.py    Elo strength scores
  models/ordered_logit.py   turns strength gaps into win/draw/loss chances
  models/poisson.py         Poisson / Dixon-Coles goals model (attack + defence per team)
  models/market.py          bookmaker odds → chances; team ratings learned from odds
  forecast.py      fits a model and prepares the simulator inputs (shared by all commands)
  simulate.py      plays the remaining games many times
  predict.py       command that puts it all together
  next_games.py    next games of the relegation fight and the impact of each result
  backtest.py      tests the model on past seasons
  export.py        writes the website's JSON files
  teams.py         team display names (São Paulo, Grêmio…) and short codes
notebooks/         personal exploration (git-ignored, local only)
tests/             automated tests
web/               the website (Next.js)
.github/workflows/ CI and the scheduled data update
```

## Rules used

- Libertadores = top 6 of the table (extra spots from cup winners are ignored).
- Relegation = bottom 4.
- Tiebreakers: points, wins, goal difference, goals scored.
