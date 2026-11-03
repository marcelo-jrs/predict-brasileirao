# Brasileirão 2026 – who makes the Libertadores, who goes down?

**🌐 <https://predict-brasileirao.vercel.app>** (Português / English)

Probabilistic forecasts for the final table of the Brazilian **Série A 2026**: each team's chance of winning the
title, finishing in the **top 6** (Libertadores) or in the **bottom 4** (relegation to Série B).
The forecasts update automatically after every round.

## How it works

1. **Rate the teams.** Three models estimate how strong each team is:
   - **Elo** – a rating learned from results (wins against strong teams count more).
   - **Poisson** – attack and defence strengths learned from scores, predicting the number of goals each side scores.
   - **Market** – ratings learned from bookmakers' odds of recent games, which also reflect injuries, suspensions
     and coaching changes.
2. **Price every remaining game.** Ratings plus home advantage give the chance of a home win, draw or away win
   (and, for Poisson, of every scoreline).
3. **Simulate the rest of the season 20,000 times.** Each simulation plays all remaining games, adds the points to
   the current table and applies the official tiebreakers (points, wins, goal difference, goals scored). A team's
   chance of, say, relegation is the share of simulations in which it finished 17th–20th.

The site also lets you pick results for upcoming games and re-runs the simulation in your browser (**What if…?**),
and shows how each team's chances evolved over the season.

## How good is it?

Model settings were chosen on the 2015–2018 seasons, then every one of the 2,660 games of 2019–2025 was predicted
using only information available before it. Lower is better:

| Model | Log-loss | Brier |
|---|---|---|
| Always predict the average home/draw/away rates | 1.0621 | 0.6410 |
| Elo | 1.0228 | 0.6137 |
| Poisson | 1.0218 | 0.6129 |
| **Market ratings** (default on the site) | **1.0153** | **0.6085** |
| *Bookmakers' closing odds (benchmark – only exist minutes before kick-off)* | *1.0007* | *0.5990* |

Calibration charts are on the site's **Accuracy** page.

## Architecture

```
GitHub Actions (twice a day)            repository                         Vercel
Python: download results, fit   ──▶  web/public/data/*.json   ──push──▶  static Next.js site
models, simulate, export JSON        (committed when it changes)           (rebuilt on every data commit)
```

Everything is precomputed, so the site is fully static. The in-browser simulator
([`web/src/lib/simulator.ts`](web/src/lib/simulator.ts)) is a TypeScript port of the Python one, and a test
checks that both give the same results.

**Data:** results and closing odds from [football-data.co.uk](https://www.football-data.co.uk/brazil.php)
(Série A since 2012), with the most recent results and the fixture schedule from ESPN's public scoreboard.

## Repository layout

```
src/brasileirao/        Python package
  data.py               download and clean match data
  fixtures.py           league table and remaining fixtures
  models/               elo.py, ordered_logit.py, poisson.py, market.py
  forecast.py           fit a model and build the simulator inputs
  simulate.py           Monte Carlo simulation of the rest of the season
  backtest.py           time-split evaluation of the models
  export.py             JSON files for the website
  predict.py            command-line forecast
  next_games.py         relegation fight: next games and risk if win / draw / lose
tests/                  pytest suite
web/                    website (Next.js, TypeScript, Tailwind, Recharts) – see web/README.md
.github/workflows/      CI and the scheduled data update
```

## Running it locally

Requires [conda](https://docs.conda.io/) (or mamba) for Python and Node.js 22 for the website.

```bash
conda env create -f environment.yml
conda activate brasileirao

python -m brasileirao.predict --refresh --model market   # forecast table in the terminal (models: elo, poisson, dixon-coles, market)
python -m brasileirao.next_games                         # next games of the teams fighting relegation
python -m brasileirao.backtest                           # reproduce the accuracy table above
pytest
```

For the website, see [web/README.md](web/README.md).

## Assumptions and limitations

- Libertadores = top 6 of the league table; extra places from cup winners are ignored. Relegation = bottom 4.
- Team ratings are frozen during a simulated season, so the chances are probably slightly overconfident.
- The models know nothing about line-ups or injuries, except what the market ratings pick up from the odds.
