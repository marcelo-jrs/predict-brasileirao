"""Export predictions as JSON files for the website (web/public/data/).

Usage:
    python -m brasileirao.export [--refresh] [--sims 20000] [--accuracy] [--rebuild-history] [--no-schedule]

Files (see web/README.md for the full schema):
    meta.json                 season, data freshness, models, team display names
    table.json                current standings
    predictions/<model>.json  simulated chances per team (title, top 6, relegation, every position)
    fixtures.json             remaining games with each model's home/draw/away chances (+ dates when known)
    score_matrices.json       Poisson score grids for the remaining games (for the in-browser simulator)
    scorelines.json           historical scoreline frequencies by result (for the in-browser simulator)
    history/<model>.json      weekly snapshots of the chances over the season
    accuracy.json             backtest leaderboard + calibration (only with --accuracy; slow)

A file is only rewritten when its content changes, so a run without new games produces no git diff.
"""

import argparse
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from brasileirao.backtest import TEST_MODELS, TEST_SEASONS, TUNE_SEASONS, calibration, holdout_predictions
from brasileirao.data import PROJECT_ROOT, fetch_espn_schedule, load_matches
from brasileirao.evaluate import brier, log_loss
from brasileirao.fixtures import league_table
from brasileirao.forecast import SCORELINE_FROM
from brasileirao.models.poisson import add_promoted_flags
from brasileirao.predict import SeasonSimulation, simulate_current_season, summary_table
from brasileirao.simulate import position_matrix, scoreline_distribution
from brasileirao.teams import display_name, short_code

WEB_DATA_DIR = PROJECT_ROOT / "web" / "public" / "data"
WEB_MODELS = ["market", "elo", "poisson"]  # the first one is the site's default
HISTORY_SIMS = 10_000
SCHEDULE_DAYS = 60
LIBERTADORES, RELEGATED = 6, 4
CALIBRATION_MODELS = ["market", "elo", "poisson", "closing_odds"]


# ---------------------------------------------------------------------------------------------- helpers
def _clean(obj):
    """Make numpy / pandas values JSON-friendly (NaN -> null)."""
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return _clean(obj.tolist())
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        return None if np.isnan(obj) else float(obj)
    return obj


def write_json(path: Path, data) -> bool:
    """Write `data` as compact JSON; return True if the file changed."""
    text = json.dumps(_clean(data), ensure_ascii=False, separators=(",", ":"))
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def _round(values, digits: int = 4):
    return np.round(np.asarray(values, dtype=float), digits)


def _form(played: pd.DataFrame, team: str, n: int = 5) -> list[str]:
    """Last `n` results of `team`, oldest first ('W', 'D', 'L')."""
    games = played[(played.home == team) | (played.away == team)].sort_values("date").tail(n)
    form = []
    for g in games.itertuples(index=False):
        scored, conceded = (g.home_goals, g.away_goals) if g.home == team else (g.away_goals, g.home_goals)
        form.append("W" if scored > conceded else "D" if scored == conceded else "L")
    return form


# ---------------------------------------------------------------------------------------------- current
def table_json(sim: SeasonSimulation) -> dict:
    table = league_table(sim.played, sim.teams).reset_index()
    rows = []
    for r in table.itertuples(index=False):
        rows.append(
            {
                "position": r.position,
                "team": r.team,
                "played": r.played,
                "wins": r.wins,
                "draws": r.draws,
                "losses": r.losses,
                "goals_for": r.goals_for,
                "goals_against": r.goals_against,
                "goal_diff": r.goal_diff,
                "points": r.points,
                "form": _form(sim.played, r.team),
            }
        )
    return {"season": sim.season, "rows": rows}


def predictions_json(model: str, sim: SeasonSimulation) -> dict:
    summary = summary_table(sim).set_index("team")
    positions = position_matrix(sim.positions, sim.teams)
    strength_cols = list(sim.forecast.strengths.columns)
    teams = []
    for team, row in summary.sort_values("expected_position").iterrows():
        teams.append(
            {
                "team": team,
                "expected_points": round(float(row.expected_points), 2),
                "expected_position": round(float(row.expected_position), 2),
                "p_title": round(float(row.p_title), 4),
                "p_top6": round(float(row.p_top6), 4),
                "p_relegation": round(float(row.p_relegation), 4),
                "positions": _round(positions.loc[team]),
                "strength": {c: row[c] for c in strength_cols},
            }
        )
    return {"model": model, "n_sims": int(sim.positions.shape[0]), "teams": teams}


