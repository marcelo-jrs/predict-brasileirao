"""Elo rating model for football matches.

Each team has a rating; the rating difference (plus home advantage) gives the expected score
E = P(win) + 0.5 * P(draw). After each match, ratings move in proportion to the surprise (S - E).
"""

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from brasileirao.models.ordered_logit import OrderedLogit

BASE_RATING = 1500.0


def expected_score(rating_diff: float | np.ndarray) -> float | np.ndarray:
    """Logistic curve: probability-like expected score for a given rating difference."""
    return 1.0 / (1.0 + 10.0 ** (-rating_diff / 400.0))


def goal_diff_multiplier(goal_diff: int) -> float:
    """Bigger wins carry more information (World Football Elo Ratings formula)."""
    gd = abs(goal_diff)
    if gd <= 1:
        return 1.0
    if gd == 2:
        return 1.5
    return (11.0 + gd) / 8.0


@dataclass
class EloModel:
    # Defaults chosen by grid search on log-loss over the tuning seasons 2015–2018 (see backtest.py)
    k: float = 8.0
    home_advantage: float = 100.0
    season_regression: float = 0.33
    ratings: dict[str, float] = field(default_factory=dict, repr=False)
    draw_rate: float = field(default=0.27, repr=False)
    history: pd.DataFrame | None = field(default=None, repr=False)
    # Optional learned mapping rating_diff -> (H, D, A); falls back to the fixed draw-rate split
    outcome_model: OrderedLogit | None = field(default=None, repr=False)

    def rating_diff(self, home: str, away: str) -> float:
        return self.ratings.get(home, BASE_RATING) + self.home_advantage - self.ratings.get(away, BASE_RATING)

    def probabilities(self, home: str, away: str) -> tuple[float, float, float]:
        """(P(home win), P(draw), P(away win)) using the current ratings."""
        diff = self.rating_diff(home, away)
        if self.outcome_model is not None:
            return tuple(self.outcome_model.predict(diff)[0])
        return self._split(expected_score(diff))

    def fit_outcome_model(self, matches: pd.DataFrame, mask: pd.Series) -> "EloModel":
        """Fit the ordered logit on pre-match rating differences of the matches selected by `mask`."""
        self.outcome_model = OrderedLogit().fit(self.history.rating_diff[mask], matches.result[mask])
        return self

    def _split(self, e: float) -> tuple[float, float, float]:
        # Keep E = P(win) + 0.5 * P(draw); shrink the draw share for extreme mismatches so no prob < 0
        p_draw = min(self.draw_rate, 2 * e, 2 * (1 - e))
        return e - p_draw / 2, p_draw, 1 - e - p_draw / 2

    def _new_season(self, teams: list[str], previous: list[str]) -> None:
        """Regress ratings toward the mean; promoted teams inherit the average of the relegated ones."""
        for team in self.ratings:
            self.ratings[team] = BASE_RATING + (self.ratings[team] - BASE_RATING) * (1 - self.season_regression)
        relegated = [t for t in previous if t not in teams]
        promoted_rating = (
            float(np.mean([self.ratings[t] for t in relegated])) if relegated else BASE_RATING
        )
        for team in teams:
            if team not in previous:
                self.ratings[team] = promoted_rating

    def fit(self, matches: pd.DataFrame) -> "EloModel":
        """Run through matches chronologically, storing the pre-match probabilities of each match."""
        self.ratings = {}
        self.outcome_model = None
        self.draw_rate = float((matches.home_goals == matches.away_goals).mean())
        records = []
        previous_teams: list[str] = []
        for season, games in matches.groupby("season", sort=True):
            teams = sorted(set(games.home) | set(games.away))
            if previous_teams:
                self._new_season(teams, previous_teams)
            else:
                self.ratings.update({t: BASE_RATING for t in teams})
            for row in games.itertuples(index=False):
                diff = self.rating_diff(row.home, row.away)
                e = expected_score(diff)
                records.append((diff, *self._split(e)))
                s = 1.0 if row.home_goals > row.away_goals else 0.5 if row.home_goals == row.away_goals else 0.0
                delta = self.k * goal_diff_multiplier(row.home_goals - row.away_goals) * (s - e)
                self.ratings[row.home] += delta
                self.ratings[row.away] -= delta
            previous_teams = teams
        self.history = pd.DataFrame(
            records, columns=["rating_diff", "p_home", "p_draw", "p_away"], index=matches.index
        )
        return self

    def rating_table(self, teams: list[str] | None = None) -> pd.Series:
        ratings = pd.Series(self.ratings, name="elo")
        if teams is not None:
            ratings = ratings.reindex(teams)
        return ratings.sort_values(ascending=False)
