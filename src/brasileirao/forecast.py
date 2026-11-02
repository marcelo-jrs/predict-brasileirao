"""Fit a match model and turn it into inputs for the season simulator.

Shared by the CLI (`predict`), `next_games` and the website export, so every entry point uses the same models.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from brasileirao.models.elo import EloModel
from brasileirao.models.market import MarketRatings
from brasileirao.models.poisson import PoissonModel, add_promoted_flags, outcome_probs, promoted_teams
from brasileirao.simulate import scoreline_distribution

MODELS = ["elo", "poisson", "dixon-coles", "market"]
SCORELINE_FROM = 2015
OUTCOME_MODEL_FROM = 2015


@dataclass
class MatchForecast:
    probs: np.ndarray  # (n_fixtures, 3): P(home win), P(draw), P(away win)
    sim_inputs: dict  # keyword arguments for `simulate_season` (probs + scorelines, or score_probs)
    strengths: pd.DataFrame  # one row per team, model-specific rating columns


def match_forecast(model: str, matches: pd.DataFrame, season: int, fixtures: pd.DataFrame) -> MatchForecast:
    """Fit `model` on `matches` (everything known so far) and predict every fixture in `fixtures`."""
    as_of = matches.date.max() + pd.Timedelta(days=1)

    if model == "elo":
        elo = EloModel().fit(matches)
        elo.fit_outcome_model(matches, (matches.season >= OUTCOME_MODEL_FROM) & (matches.season < season))
        probs = np.array([elo.probabilities(h, a) for h, a in fixtures.itertuples(index=False)]).reshape(-1, 3)
        strengths = pd.DataFrame({"elo": pd.Series(elo.ratings).round(0)})
        return MatchForecast(probs, {"probs": probs, "scorelines": _scorelines(matches)}, strengths)

    if model in ("poisson", "dixon-coles"):
        flagged = add_promoted_flags(matches)
        poisson = PoissonModel(dixon_coles=model == "dixon-coles").fit(
            flagged, as_of, promoted_teams(flagged, season)
        )
        score_probs = poisson.score_matrices(list(fixtures.home), list(fixtures.away))
        return MatchForecast(outcome_probs(score_probs), {"score_probs": score_probs}, poisson.strengths().round(2))

    if model == "market":
        market = MarketRatings().fit(matches, as_of)
        probs = market.probabilities_many(fixtures.home, fixtures.away)
        strengths = market.rating_table().round(2).to_frame()
        return MatchForecast(probs, {"probs": probs, "scorelines": _scorelines(matches)}, strengths)

    raise ValueError(f"unknown model {model!r}; choose from {MODELS}")


def _scorelines(matches: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return scoreline_distribution(matches[matches.season >= SCORELINE_FROM])
