# predict-brasileirao

Predicts the final table of the **Brasileirão Série A 2026**, focusing on:

- **Top 6** → Libertadores
- **Bottom 4** → relegation to Série B

How it works, in one line: each team gets a strength score (Elo) from past results, then the remaining games
are "played" 20,000 times on the computer, and we count how often each team finishes in each position.
For a hands-on explanation, see [notebooks/02_how_the_model_works.ipynb](notebooks/02_how_the_model_works.ipynb).

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
- `--model poisson` (or `dixon-coles`) uses the Poisson goals model instead of Elo (default `elo`).
  Results are saved per model, e.g. `outputs/predictions_2026_poisson.csv`.

It prints a table like this (one row per team):

| column | meaning |
|---|---|
| `current_position`, `current_points` | the table today |
| `elo` (Elo model) / `attack`, `defence` (Poisson models) | team strength (Elo: 1500 = average; Poisson: 1.0 = average, higher = better) |
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

## 4. Notebooks

```bash
jupyter lab
```

- `notebooks/01_eda.ipynb` – first look at the data (home advantage, goals, points needed for top 6 / to avoid relegation)
- `notebooks/02_how_the_model_works.ipynb` – the model explained step by step, with code to play with
- `notebooks/03_poisson_model.ipynb` – the Poisson goals model, hands-on

In VS Code: open the notebook and pick the **brasileirao** kernel (top right). If the kernel crashes or you get
`name 'np' is not defined`, click **Restart** and run the cells again from the top.

## 5. Tests

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
  simulate.py      plays the remaining games many times
  predict.py       command that puts it all together
  next_games.py    next games of the relegation fight and the impact of each result
  backtest.py      tests the model on past seasons
notebooks/         explanations and exploration
tests/             automated tests
```

## Rules used

- Libertadores = top 6 of the table (extra spots from cup winners are ignored).
- Relegation = bottom 4.
- Tiebreakers: points, wins, goal difference, goals scored.
