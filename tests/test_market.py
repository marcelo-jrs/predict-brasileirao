import numpy as np
import pandas as pd
import pytest

from brasileirao.models.market import MarketRatings, implied_probabilities, ordered_logit_probs


def test_implied_probabilities_remove_margin():
    odds = pd.DataFrame({"odds_home": [2.0], "odds_draw": [3.5], "odds_away": [4.0]})
    p = implied_probabilities(odds)[0]
    assert p.sum() == pytest.approx(1)
    raw = np.array([1 / 2.0, 1 / 3.5, 1 / 4.0])
    assert p == pytest.approx(raw / raw.sum())
    assert p[0] > p[2]


def _odds_from(probs, margin=1.06):
    return 1 / (np.asarray(probs) * margin)


def _market_league(true_ratings, home_adv=0.4, c1=-0.5, c2=0.7, days=60):
    """Every pair plays at home once; odds are generated from known ratings."""
    rows, day = [], pd.Timestamp("2025-01-01")
    for _ in range(3):
        for h in true_ratings:
            for a in true_ratings:
                if h == a:
                    continue
                p = ordered_logit_probs(np.array([true_ratings[h] + home_adv - true_ratings[a]]), c1, c2)[0]
                oh, od, oa = _odds_from(p)
                rows.append((day, h, a, oh, od, oa))
                day += pd.Timedelta(days=1)
    return pd.DataFrame(rows, columns=["date", "home", "away", "odds_home", "odds_draw", "odds_away"])


def test_recovers_ratings_from_odds():
    true = {"A": 0.8, "B": 0.2, "C": -0.3, "D": -0.7}
    league = _market_league(true)
    model = MarketRatings(decay=0.0, ridge=0.0).fit(league, as_of=league.date.max() + pd.Timedelta(days=1))
    fitted = pd.Series(model.ratings)
    # ratings are only defined up to a constant shift; compare differences
    assert (fitted - fitted.mean()).to_numpy() == pytest.approx(
        (pd.Series(true) - np.mean(list(true.values()))).to_numpy(), abs=0.02
    )
    # c1 - home_adv = -0.9 and c2 - home_adv = 0.3, so the centre of the draw band is 0.3 below 0
    assert model.home_advantage == pytest.approx(0.3, abs=0.02)


def test_unknown_team_is_average_and_probs_sum_to_one():
    league = _market_league({"A": 0.5, "B": -0.5})
    model = MarketRatings().fit(league, as_of=league.date.max() + pd.Timedelta(days=1))
    p = model.probabilities_many(["A", "New"], ["New", "B"])
    assert np.allclose(p.sum(axis=1), 1)
    assert p[0, 0] > p[1, 0]
