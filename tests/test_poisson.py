import numpy as np
import pandas as pd
import pytest
from scipy.stats import poisson as poisson_dist

from brasileirao.models.poisson import (
    PoissonModel,
    add_promoted_flags,
    dixon_coles_tau,
    outcome_probs,
    promoted_teams,
)
from brasileirao.simulate import _sample_scores


def _fake_league(n_rounds=6, seed=0):
    """Synthetic double round-robins where 'Strong' scores a lot and 'Weak' concedes a lot."""
    rng = np.random.default_rng(seed)
    attack = {"Strong": 1.6, "Mid1": 1.0, "Mid2": 1.0, "Weak": 0.7}
    leaky = {"Strong": 0.7, "Mid1": 1.0, "Mid2": 1.0, "Weak": 1.5}
    rows, day = [], pd.Timestamp("2020-01-01")
    for _ in range(n_rounds):
        for h in attack:
            for a in attack:
                if h == a:
                    continue
                hg = rng.poisson(1.3 * attack[h] * leaky[a])
                ag = rng.poisson(1.0 * attack[a] * leaky[h])
                rows.append((2020, day, h, a, hg, ag))
                day += pd.Timedelta(days=1)
    df = pd.DataFrame(rows, columns=["season", "date", "home", "away", "home_goals", "away_goals"])
    return add_promoted_flags(df)


def test_learns_attack_and_defence_ordering():
    m = _fake_league()
    model = PoissonModel(decay=0.0, alpha=1e-4).fit(m, as_of=m.date.max() + pd.Timedelta(days=1))
    s = model.strengths()
    assert s.attack.idxmax() == "Strong"
    assert s.defence.idxmin() == "Weak"
    lam, mu = model.expected_goals("Strong", "Weak")
    assert lam > 2 * mu


def test_score_matrix_sums_to_one_and_matches_poisson():
    m = _fake_league()
    model = PoissonModel(decay=0.0).fit(m, as_of=m.date.max() + pd.Timedelta(days=1))
    matrix = model.score_matrices(["Mid1"], ["Mid2"])[0]
    assert matrix.sum() == pytest.approx(1)
    lam, mu = model.expected_goals("Mid1", "Mid2")
    assert matrix[2, 1] == pytest.approx(poisson_dist.pmf(2, lam) * poisson_dist.pmf(1, mu), rel=1e-3)
    assert sum(model.probabilities("Mid1", "Mid2")) == pytest.approx(1)


def test_fit_ignores_future_matches():
    m = _fake_league()
    cutoff = m.date.iloc[20]
    a = PoissonModel().fit(m, as_of=cutoff)
    b = PoissonModel().fit(m[m.date < cutoff], as_of=cutoff)
    assert np.allclose(a.glm.coef_, b.glm.coef_)


def test_dixon_coles_tau_preserves_total_probability():
    lam, mu, rho = 1.4, 1.1, -0.1
    g = np.arange(11)
    i, j = np.meshgrid(g, g, indexing="ij")
    base = poisson_dist.pmf(i, lam) * poisson_dist.pmf(j, mu)
    adjusted = base * dixon_coles_tau(i, j, lam, mu, rho)
    assert adjusted.sum() == pytest.approx(base.sum())
    assert adjusted[0, 0] > base[0, 0]  # negative rho -> more 0-0 draws


def test_outcome_probs_reads_the_right_triangles():
    matrix = np.zeros((1, 3, 3))
    matrix[0, 2, 0] = 0.5  # home 2-0
    matrix[0, 1, 1] = 0.3  # draw
    matrix[0, 0, 1] = 0.2  # away 0-1
    assert np.allclose(outcome_probs(matrix), [[0.5, 0.3, 0.2]])


def test_promoted_teams():
    df = pd.DataFrame({"season": [2020, 2021], "home": ["A", "A"], "away": ["B", "C"]})
    assert promoted_teams(df, 2021) == {"C"}
    assert promoted_teams(df, 2020) == set()


def test_sample_scores_follows_matrix():
    matrix = np.zeros((1, 3, 3))
    matrix[0, 1, 0] = 0.75
    matrix[0, 2, 2] = 0.25
    home, away = _sample_scores(matrix, 20_000, np.random.default_rng(0))
    assert set(zip(home[:, 0], away[:, 0])) == {(1, 0), (2, 2)}
    assert ((home == 1) & (away == 0)).mean() == pytest.approx(0.75, abs=0.02)
