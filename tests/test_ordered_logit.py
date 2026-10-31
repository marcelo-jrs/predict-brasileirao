import numpy as np
import pandas as pd
import pytest
from scipy.special import expit

from brasileirao.models.elo import EloModel
from brasileirao.models.ordered_logit import X_SCALE, OrderedLogit


def _simulate(beta, c1, c2, n=20_000, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.normal(0, 150, n)
    latent = beta * x / X_SCALE + rng.logistic(size=n)
    results = np.where(latent < c1, "A", np.where(latent < c2, "D", "H"))
    return x, pd.Series(results)


def test_recovers_true_parameters():
    x, results = _simulate(beta=0.8, c1=-1.0, c2=0.2)
    model = OrderedLogit().fit(x, results)
    assert model.beta == pytest.approx(0.8, abs=0.05)
    assert model.c1 == pytest.approx(-1.0, abs=0.05)
    assert model.c2 == pytest.approx(0.2, abs=0.05)


def test_probabilities_valid_and_monotonic():
    x, results = _simulate(beta=0.8, c1=-1.0, c2=0.2)
    model = OrderedLogit().fit(x, results)
    p = model.predict(np.linspace(-500, 500, 51))
    assert np.allclose(p.sum(axis=1), 1)
    assert (p > 0).all()
    assert (np.diff(p[:, 0]) > 0).all()  # P(home) grows with the rating difference
    assert (np.diff(p[:, 2]) < 0).all()  # P(away) shrinks
    assert p[25, 0] == pytest.approx(1 - expit(0.2), abs=0.02)


def test_elo_with_outcome_model_gives_underdog_a_chance():
    model = EloModel()
    x, results = _simulate(beta=0.8, c1=-1.0, c2=0.2)
    model.outcome_model = OrderedLogit().fit(x, results)
    model.ratings = {"Strong": 1700, "Weak": 1350}
    p_home, p_draw, p_away = model.probabilities("Strong", "Weak")
    assert p_home + p_draw + p_away == pytest.approx(1)
    assert p_away > 0.01
