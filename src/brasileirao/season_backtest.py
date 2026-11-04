"""Season-level backtest: are the title / top-6 / relegation probabilities honest?

For every test season we "travel back in time" to a few moments before the end (e.g. 15, 10 and 5 rounds left),
hide everything that happened afterwards, run exactly the same simulation as the website, and then compare the
predicted chances with how the season really ended.

Usage:
    python -m brasileirao.season_backtest [--sims 20000] [--models market elo poisson]
"""

import argparse

import numpy as np
import pandas as pd

from brasileirao.backtest import TEST_SEASONS
from brasileirao.data import PROJECT_ROOT, load_matches
from brasileirao.fixtures import league_table, season_teams
from brasileirao.predict import simulate_current_season, summary_table

OUTPUT_DIR = PROJECT_ROOT / "outputs"
ROUNDS_LEFT = [15, 10, 5]
GAMES_PER_ROUND = 10
EVENTS = {"title": "p_title", "top6": "p_top6", "relegation": "p_relegation"}
BINS = [0, 0.01, 0.1, 0.3, 0.5, 0.7, 0.9, 0.99, 1.0 + 1e-9]  # last group includes exactly 100%


def checkpoint(matches: pd.DataFrame, season: int, rounds_left: int) -> pd.Timestamp:
    """Date from which roughly `rounds_left` rounds of `season` remain (games on that date count as remaining)."""
    dates = matches.loc[matches.season == season, "date"].sort_values().reset_index(drop=True)
    return dates.iloc[len(dates) - rounds_left * GAMES_PER_ROUND]


def final_table(matches: pd.DataFrame, season: int) -> pd.DataFrame:
    return league_table(matches[matches.season == season], season_teams(matches, season)).reset_index()


def season_predictions(
    matches: pd.DataFrame,
    models: list[str],
    seasons: list[int] = TEST_SEASONS,
    rounds_left: list[int] = ROUNDS_LEFT,
    n_sims: int = 20_000,
) -> pd.DataFrame:
    """One row per (model, season, checkpoint, team) with the predicted chances and what really happened."""
    rows = []
    for season in seasons:
        final = final_table(matches, season).set_index("team")
        n_teams = len(final)
        for left in rounds_left:
            cutoff = checkpoint(matches, season, left)
            known = matches[matches.date < cutoff]
            for model in models:
                sim = simulate_current_season(model, known, n_sims=n_sims)
                summary = summary_table(sim).set_index("team")
                for team, r in summary.iterrows():
                    pos = int(final.loc[team, "position"])
                    rows.append(
                        {
                            "model": model,
                            "season": season,
                            "rounds_left": left,
                            "cutoff": cutoff.date(),
                            "games_remaining": len(sim.fixtures),
                            "team": team,
                            "current_position": int(r.current_position),
                            "final_position": pos,
                            "p_title": r.p_title,
                            "p_top6": r.p_top6,
                            "p_relegation": r.p_relegation,
                            "title": pos == 1,
                            "top6": pos <= 6,
                            "relegation": pos > n_teams - 4,
                        }
                    )
            print(f"  {season}, {left} rounds left (from {cutoff.date()}): done")
    return pd.DataFrame(rows)


def add_baselines(preds: pd.DataFrame) -> pd.DataFrame:
    """Two naive forecasters to compare with, on the same team-checkpoints.

    - "table as it stands": 100% for whatever the current position says (e.g. in the bottom 4 -> relegated).
    - "always the average": 1/20 title, 6/20 top 6, 4/20 relegation for every team.
    """
    one = preds[preds.model == preds.model.iloc[0]].copy()
    table = one.assign(
        model="table as it stands",
        p_title=(one.current_position == 1).astype(float),
        p_top6=(one.current_position <= 6).astype(float),
        p_relegation=(one.current_position > 16).astype(float),
    )
    average = one.assign(model="always the average", p_title=1 / 20, p_top6=6 / 20, p_relegation=4 / 20)
    return pd.concat([preds, table, average], ignore_index=True)


def brier_scores(preds: pd.DataFrame) -> pd.DataFrame:
    """Mean squared error between predicted chance and what happened (0 = perfect), per model and event."""
    out = {}
    for event, col in EVENTS.items():
        out[event] = preds.groupby("model").apply(
            lambda g: float(((g[col] - g[event].astype(float)) ** 2).mean()), include_groups=False
        )
    return pd.DataFrame(out)


def calibration_table(preds: pd.DataFrame, event: str) -> pd.DataFrame:
    """Group predictions by stated chance; compare the average stated chance with how often it really happened."""
    col = EVENTS[event]
    binned = preds.assign(bin=pd.cut(preds[col], BINS, include_lowest=True, right=False))
    return (
        binned.groupby(["model", "bin"], observed=True)
        .agg(n=(col, "size"), predicted=(col, "mean"), observed=(event, "mean"))
        .reset_index()
    )


def plot_calibration(preds: pd.DataFrame, models: list[str], path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    events = ["relegation", "top6"]
    fig, axes = plt.subplots(1, len(events), figsize=(12, 5.5))
    for ax, event in zip(axes, events):
        calib = calibration_table(preds[preds.model.isin(models)], event)
        ax.plot([0, 1], [0, 1], "k--", lw=1, label="perfect")
        for model in models:
            c = calib[calib.model == model]
            ax.plot(c.predicted, c.observed, "o-", label=model)
            for _, r in c.iterrows():
                ax.annotate(str(r.n), (r.predicted, r.observed), fontsize=7, xytext=(4, -10), textcoords="offset points")
        ax.set_title(f"{event}: predicted chance vs what happened")
        ax.set_xlabel("predicted chance")
        ax.set_ylabel("share that really happened")
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-0.02, 1.02)
        ax.legend(loc="upper left")
    fig.suptitle("Season backtest 2019–2025 (numbers = how many team-predictions in each group)")
    fig.tight_layout()
    fig.savefig(path, dpi=130)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sims", type=int, default=20_000)
    parser.add_argument("--models", nargs="+", default=["market", "elo", "poisson"])
    args = parser.parse_args()

    matches = load_matches()
    preds = season_predictions(matches, args.models, n_sims=args.sims)
    OUTPUT_DIR.mkdir(exist_ok=True)
    preds.to_csv(OUTPUT_DIR / "season_backtest.csv", index=False)

    scored = add_baselines(preds)
    pd.set_option("display.width", 140)
    print("\nBrier score (lower is better):")
    print(brier_scores(scored).round(4).to_string())
    for event in ["relegation", "top6"]:
        print(f"\nCalibration – {event}:")
        print(calibration_table(preds, event).round(3).to_string(index=False))
    plot_calibration(preds, args.models, OUTPUT_DIR / "season_backtest.png")
    print(f"\nSaved {OUTPUT_DIR / 'season_backtest.csv'} and season_backtest.png")


if __name__ == "__main__":
    main()
