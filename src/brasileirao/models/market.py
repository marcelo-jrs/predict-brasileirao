"""Betting-market models.

1. `implied_probabilities`: turn bookmaker odds into probabilities (remove the bookmaker's margin).
2. `MarketRatings`: learn one strength number per team from the market's recent opinions (odds), so we can
   price ANY fixture – including future games that have no odds yet.

   P(home/draw/away) follows an ordered logit on  x = rating[home] - rating[away]
   (same shape as the Elo draw fix), fitted to make our probabilities as close as possible to the market's
   (weighted cross-entropy, recent games weigh more). Home advantage lives in the cut points c1 < c2: they
   are not centred on 0, so even two equal teams give the home side the bigger share.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit

WINDOW_DAYS = 2 * 365


def implied_probabilities(odds: pd.DataFrame) -> np.ndarray:
    """(n, 3) probabilities from decimal odds columns odds_home/odds_draw/odds_away.

    1/odds sums to ~1.07 (the bookmaker's margin); dividing by that sum rescales to 1.
    """
    raw = 1 / odds[["odds_home", "odds_draw", "odds_away"]].to_numpy(dtype=float)
    return raw / raw.sum(axis=1, keepdims=True)


def ordered_logit_probs(x: np.ndarray, c1: float, c2: float) -> np.ndarray:
    p_away = expit(c1 - x)
    p_away_or_draw = expit(c2 - x)
    return np.column_stack([1 - p_away_or_draw, p_away_or_draw - p_away, p_away])


class MarketRatings:
    # Default decay chosen by grid search on the tuning seasons 2015–2018 (see backtest.py)
    def __init__(self, decay: float = 0.01, ridge: float = 0.01):
        self.decay = decay  # per day; half-life = ln(2) / decay days
        self.ridge = ridge  # keeps ratings near 0 (= average) when a team has few games

    def fit(self, matches: pd.DataFrame, as_of: pd.Timestamp) -> "MarketRatings":
        """Fit on games with odds played before `as_of` (within WINDOW_DAYS)."""
        train = matches[
            (matches.date < as_of)
            & (matches.date >= as_of - pd.Timedelta(days=WINDOW_DAYS))
            & matches.odds_home.notna()
        ]
        self.teams = sorted(set(train.home) | set(train.away))
        self._index = {t: i for i, t in enumerate(self.teams)}
        n = len(self.teams)

        home = train.home.map(self._index).to_numpy()
        away = train.away.map(self._index).to_numpy()
        target = implied_probabilities(train)
        weights = np.exp(-self.decay * (as_of - train.date).dt.days.to_numpy())
        weights = weights / weights.sum()

        def loss(params):
            ratings, c1, log_gap = params[:n], params[n], params[n + 1]
            probs = ordered_logit_probs(ratings[home] - ratings[away], c1, c1 + np.exp(log_gap))
            cross_entropy = -np.sum(weights * np.sum(target * np.log(np.clip(probs, 1e-12, 1)), axis=1))
            return cross_entropy + self.ridge * np.mean(ratings**2)

        start = np.concatenate([np.zeros(n), [-0.8, 0.2]])
        result = minimize(loss, start, method="L-BFGS-B")
        self.ratings = dict(zip(self.teams, result.x[:n]))
        self.c1 = result.x[n]
        self.c2 = self.c1 + np.exp(result.x[n + 1])
        return self

    @property
    def home_advantage(self) -> float:
        """Rating units the home side is 'worth': how far the middle of the draw band sits below 0."""
        return -(self.c1 + self.c2) / 2

    def probabilities_many(self, home, away) -> np.ndarray:
        """(n, 3): P(home win), P(draw), P(away win). Teams without recent odds count as average (0)."""
        r_home = np.array([self.ratings.get(t, 0.0) for t in home])
        r_away = np.array([self.ratings.get(t, 0.0) for t in away])
        return ordered_logit_probs(r_home - r_away, self.c1, self.c2)

    def probabilities(self, home: str, away: str) -> tuple[float, float, float]:
        return tuple(self.probabilities_many([home], [away])[0])

    def rating_table(self) -> pd.Series:
        return pd.Series(self.ratings, name="market_rating").sort_values(ascending=False)


def walk_forward(matches: pd.DataFrame, seasons: list[int], **params) -> np.ndarray:
    """Predict every match of `seasons`, refitting weekly on odds of games played before that week."""
    target = matches[matches.season.isin(seasons)]
    weeks = target.date.dt.to_period("W-MON").dt.start_time
    out = np.zeros((len(target), 3))
    for week_start in sorted(weeks.unique()):
        in_week = (weeks == week_start).to_numpy()
        games = target[in_week]
        model = MarketRatings(**params).fit(matches, as_of=week_start)
        out[in_week] = model.probabilities_many(games.home, games.away)
    return out
