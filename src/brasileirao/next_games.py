"""Next games of the teams fighting relegation, and how each result would change their risk.

Usage:
    python -m brasileirao.next_games [--model elo|poisson|dixon-coles] [--sims 20000] [--min-risk 5]
                                     [--days 14] [--refresh]

How the "impact of a result" is measured (conditional probability):
    We simulate the rest of the season many times. To get "risk of relegation if team X loses its next game",
    we keep only the simulated seasons in which X lost that game, and count how often X was relegated in them.
"""

import argparse
from datetime import date, timedelta

import numpy as np
import pandas as pd
import requests

from brasileirao.data import fetch_espn_schedule, load_matches
from brasileirao.fixtures import league_table, season_teams
from brasileirao.forecast import MODELS
from brasileirao.predict import simulate_current_season

RELEGATED = 4
HOME_WIN, DRAW, AWAY_WIN = 0, 1, 2


def relegation_risk(positions: np.ndarray, bottom: int = RELEGATED) -> np.ndarray:
    """Share of simulated seasons in which each team finishes in the bottom `bottom` places."""
    return (positions > positions.shape[1] - bottom).mean(axis=0)


def conditional_relegation(
    positions: np.ndarray,
    outcomes: np.ndarray,
    fixture: int,
    team: int,
    is_home: bool,
    bottom: int = RELEGATED,
) -> dict[str, float]:
    """Relegation risk of `team` given each result of `fixture`, from the team's point of view.

    Returns {"win": ..., "draw": ..., "lose": ...}; NaN if a result never happened in the simulations.
    """
    relegated = positions[:, team] > positions.shape[1] - bottom
    win, lose = (HOME_WIN, AWAY_WIN) if is_home else (AWAY_WIN, HOME_WIN)
    risk = {}
    for name, code in [("win", win), ("draw", DRAW), ("lose", lose)]:
        happened = outcomes[:, fixture] == code
        risk[name] = float(relegated[happened].mean()) if happened.any() else float("nan")
    return risk


def next_games(schedule: pd.DataFrame, fixtures: pd.DataFrame, teams: list[str]) -> tuple[pd.DataFrame, list[str]]:
    """The next scheduled game of each team in `teams` (one row per game, sorted by date).

    Only games still missing from our results (`fixtures`) count. Returns (games, teams without a game).
    `games` has a `fixture` column with the row number of the game in `fixtures`.
    """
    fixture_index = {(h, a): i for i, (h, a) in enumerate(fixtures.itertuples(index=False))}
    pending = schedule[[(h, a) in fixture_index for h, a in zip(schedule.home, schedule.away)]]
    pending = pending.sort_values("date")

    rows, missing = {}, []
    for team in teams:
        games = pending[(pending.home == team) | (pending.away == team)]
        if games.empty:
            missing.append(team)
            continue
        game = games.iloc[0]
        rows[(game.home, game.away)] = game
    if not rows:
        return pd.DataFrame(columns=["date", "home", "away", "fixture"]), missing
    games = pd.DataFrame(rows.values()).sort_values("date").reset_index(drop=True)
    games["fixture"] = [fixture_index[(h, a)] for h, a in zip(games.home, games.away)]
    return games, missing


def pct(p: float) -> str:
    """Format a probability; simulations can't prove 0% or 100%, so extremes are shown as <1% / >99%."""
    if np.isnan(p):
        return "n/a"
    if p < 0.005:
        return "<1%"
    if p > 0.995:
        return ">99%"
    return f"{100 * p:.0f}%"


def ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def format_report(
    season: int,
    model: str,
    n_sims: int,
    min_risk: float,
    games: pd.DataFrame,
    probs: np.ndarray,
    table: pd.DataFrame,
    risk: dict[str, float],
    conditional: dict[str, dict[str, float]],
    missing: list[str],
) -> str:
    n_teams = len(table)
    lines = [
        f"Serie A {season} - the relegation fight: next games",
        f"Model: {model} | {n_sims:,} simulated seasons | "
        f"relegation risk = chance of finishing {n_teams - RELEGATED + 1}th-{n_teams}th",
        f"Teams shown: relegation risk today >= {100 * min_risk:g}%",
    ]
    name_width = max([len(t) for t in conditional] + [len("Relegation risk")])
    for game in games.itertuples(index=False):
        p_home, p_draw, p_away = probs[game.fixture]
        home, away = table.loc[game.home], table.loc[game.away]
        lines += [
            "",
            f"{game.date:%a %d/%m %H:%M}   "
            f"{game.home} ({home.points} pts, {ordinal(home.position)})  x  "
            f"{game.away} ({away.points} pts, {ordinal(away.position)})",
            f"  Chance:  {game.home} win {pct(p_home)}  |  draw {pct(p_draw)}  |  {game.away} win {pct(p_away)}",
            f"  {'Relegation risk':<{name_width}}  {'today':>6}  {'if win':>7}  {'if draw':>7}  {'if lose':>7}",
        ]
        for team in (game.home, game.away):
            if team in conditional:
                c = conditional[team]
                lines.append(
                    f"  {team:<{name_width}}  {pct(risk[team]):>6}  {pct(c['win']):>7}  "
                    f"{pct(c['draw']):>7}  {pct(c['lose']):>7}"
                )
    if missing:
        lines += ["", f"No game found in the schedule for: {', '.join(missing)}"]
    return "\n".join(lines)


def run(
    model: str = "elo",
    n_sims: int = 20_000,
    min_risk: float = 0.05,
    days: int = 14,
    refresh: bool = False,
    seed: int = 42,
    start: date | None = None,
) -> str:
    matches = load_matches(refresh=refresh)
    sim = simulate_current_season(model, matches, n_sims=n_sims, seed=seed)
    season, played, fixtures, teams = sim.season, sim.played, sim.fixtures, sim.teams
    positions, outcomes, probs = sim.positions, sim.outcomes, sim.forecast.probs
    risk = dict(zip(teams, relegation_risk(positions)))
    at_risk = sorted((t for t in teams if risk[t] >= min_risk), key=risk.get, reverse=True)

    start = start or date.today()
    try:
        schedule = fetch_espn_schedule(start, start + timedelta(days=days))
    except requests.RequestException as error:
        raise SystemExit(f"Could not fetch the schedule from ESPN: {error}") from error
    games, missing = next_games(schedule, fixtures, at_risk)

    conditional = {}
    for game in games.itertuples(index=False):
        for team, is_home in ((game.home, True), (game.away, False)):
            if team in at_risk:
                conditional[team] = conditional_relegation(
                    positions, outcomes, game.fixture, teams.index(team), is_home
                )

    table = league_table(played, season_teams(matches, season)).reset_index().set_index("team")
    return format_report(season, model, n_sims, min_risk, games, probs, table, risk, conditional, missing)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", choices=MODELS, default="elo", help="match model to use (default: elo)")
    parser.add_argument("--sims", type=int, default=20_000, help="number of Monte Carlo simulations")
    parser.add_argument(
        "--min-risk", type=float, default=5, help="show teams with relegation risk >= this %% (default: 5)"
    )
    parser.add_argument("--days", type=int, default=14, help="how many days ahead to look for games (default: 14)")
    parser.add_argument("--refresh", action="store_true", help="re-download the latest results")
    args = parser.parse_args()
    print(run(model=args.model, n_sims=args.sims, min_risk=args.min_risk / 100, days=args.days, refresh=args.refresh))


if __name__ == "__main__":
    main()
