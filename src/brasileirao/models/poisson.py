"""Poisson goals model (optionally with the Dixon-Coles low-score correction).

Each team has an ATTACK strength and a CONCEDE strength (how leaky its defence is). Expected goals:

    log(goals_home) = intercept + home + attack[home_team] + concede[away_team] (+ promoted effects)
    log(goals_away) = intercept        + attack[away_team] + concede[home_team] (+ promoted effects)

Logs turn the multiplication  average x home bonus x attack x leaky defence  into a sum, which is what a
Poisson regression (a GLM) fits. Recent matches get more weight: weight = exp(-decay * days_ago).
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.stats import poisson
from sklearn.linear_model import PoissonRegressor

MAX_GOALS = 10
WINDOW_DAYS = 4 * 365


def promoted_teams(matches: pd.DataFrame, season: int) -> set[str]:
    """Teams playing `season` that did not play the previous season."""
    def teams(s):
        g = matches[matches.season == s]
        return set(g.home) | set(g.away)

    previous = teams(season - 1)
    return teams(season) - previous if previous else set()


def add_promoted_flags(matches: pd.DataFrame) -> pd.DataFrame:
    flags = {s: promoted_teams(matches, s) for s in matches.season.unique()}
    return matches.assign(
        home_promoted=[h in flags[s] for h, s in zip(matches.home, matches.season)],
        away_promoted=[a in flags[s] for a, s in zip(matches.away, matches.season)],
    )


def dixon_coles_tau(h: np.ndarray, a: np.ndarray, lam: np.ndarray, mu: np.ndarray, rho: float) -> np.ndarray:
    """Correction factor for low scores (0-0, 1-0, 0-1, 1-1); 1 for every other score."""
    tau = np.ones(np.broadcast(h, a, lam, mu).shape)
    tau = np.where((h == 0) & (a == 0), 1 - lam * mu * rho, tau)
    tau = np.where((h == 0) & (a == 1), 1 + lam * rho, tau)
    tau = np.where((h == 1) & (a == 0), 1 + mu * rho, tau)
    tau = np.where((h == 1) & (a == 1), 1 - rho, tau)
    return tau


class PoissonModel:
    # Defaults chosen by grid search on log-loss over the tuning seasons 2015–2018 (see backtest.py)
    def __init__(self, decay: float = 0.002, alpha: float = 0.01, dixon_coles: bool = False):
        self.decay = decay  # per day; half-life = ln(2) / decay days
        self.alpha = alpha  # ridge penalty: pulls team strengths towards average when data is scarce
        self.dixon_coles = dixon_coles
        self.rho = 0.0

    # ------------------------------------------------------------------ design matrix
    def _design(self, attackers, defenders, is_home, att_promoted, def_promoted) -> np.ndarray:
        n = len(attackers)
        X = np.zeros((n, 2 * len(self.teams) + 3))
        att_idx = np.array([self._index.get(t, -1) for t in attackers])
        def_idx = np.array([self._index.get(t, -1) for t in defenders])
        rows = np.arange(n)
        # unknown teams (no matches in the window) keep 0 = league average
        X[rows[att_idx >= 0], att_idx[att_idx >= 0]] = 1
        X[rows[def_idx >= 0], len(self.teams) + def_idx[def_idx >= 0]] = 1
        X[:, -3] = is_home
        X[:, -2] = att_promoted
        X[:, -1] = def_promoted
        return X

    def _long(self, m: pd.DataFrame):
        """Two rows per match: home team attacking, away team attacking."""
        attackers = np.concatenate([m.home, m.away])
        defenders = np.concatenate([m.away, m.home])
        is_home = np.concatenate([np.ones(len(m)), np.zeros(len(m))])
        att_p = np.concatenate([m.home_promoted, m.away_promoted]).astype(float)
        def_p = np.concatenate([m.away_promoted, m.home_promoted]).astype(float)
        goals = np.concatenate([m.home_goals, m.away_goals])
        return attackers, defenders, is_home, att_p, def_p, goals

    # ------------------------------------------------------------------ fitting
    def fit(self, matches: pd.DataFrame, as_of: pd.Timestamp, promoted: set[str] = frozenset()) -> "PoissonModel":
        """Fit on matches played before `as_of` (within WINDOW_DAYS). `promoted`: newly promoted teams now."""
        train = matches[(matches.date < as_of) & (matches.date >= as_of - pd.Timedelta(days=WINDOW_DAYS))]
        self.promoted = set(promoted)
        self.teams = sorted(set(train.home) | set(train.away))
        self._index = {t: i for i, t in enumerate(self.teams)}

        attackers, defenders, is_home, att_p, def_p, goals = self._long(train)
        days_ago = (as_of - train.date).dt.days.to_numpy()
        weights = np.tile(np.exp(-self.decay * days_ago), 2)

        X = self._design(attackers, defenders, is_home, att_p, def_p)
        self.glm = PoissonRegressor(alpha=self.alpha, solver="newton-cholesky", max_iter=300)
        self.glm.fit(X, goals, sample_weight=weights)

        if self.dixon_coles:
            self.rho = self._fit_rho(train, weights[: len(train)])
        return self

    def _fit_rho(self, train: pd.DataFrame, weights: np.ndarray) -> float:
        lam, mu = self._expected(train.home, train.away, train.home_promoted, train.away_promoted)
        h, a = train.home_goals.to_numpy(), train.away_goals.to_numpy()

        def negative_log_likelihood(rho):
            tau = dixon_coles_tau(h, a, lam, mu, rho)
            return -np.sum(weights * np.log(np.clip(tau, 1e-10, None)))

        return float(minimize_scalar(negative_log_likelihood, bounds=(-0.3, 0.3), method="bounded").x)

    # ------------------------------------------------------------------ predicting
    def _expected(self, home, away, home_promoted, away_promoted):
        home, away = np.asarray(home), np.asarray(away)
        hp, ap = np.asarray(home_promoted, float), np.asarray(away_promoted, float)
        n = len(home)
        lam = self.glm.predict(self._design(home, away, np.ones(n), hp, ap))
        mu = self.glm.predict(self._design(away, home, np.zeros(n), ap, hp))
        return lam, mu

    def expected_goals(self, home: str, away: str) -> tuple[float, float]:
        lam, mu = self._expected([home], [away], [home in self.promoted], [away in self.promoted])
        return float(lam[0]), float(mu[0])

    def score_matrices(self, home, away, home_promoted=None, away_promoted=None) -> np.ndarray:
        """Array (n, G, G): P(home scores i, away scores j) for each match."""
        if home_promoted is None:
            home_promoted = [t in self.promoted for t in home]
            away_promoted = [t in self.promoted for t in away]
        lam, mu = self._expected(home, away, home_promoted, away_promoted)
        goals = np.arange(MAX_GOALS + 1)
        p_home = poisson.pmf(goals[None, :], lam[:, None])  # (n, G)
        p_away = poisson.pmf(goals[None, :], mu[:, None])
        matrix = p_home[:, :, None] * p_away[:, None, :]
        if self.dixon_coles:
            i, j = np.meshgrid(goals, goals, indexing="ij")
            matrix *= dixon_coles_tau(i[None], j[None], lam[:, None, None], mu[:, None, None], self.rho)
        return matrix / matrix.sum(axis=(1, 2), keepdims=True)

    def probabilities_many(self, home, away, home_promoted=None, away_promoted=None) -> np.ndarray:
        """Array (n, 3): P(home win), P(draw), P(away win)."""
        return outcome_probs(self.score_matrices(home, away, home_promoted, away_promoted))

    def probabilities(self, home: str, away: str) -> tuple[float, float, float]:
        return tuple(self.probabilities_many([home], [away])[0])

    def strengths(self) -> pd.DataFrame:
        """Team strengths as multipliers (1.0 = league average)."""
        n = len(self.teams)
        coef = self.glm.coef_
        return pd.DataFrame(
            {"attack": np.exp(coef[:n]), "defence": np.exp(-coef[n : 2 * n])}, index=self.teams
        ).sort_values("attack", ascending=False)


def outcome_probs(matrices: np.ndarray) -> np.ndarray:
    """Sum a score matrix into (home win, draw, away win)."""
    home = np.tril(matrices, k=-1).sum(axis=(1, 2))
    draw = np.trace(matrices, axis1=1, axis2=2)
    away = np.triu(matrices, k=1).sum(axis=(1, 2))
    return np.column_stack([home, draw, away])


def walk_forward(matches: pd.DataFrame, seasons: list[int], **params) -> np.ndarray:
    """Predict every match of `seasons`, refitting once a week on everything played before that week.

    `matches` must contain the promoted flags (see `add_promoted_flags`). Returns (n, 3) in match order.
    """
    target = matches[matches.season.isin(seasons)]
    weeks = target.date.dt.to_period("W-MON").dt.start_time
    out = np.zeros((len(target), 3))
    for week_start in sorted(weeks.unique()):
        in_week = (weeks == week_start).to_numpy()
        games = target[in_week]
        model = PoissonModel(**params).fit(matches, as_of=week_start)
        out[in_week] = model.probabilities_many(games.home, games.away, games.home_promoted, games.away_promoted)
    return out