def fixtures_json(sims: dict[str, SeasonSimulation], schedule: pd.DataFrame) -> dict:
    first = next(iter(sims.values()))
    when = {(h, a): d for h, a, d in zip(schedule.home, schedule.away, schedule.date)}
    fixtures = []
    for i, (home, away) in enumerate(first.fixtures.itertuples(index=False)):
        kickoff = when.get((home, away))
        fixtures.append(
            {
                "id": i,
                "home": home,
                "away": away,
                "date": kickoff.strftime("%Y-%m-%dT%H:%M") if kickoff is not None else None,
                "probs": {m: _round(s.forecast.probs[i]) for m, s in sims.items()},
            }
        )
    return {"fixtures": fixtures}


def score_matrices_json(sims: dict[str, SeasonSimulation]) -> dict:
    return {
        m: _round(s.forecast.sim_inputs["score_probs"], 5)
        for m, s in sims.items()
        if "score_probs" in s.forecast.sim_inputs
    }


def scorelines_json(matches: pd.DataFrame) -> dict:
    dist = scoreline_distribution(matches[matches.season >= SCORELINE_FROM])
    return {
        res: [[int(r.home_goals), int(r.away_goals), round(float(r.freq), 5)] for r in d.itertuples(index=False)]
        for res, d in dist.items()
    }


def fetch_schedule(enabled: bool) -> pd.DataFrame:
    empty = pd.DataFrame(columns=["date", "home", "away"])
    if not enabled:
        return empty
    try:
        return fetch_espn_schedule(date.today(), date.today() + timedelta(days=SCHEDULE_DAYS))
    except requests.RequestException as error:
        print(f"warning: could not fetch the schedule from ESPN ({error}); fixtures will have no dates")
        return empty


def export_current(matches: pd.DataFrame, out_dir: Path, n_sims: int, schedule: pd.DataFrame) -> tuple[bool, dict]:
    sims = {m: simulate_current_season(m, matches, n_sims=n_sims) for m in WEB_MODELS}
    first = sims[WEB_MODELS[0]]
    changed = write_json(out_dir / "table.json", table_json(first))
    for model, sim in sims.items():
        changed |= write_json(out_dir / "predictions" / f"{model}.json", predictions_json(model, sim))
    changed |= write_json(out_dir / "fixtures.json", fixtures_json(sims, schedule))
    changed |= write_json(out_dir / "score_matrices.json", score_matrices_json(sims))
    changed |= write_json(out_dir / "scorelines.json", scorelines_json(matches))
    info = {
        "season": first.season,
        "teams": first.teams,
        "games_played": len(first.played),
        "games_remaining": len(first.fixtures),
    }
    return changed, info


# ---------------------------------------------------------------------------------------------- history
def snapshot_dates(matches: pd.DataFrame, season: int, today: date | None = None) -> list[pd.Timestamp]:
    """Every Monday after the first game of `season` up to `today` (each team has played by then)."""
    games = matches[matches.season == season]
    first_monday = (games.date.min() + pd.offsets.Week(weekday=0)).normalize()
    last = pd.Timestamp(today or date.today())
    return list(pd.date_range(first_monday, last, freq="W-MON"))


def export_history(
    matches: pd.DataFrame,
    out_dir: Path,
    models: list[str] = WEB_MODELS,
    n_sims: int = HISTORY_SIMS,
    dates: list[pd.Timestamp] | None = None,
    rebuild: bool = False,
) -> bool:
    """Weekly "what would we have said on that Monday" snapshots, using only games played before it.

    A snapshot is (re)computed only if it is new or the number of games before its date changed
    (e.g. late-arriving results), so daily runs are cheap.
    """
    season = int(matches.season.max())
    dates = dates if dates is not None else snapshot_dates(matches, season)
    changed = False
    for model in models:
        path = out_dir / "history" / f"{model}.json"
        old = {} if rebuild or not path.exists() else json.loads(path.read_text(encoding="utf-8"))
        old_snaps = {s["date"]: s for s in old.get("snapshots", [])} if old.get("season") == season else {}
        snapshots = []
        for monday in dates:
            known = matches[matches.date < monday]
            n_games = int((known.season == season).sum())
            key = monday.strftime("%Y-%m-%d")
            if key in old_snaps and old_snaps[key]["games"] == n_games:
                snapshots.append(old_snaps[key])
                continue
            sim = simulate_current_season(model, known, n_sims=n_sims)
            summary = summary_table(sim).set_index("team")
            snapshots.append(
                {
                    "date": key,
                    "games": n_games,
                    "teams": {
                        team: {
                            "p_title": round(float(r.p_title), 4),
                            "p_top6": round(float(r.p_top6), 4),
                            "p_relegation": round(float(r.p_relegation), 4),
                            "expected_points": round(float(r.expected_points), 1),
                        }
                        for team, r in summary.iterrows()
                    },
                }
            )
            print(f"  history {model} {key}: {n_games} games")
        changed |= write_json(path, {"model": model, "season": season, "snapshots": snapshots})
    return changed


