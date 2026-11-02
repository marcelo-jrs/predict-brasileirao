"""Predict the final standings of the current season.

Usage:
    python -m brasileirao.predict [--model elo|poisson|dixon-coles|market] [--sims 20000] [--refresh]
"""

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from brasileirao.data import PROJECT_ROOT, load_matches
from brasileirao.fixtures import league_table, remaining_fixtures, season_teams
from brasileirao.forecast import MODELS, MatchForecast, match_forecast
from brasileirao.simulate import position_matrix, simulate_season, summarize, teams_of

OUTPUT_DIR = PROJECT_ROOT / "outputs"


@dataclass
class SeasonSimulation:
    season: int
    played: pd.DataFrame  # games already played this season
    fixtures: pd.DataFrame  # remaining (home, away) pairs
    forecast: MatchForecast
    teams: list[str]  # alphabetical; column order of `positions` / `points`
    positions: np.ndarray  # (n_sims, n_teams)
    points: np.ndarray  # (n_sims, n_teams)
    outcomes: np.ndarray  # (n_sims, n_fixtures): 0 home win, 1 draw, 2 away win


def simulate_current_season(
    model: str, matches: pd.DataFrame, n_sims: int = 20_000, seed: int = 42
) -> SeasonSimulation:
    """Fit `model` on `matches` and simulate the rest of the latest season in `matches`."""
    season = int(matches.season.max())
    played = matches[matches.season == season]
    fixtures = remaining_fixtures(matches, season)
    forecast = match_forecast(model, matches, season, fixtures)
    positions, points, outcomes = simulate_season(
        played, fixtures, n_sims=n_sims, seed=seed, return_outcomes=True, **forecast.sim_inputs
    )
    teams = teams_of(played, fixtures)
    return SeasonSimulation(season, played, fixtures, forecast, teams, positions, points, outcomes)


def summary_table(sim: SeasonSimulation) -> pd.DataFrame:
    """One row per team: current table, model strengths and simulated chances."""
    current = league_table(sim.played, sim.teams).reset_index()
    summary = summarize(sim.positions, sim.points, sim.teams).merge(
        current[["team", "position", "played", "points"]].rename(
            columns={"position": "current_position", "points": "current_points"}
        ),
        on="team",
    )
    strengths = sim.forecast.strengths
    summary = summary.join(strengths, on="team")
    return summary[
        ["team", "current_position", "played", "current_points", *strengths.columns, "expected_points",
         "expected_position", "p_title", "p_top6", "p_relegation"]
    ]


def run(
    model: str = "elo", n_sims: int = 20_000, refresh: bool = False, output_dir: Path = OUTPUT_DIR, seed: int = 42
) -> pd.DataFrame:
    if model not in MODELS:
        raise ValueError(f"unknown model {model!r}; choose from {MODELS}")
    sim = simulate_current_season(model, load_matches(refresh=refresh), n_sims=n_sims, seed=seed)
    summary = summary_table(sim)

    output_dir.mkdir(parents=True, exist_ok=True)
    name = model.replace("-", "_")
    summary.to_csv(output_dir / f"predictions_{sim.season}_{name}.csv", index=False)
    position_matrix(sim.positions, sim.teams).loc[summary.team].to_csv(
        output_dir / f"positions_{sim.season}_{name}.csv"
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", choices=MODELS, default="elo", help="match model to use (default: elo)")
    parser.add_argument("--sims", type=int, default=20_000, help="number of Monte Carlo simulations")
    parser.add_argument("--refresh", action="store_true", help="re-download the latest results")
    args = parser.parse_args()

    summary = run(model=args.model, n_sims=args.sims, refresh=args.refresh)
    display = summary.copy()
    for col in ["p_title", "p_top6", "p_relegation"]:
        display[col] = (100 * display[col]).map(lambda v: f"{v:5.1f}%")
    display["expected_points"] = display.expected_points.round(1)
    display["expected_position"] = display.expected_position.round(1)
    print(f"Model: {args.model}\n")
    print(display.to_string(index=False))
    print(f"\nSaved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
