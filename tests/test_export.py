import json

import numpy as np
import pandas as pd
import pytest

from brasileirao.data import load_matches
from brasileirao.export import (
    WEB_MODELS,
    _clean,
    export_current,
    export_history,
    export_meta,
    snapshot_dates,
    write_json,
)


@pytest.fixture(scope="module")
def matches():
    return load_matches()


@pytest.fixture(scope="module")
def exported(tmp_path_factory, matches):
    out = tmp_path_factory.mktemp("data")
    schedule = pd.DataFrame(columns=["date", "home", "away"])
    changed, info = export_current(matches, out, n_sims=500, schedule=schedule)
    return out, changed, info, schedule


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_current_files_and_rerun_without_changes(exported, matches):
    out, changed, _, schedule = exported
    assert changed
    for name in ["table.json", "fixtures.json", "score_matrices.json", "scorelines.json"]:
        assert (out / name).exists()
    for model in WEB_MODELS:
        assert (out / "predictions" / f"{model}.json").exists()
    changed_again, _ = export_current(matches, out, n_sims=500, schedule=schedule)
    assert not changed_again


def test_predictions_are_consistent(exported):
    out, *_ = exported
    for model in WEB_MODELS:
        teams = _read(out / "predictions" / f"{model}.json")["teams"]
        assert len(teams) == 20
        assert sum(t["p_title"] for t in teams) == pytest.approx(1, abs=1e-3)
        assert sum(t["p_top6"] for t in teams) == pytest.approx(6, abs=1e-3)
        assert sum(t["p_relegation"] for t in teams) == pytest.approx(4, abs=1e-3)
        for t in teams:
            assert len(t["positions"]) == 20
            assert sum(t["positions"]) == pytest.approx(1, abs=1e-3)


def test_fixtures_have_probabilities_for_every_model(exported):
    out, _, info, _ = exported
    fixtures = _read(out / "fixtures.json")["fixtures"]
    assert len(fixtures) == info["games_remaining"]
    for f in fixtures:
        assert set(f["probs"]) == set(WEB_MODELS)
        for p in f["probs"].values():
            assert sum(p) == pytest.approx(1, abs=1e-3)
    grids = _read(out / "score_matrices.json")
    assert set(grids) == {"poisson"}
    assert len(grids["poisson"]) == len(fixtures)
    assert np.sum(grids["poisson"][0]) == pytest.approx(1, abs=1e-3)


def test_table_matches_games_played(exported):
    out, _, info, _ = exported
    rows = _read(out / "table.json")["rows"]
    assert [r["position"] for r in rows] == list(range(1, 21))
    assert sum(r["played"] for r in rows) == 2 * info["games_played"]
    assert all(r["points"] == 3 * r["wins"] + r["draws"] for r in rows)


def test_meta_only_changes_when_forced_or_content_differs(tmp_path, matches):
    info = {"season": 2026, "teams": ["Gremio"], "games_played": 1, "games_remaining": 2}
    assert export_meta(tmp_path, matches, info, 100, force=False)
    meta = _read(tmp_path / "meta.json")
    assert meta["teams"]["Gremio"] == {"name": "Grêmio", "short": "GRE"}
    assert not export_meta(tmp_path, matches, info, 100, force=False)
    assert export_meta(tmp_path, matches, {**info, "games_played": 2}, 100, force=False)


def test_snapshot_dates_are_mondays_after_first_game(matches):
    dates = snapshot_dates(matches, 2026, today=pd.Timestamp("2026-03-01").date())
    first_game = matches[matches.season == 2026].date.min()
    assert all(d.weekday() == 0 for d in dates)
    assert dates[0] > first_game
    assert dates[-1] <= pd.Timestamp("2026-03-01")


def test_history_reuses_unchanged_snapshots(tmp_path, matches):
    dates = snapshot_dates(matches, 2026)[:2]
    assert export_history(matches, tmp_path, models=["market"], n_sims=200, dates=dates)
    history = _read(tmp_path / "history" / "market.json")
    assert [s["date"] for s in history["snapshots"]] == [d.strftime("%Y-%m-%d") for d in dates]
    first = history["snapshots"][0]
    assert first["games"] == int(((matches.season == 2026) & (matches.date < dates[0])).sum())
    assert len(first["teams"]) == 20
    assert not export_history(matches, tmp_path, models=["market"], n_sims=200, dates=dates)


def test_clean_and_write_json(tmp_path):
    data = {"a": np.float64(np.nan), "b": np.int64(3), "c": np.array([0.5, 1.0])}
    assert _clean(data) == {"a": None, "b": 3, "c": [0.5, 1.0]}
    path = tmp_path / "x.json"
    assert write_json(path, data)
    assert not write_json(path, data)
