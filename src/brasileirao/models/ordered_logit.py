"""Ordered logistic regression: turn one strength signal into P(home win), P(draw), P(away win).

Outcomes are ordered from the home team's point of view: away win < draw < home win.
A latent "home dominance" y* = beta * x + noise (logistic noise) falls into one of three bands:

    away win  if y* < c1
    draw      if c1 <= y* < c2
    home win  if y* >= c2

so  P(away) = sigmoid(c1 - beta*x)  and  P(away or draw) = sigmoid(c2 - beta*x).
Parameters are fitted by maximum likelihood (= minimizing log-loss).
"""

import numpy as np
from scipy.optimize import minimize
from scipy.special import expit

from brasileirao.evaluate import one_hot

# Rating differences are in the hundreds; rescaling keeps the optimizer well-conditioned
X_SCALE = 100.0


class OrderedLogit:
    def __init__(self) -> None:
        self.beta: float | None = None
        self.c1: float | None = None
        self.c2: float | None = None

    @staticmethod
    def _unpack(params: np.ndarray) -> tuple[float, float, float]:
        # c2 = c1 + exp(gap) guarantees c1 < c2 without constrained optimization
        beta, c1, log_gap = params
        return beta, c1, c1 + np.exp(log_gap)

    @staticmethod
    def _probs(x: np.ndarray, beta: float, c1: float, c2: float) -> np.ndarray:
        cdf_away = expit(c1 - beta * x)
        cdf_away_or_draw = expit(c2 - beta * x)
        return np.column_stack([1 - cdf_away_or_draw, cdf_away_or_draw - cdf_away, cdf_away])

    def fit(self, x, results) -> "OrderedLogit":
        """x: rating differences (home - away, incl. home advantage); results: 'H'/'D'/'A'."""
        x = np.asarray(x, dtype=float) / X_SCALE
        y = one_hot(results)

        def negative_log_likelihood(params):
            p = self._probs(x, *self._unpack(params))
            return -np.sum(y * np.log(np.clip(p, 1e-15, 1)))

        result = minimize(negative_log_likelihood, x0=[0.5, -1.0, 0.0], method="BFGS")
        self.beta, self.c1, self.c2 = self._unpack(result.x)
        return self

    def predict(self, x) -> np.ndarray:
        """Array (n, 3) with P(home), P(draw), P(away)."""
        x = np.atleast_1d(np.asarray(x, dtype=float)) / X_SCALE
        return self._probs(x, self.beta, self.c1, self.c2)
