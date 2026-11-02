"""Time-respecting evaluation of match models.

Season roles:
    2012–2014  burn-in (Elo ratings warm up, nothing is scored)
    2015–2018  tuning  (choose hyperparameters)
    2019–2025  test    (report the final, honest error)

Usage:
    python -m brasileirao.backtest
"""

import itertools

import numpy as np
import pandas as pd

from brasileirao.data import load_matches
from brasileirao.evaluate import baseline_probs, brier, log_loss, one_hot
from brasileirao.models import market, poisson
from brasileirao.models.elo import EloModel
from brasileirao.models.ordered_logit import OrderedLogit

TUNE_SEASONS = list(range(2015, 2019))
TEST_SEASONS = list(range(2019, 2026))

ELO_GRID = {
    "k": [6, 8, 10, 12, 15, 20],
    "home_advantage": [60, 70, 80, 90, 100, 110, 120, 140],
    "season_regression": [0.2, 0.33, 0.5],
}

POISSON_GRID = {
    "decay": [0.0005, 0.001, 0.002, 0.004],
    "alpha": [1e-3, 1e-2, 3e-2, 0.1, 0.3],
}

MARKET_GRID = {
    "decay": [0.0025, 0.005, 0.01, 0.02, 0.04],
}


def elo_grid_search(matches: pd.DataFrame, seasons: list[int], grid: dict = ELO_GRID) -> pd.DataFrame:
    """Log-loss of every hyperparameter combination, scored only on `seasons`."""
    mask = matches.season.isin(seasons)
    rows = []
    for values in itertools.product(*grid.values()):
        params = dict(zip(grid, values))
        probs = EloModel(**params).fit(matches).history.loc[mask, ["p_home", "p_draw", "p_away"]]
        rows.append({**params, "log_loss": log_loss(probs.to_numpy(), matches.result[mask])})
    return pd.DataFrame(rows).sort_values("log_loss").reset_index(drop=True)


def walk_forward_grid_search(
    matches: pd.DataFrame, seasons: list[int], walk_forward, grid: dict
) -> pd.DataFrame:
    """Log-loss of every combination for a walk-forward model (refit weekly). `matches` needs promoted flags."""
    results = matches.result[matches.season.isin(seasons)]
    rows = []
    for values in itertools.product(*grid.values()):
        params = dict(zip(grid, values))
        probs = walk_forward(matches, seasons, **params)
        rows.append({**params, "log_loss": log_loss(probs, results)})
    return pd.DataFrame(rows).sort_values("log_loss").reset_index(drop=True)


def expanding_window_ordered_logit(
    matches: pd.DataFrame, history: pd.DataFrame, test_seasons: list[int], first_train_season: int = 2015
) -> np.ndarray:
    """For each test season S, fit the ordered logit on seasons [first_train_season, S) and predict S."""
    probs = []
    for season in test_seasons:
        train = (matches.season >= first_train_season) & (matches.season < season)
        test = matches.season == season
        model = OrderedLogit().fit(history.rating_diff[train], matches.result[train])
        probs.append(model.predict(history.rating_diff[test]))
    return np.vstack(probs)


TEST_MODELS = {
    # id: display name (ids are used by the website)
    "baseline": "baseline (historical H/D/A frequencies)",
    "elo_fixed_draws": "Elo + fixed draw rate",
    "elo": "Elo + ordered logit",
    "poisson": "Poisson",
    "dixon_coles": "Dixon-Coles",
    "market": "Market ratings (learned from past odds)",
    "closing_odds": "Market closing odds (benchmark)",
}


def holdout_predictions(
    matches: pd.DataFrame,
    elo_params: dict,
    poisson_params: dict,
    market_params: dict,
    test_seasons: list[int] = TEST_SEASONS,
) -> dict[str, np.ndarray]:
    """P(home/draw/away) of every test-season match for each model in TEST_MODELS (keyed by id)."""
    test = matches.season.isin(test_seasons)
    history = EloModel(**elo_params).fit(matches).history
    return {
        "baseline": baseline_probs(matches.result[matches.season < min(test_seasons)], test.sum()),
        "elo_fixed_draws": history.loc[test, ["p_home", "p_draw", "p_away"]].to_numpy(),
        "elo": expanding_window_ordered_logit(matches, history, test_seasons),
        "poisson": poisson.walk_forward(matches, test_seasons, **poisson_params),
        "dixon_coles": poisson.walk_forward(matches, test_seasons, dixon_coles=True, **poisson_params),
        "market": market.walk_forward(matches, test_seasons, **market_params),
        # Benchmark only: needs each game's own closing odds, which future fixtures don't have yet
        "closing_odds": market.implied_probabilities(matches[test]),
    }


def compare_on_test(
    matches: pd.DataFrame,
    elo_params: dict,
    poisson_params: dict,
    market_params: dict,
    test_seasons: list[int] = TEST_SEASONS,
) -> pd.DataFrame:
    results = matches.result[matches.season.isin(test_seasons)]
    candidates = holdout_predictions(matches, elo_params, poisson_params, market_params, test_seasons)
    return pd.DataFrame(
        [
            {"model": TEST_MODELS[key], "log_loss": log_loss(p, results), "brier": brier(p, results)}
            for key, p in candidates.items()
        ]
    ).set_index("model")


def calibration(probs: np.ndarray, results: pd.Series, bins: int = 10) -> pd.DataFrame:
    """Group every predicted probability (home, draw and away alike) into bins and compare with reality.

    A well-calibrated model has `observed` close to `predicted` in every bin.
    """
    p = np.asarray(probs).ravel()
    happened = one_hot(results).ravel()
    edges = np.linspace(0, 1, bins + 1)
    which = np.clip(np.digitize(p, edges) - 1, 0, bins - 1)
    df = pd.DataFrame({"bin": which, "predicted": p, "observed": happened})
    out = df.groupby("bin").agg(predicted=("predicted", "mean"), observed=("observed", "mean"), n=("bin", "size"))
    return out.reset_index(drop=True)


def main() -> None:
    matches = poisson.add_promoted_flags(load_matches())
    matches = matches[matches.season <= max(TEST_SEASONS)]
    tune = f"{TUNE_SEASONS[0]}–{TUNE_SEASONS[-1]}"

    grid = elo_grid_search(matches, TUNE_SEASONS)
    print(f"Elo grid search on {tune} (top 5):")
    print(grid.head().round(4).to_string(index=False))
    best_elo = grid.iloc[0][list(ELO_GRID)].to_dict()

    grid = walk_forward_grid_search(matches, TUNE_SEASONS, poisson.walk_forward, POISSON_GRID)
    print(f"\nPoisson grid search on {tune} (top 5):")
    print(grid.head().to_string(index=False, float_format=lambda v: f"{v:.4g}"))
    best_poisson = grid.iloc[0][list(POISSON_GRID)].to_dict()

    grid = walk_forward_grid_search(matches, TUNE_SEASONS, market.walk_forward, MARKET_GRID)
    print(f"\nMarket ratings grid search on {tune}:")
    print(grid.to_string(index=False, float_format=lambda v: f"{v:.4g}"))
    best_market = grid.iloc[0][list(MARKET_GRID)].to_dict()

    print(f"\nTest seasons {TEST_SEASONS[0]}–{TEST_SEASONS[-1]}")
    print(f"  Elo params: {best_elo}\n  Poisson params: {best_poisson}\n  Market params: {best_market}")
    print(compare_on_test(matches, best_elo, best_poisson, best_market).round(4).to_string())


if __name__ == "__main__":
    main()
