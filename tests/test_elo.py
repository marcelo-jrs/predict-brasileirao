import numpy as np
import pandas as pd
import pytest

from brasileirao.evaluate import brier, log_loss
from brasileirao.models.elo import EloModel, expected_score


def test_expected_score_properties():
    assert expected_score(0) == pytest.approx(0.5)
    assert expected_score(400) == pytest.approx(10 / 11)
    assert expected_score(100) + expected_score(-100) == pytest.approx(1)


def test_probabilities_sum_to_one_and_are_consistent():
    model = EloModel(home_advantage=60)
    model.ratings = {"A": 1600, "B": 1400}
    p_home, p_draw, p_away = model.probabilities("A", "B")
    assert p_home + p_draw + p_away == pytest.approx(1)
    assert p_home + 0.5 * p_draw == pytest.approx(expected_score(260))
    assert min(p_home, p_draw, p_away) >= 0


def _matches(rows):
    df = pd.DataFrame(rows, columns=["season", "home", "away", "home_goals", "away_goals"])
    df["date"] = pd.date_range("2020-01-01", periods=len(df))
    return df


def test_winner_gains_and_update_is_zero_sum():
    model = EloModel().fit(_matches([(2020, "A", "B", 2, 0)]))
    assert model.ratings["A"] > 1500 > model.ratings["B"]
    assert model.ratings["A"] + model.ratings["B"] == pytest.approx(3000)


def test_promoted_team_inherits_relegated_rating():
    rows = [(2020, "A", "B", 3, 0), (2020, "B", "A", 0, 3), (2021, "A", "C", 1, 1)]
    model = EloModel(season_regression=0.0).fit(_matches(rows))
    # C replaced B, so C started 2021 with B's (low) end-of-2020 rating instead of 1500
    first_2021 = model.history.iloc[2]
    e = first_2021.p_home + 0.5 * first_2021.p_draw
    assert e > expected_score(model.home_advantage)


def test_metrics_perfect_and_uniform():
    results = pd.Series(["H", "D", "A"])
    perfect = np.eye(3)
    uniform = np.full((3, 3), 1 / 3)
    assert log_loss(perfect, results) == pytest.approx(0, abs=1e-9)
    assert log_loss(uniform, results) == pytest.approx(np.log(3))
    assert brier(perfect, results) == 0
    assert brier(uniform, results) == pytest.approx(2 / 3)
