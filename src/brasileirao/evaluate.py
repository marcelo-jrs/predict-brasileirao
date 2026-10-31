"""Metrics for probabilistic predictions of match outcomes (home / draw / away)."""

import numpy as np
import pandas as pd

OUTCOMES = ["H", "D", "A"]


def one_hot(results: pd.Series) -> np.ndarray:
    return np.column_stack([(results == o).to_numpy() for o in OUTCOMES]).astype(float)


def log_loss(probs: np.ndarray, results: pd.Series) -> float:
    """Mean negative log-probability assigned to what actually happened (lower is better)."""
    p = np.clip(np.asarray(probs)[one_hot(results).astype(bool)], 1e-15, 1)
    return float(-np.log(p).mean())


def brier(probs: np.ndarray, results: pd.Series) -> float:
    """Mean squared error between probability vectors and one-hot outcomes (lower is better)."""
    return float(((np.asarray(probs) - one_hot(results)) ** 2).sum(axis=1).mean())


def baseline_probs(train_results: pd.Series, n: int) -> np.ndarray:
    """'Know-nothing' model: always predict the historical outcome frequencies."""
    freqs = train_results.value_counts(normalize=True).reindex(OUTCOMES).to_numpy()
    return np.tile(freqs, (n, 1))
