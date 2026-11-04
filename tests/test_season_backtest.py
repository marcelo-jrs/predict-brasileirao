import pandas as pd
import pytest

from brasileirao.data import load_matches
from brasileirao.season_backtest import (
    add_baselines,
    brier_scores,
    calibration_table,
    checkpoint,
    season_predictions,
)


@pytest.fixture(scope="module")
def matches():
    return load_matches()


@pytest.fixture(scope="module")
def preds(matches):
    return season_predictions(matches, ["elo"], seasons=[2019], rounds_left=[5], n_sims=500)


def test_checkpoint_leaves_about_the_right_number_of_games(matches):
    cutoff = checkpoint(matches, 2019, 5)
    remaining = ((matches.season == 2019) & (matches.date >= cutoff)).sum()
    assert 50 <= remaining <= 60


def test_predictions_use_only_the_past_and_are_consistent(preds):
    assert len(preds) == 20
    assert preds.p_relegation.sum() == pytest.approx(4)
    assert preds.p_top6.sum() == pytest.approx(6)
    assert preds.relegation.sum() == 4 and preds.top6.sum() == 6 and preds.title.sum() == 1
    assert (preds.games_remaining >= 50).all()


def test_scores_and_baselines(preds):
    scored = add_baselines(preds)
    assert set(scored.model) == {"elo", "table as it stands", "always the average"}
    brier = brier_scores(scored)
    assert (brier.values >= 0).all() and (brier.values <= 1).all()
    # 5 rounds from the end, the simulation should beat knowing nothing
    assert brier.loc["elo", "relegation"] < brier.loc["always the average", "relegation"]
    calib = calibration_table(preds, "relegation")
    assert calib.n.sum() == 20
