"""Predict the final standings of the current season.

Usage:
    python -m brasileirao.predict [--sims 20000] [--refresh]
"""

import argparse
from pathlib import Path

import numpy as np

from brasileirao.data import PROJECT_ROOT, load_matches
from brasileirao.fixtures import league_table, remaining_fixtures, season_teams
from brasileirao.models.elo import EloModel
from brasileirao.simulate import position_matrix, scoreline_distribution, simulate_season, summarize, teams_of

OUTPUT_DIR = PROJECT_ROOT / "outputs"
SCORELINE_FROM = 2015
OUTCOME_MODEL_FROM = 2015


def run(n_sims: int = 20_000, refresh: bool = False, output_dir: Path = OUTPUT_DIR, seed: int = 42):
    matches = load_matches(refresh=refresh)
    season = int(matches.season.max())
    played = matches[matches.season == season]
    fixtures = remaining_fixtures(matches, season)

    model = EloModel().fit(matches)
    model.fit_outcome_model(matches, (matches.season >= OUTCOME_MODEL_FROM) & (matches.season < season))
    probs = np.array([model.probabilities(h, a) for h, a in fixtures.itertuples(index=False)])
    scorelines = scoreline_distribution(matches[matches.season >= SCORELINE_FROM])

    positions, points = simulate_season(played, fixtures, probs, scorelines, n_sims=n_sims, seed=seed)
    teams = teams_of(played, fixtures)

    current = league_table(played, season_teams(matches, season)).reset_index()
    summary = summarize(positions, points, teams).merge(
        current[["team", "position", "played", "points"]].rename(
            columns={"position": "current_position", "points": "current_points"}
        ),
        on="team",
    )
    summary["elo"] = summary.team.map(model.ratings).round(0)
    summary = summary[
        ["team", "current_position", "played", "current_points", "elo", "expected_points",
         "expected_position", "p_title", "p_top6", "p_relegation"]
    ]

    output_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output_dir / f"predictions_{season}_elo.csv", index=False)
    position_matrix(positions, teams).loc[summary.team].to_csv(output_dir / f"positions_{season}_elo.csv")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sims", type=int, default=20_000, help="number of Monte Carlo simulations")
    parser.add_argument("--refresh", action="store_true", help="re-download the latest results")
    args = parser.parse_args()

    summary = run(n_sims=args.sims, refresh=args.refresh)
    display = summary.copy()
    for col in ["p_title", "p_top6", "p_relegation"]:
        display[col] = (100 * display[col]).map(lambda v: f"{v:5.1f}%")
    display["expected_points"] = display.expected_points.round(1)
    display["expected_position"] = display.expected_position.round(1)
    print(display.to_string(index=False))
    print(f"\nSaved to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