# ---------------------------------------------------------------------------------------------- accuracy
def export_accuracy(matches: pd.DataFrame, out_dir: Path) -> bool:
    """Backtest leaderboard and calibration on the test seasons, with the models' default (tuned) settings."""
    history = add_promoted_flags(matches[matches.season <= max(TEST_SEASONS)])
    test = history.season.isin(TEST_SEASONS)
    results = history.result[test]
    preds = holdout_predictions(history, {}, {}, {}, TEST_SEASONS)
    leaderboard = [
        {
            "id": key,
            "name": TEST_MODELS[key],
            "log_loss": round(log_loss(p, results), 4),
            "brier": round(brier(p, results), 4),
        }
        for key, p in preds.items()
    ]
    calib = {
        key: calibration(preds[key], results).round(4).to_dict(orient="records") for key in CALIBRATION_MODELS
    }
    return write_json(
        out_dir / "accuracy.json",
        {
            "tune_seasons": [TUNE_SEASONS[0], TUNE_SEASONS[-1]],
            "test_seasons": [TEST_SEASONS[0], TEST_SEASONS[-1]],
            "n_matches": int(test.sum()),
            "leaderboard": leaderboard,
            "calibration": calib,
        },
    )


# ---------------------------------------------------------------------------------------------- meta
def export_meta(out_dir: Path, matches: pd.DataFrame, info: dict, n_sims: int, force: bool) -> bool:
    meta = {
        "season": info["season"],
        "data_through": matches.date.max().strftime("%Y-%m-%d"),
        "n_sims": n_sims,
        "models": WEB_MODELS,
        "default_model": WEB_MODELS[0],
        "games_played": info["games_played"],
        "games_remaining": info["games_remaining"],
        "zones": {"libertadores": LIBERTADORES, "relegation": RELEGATED},
        "teams": {t: {"name": display_name(t), "short": short_code(t)} for t in info["teams"]},
    }
    path = out_dir / "meta.json"
    if path.exists() and not force:
        old = json.loads(path.read_text(encoding="utf-8"))
        old.pop("generated_at", None)
        if old == _clean(meta):
            return False
    meta["generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return write_json(path, meta)


def run(
    out_dir: Path = WEB_DATA_DIR,
    n_sims: int = 20_000,
    refresh: bool = False,
    accuracy: bool = False,
    history: bool = True,
    rebuild_history: bool = False,
    schedule: bool = True,
) -> bool:
    matches = load_matches(refresh=refresh)
    print("Simulating the current season...")
    changed, info = export_current(matches, out_dir, n_sims, fetch_schedule(schedule))
    if history:
        print("Updating weekly history...")
        changed |= export_history(matches, out_dir, rebuild=rebuild_history)
    if accuracy or not (out_dir / "accuracy.json").exists():
        print("Running the backtest for the accuracy page (takes ~1 minute)...")
        changed |= export_accuracy(matches, out_dir)
    changed |= export_meta(out_dir, matches, info, n_sims, force=changed)
    print(f"{'Updated' if changed else 'No changes in'} {out_dir}")
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, default=WEB_DATA_DIR, help="output folder")
    parser.add_argument("--sims", type=int, default=20_000, help="number of Monte Carlo simulations")
    parser.add_argument("--refresh", action="store_true", help="re-download the latest results")
    parser.add_argument("--accuracy", action="store_true", help="re-run the backtest for accuracy.json")
    parser.add_argument("--rebuild-history", action="store_true", help="recompute every weekly snapshot")
    parser.add_argument("--no-schedule", action="store_true", help="don't fetch fixture dates from ESPN")
    args = parser.parse_args()
    run(
        out_dir=args.out,
        n_sims=args.sims,
        refresh=args.refresh,
        accuracy=args.accuracy,
        rebuild_history=args.rebuild_history,
        schedule=not args.no_schedule,
    )


if __name__ == "__main__":
    main()
