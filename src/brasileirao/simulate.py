"""Monte Carlo simulation of the remaining fixtures of a season."""

import numpy as np
import pandas as pd

from brasileirao.fixtures import league_table


def scoreline_distribution(matches: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Empirical frequency of each scoreline, split by result (H/D/A).

    Used to give simulated results realistic goals (needed for goal-difference tiebreakers).
    """
    counts = matches.groupby(["result", "home_goals", "away_goals"]).size().rename("freq").reset_index()
    return {
        res: g.assign(freq=g.freq / g.freq.sum()).reset_index(drop=True)
        for res, g in counts.groupby("result")
    }


def simulate_season(
    played: pd.DataFrame,
    fixtures: pd.DataFrame,
    probs: np.ndarray,
    scorelines: dict[str, pd.DataFrame],
    n_sims: int = 20_000,
    seed: int | None = 42,
) -> tuple[np.ndarray, np.ndarray]:
    """Simulate the remaining fixtures `n_sims` times.

    Args:
        played: matches already played this season.
        fixtures: remaining (home, away) pairs.
        probs: array (n_fixtures, 3) with P(home), P(draw), P(away) for each fixture.
        scorelines: output of `scoreline_distribution`.

    Returns:
        positions: int array (n_sims, n_teams) with the final position (1 = champion) of each team.
        points: int array (n_sims, n_teams) with the final points of each team.
        Teams are in alphabetical order (see `teams_of`).
    """
    rng = np.random.default_rng(seed)
    teams = teams_of(played, fixtures)
    idx = {t: i for i, t in enumerate(teams)}
    n_fix, n_teams = len(fixtures), len(teams)

    # 1. Sample results: 0 = home win, 1 = draw, 2 = away win
    u = rng.random((n_sims, n_fix))
    cum = np.cumsum(probs, axis=1)
    outcome = (u[:, :, None] > cum[None, :, :2]).sum(axis=2)

    # 2. Sample a realistic scoreline for each result
    home_goals = np.zeros((n_sims, n_fix), dtype=np.int64)
    away_goals = np.zeros((n_sims, n_fix), dtype=np.int64)
    for code, res in enumerate(["H", "D", "A"]):
        mask = outcome == code
        dist = scorelines[res]
        pick = rng.choice(len(dist), size=mask.sum(), p=dist.freq.to_numpy())
        home_goals[mask] = dist.home_goals.to_numpy()[pick]
        away_goals[mask] = dist.away_goals.to_numpy()[pick]

    # 3. Aggregate per team with matrix products: (sims x fixtures) @ (fixtures x teams)
    home_onehot = np.zeros((n_fix, n_teams))
    away_onehot = np.zeros((n_fix, n_teams))
    home_onehot[np.arange(n_fix), fixtures.home.map(idx).to_numpy()] = 1
    away_onehot[np.arange(n_fix), fixtures.away.map(idx).to_numpy()] = 1

    home_win, draw, away_win = (outcome == 0), (outcome == 1), (outcome == 2)
    points = (3 * home_win + draw) @ home_onehot + (3 * away_win + draw) @ away_onehot
    wins = home_win @ home_onehot + away_win @ away_onehot
    goals_for = home_goals @ home_onehot + away_goals @ away_onehot
    goals_against = away_goals @ home_onehot + home_goals @ away_onehot

    # 4. Add the current table
    current = league_table(played, teams).set_index("team").loc[teams]
    points += current.points.to_numpy()
    wins += current.wins.to_numpy()
    goals_for += current.goals_for.to_numpy()
    goals_against += current.goals_against.to_numpy()

    # 5. Rank with tiebreakers packed into one sortable key (+ random fraction for remaining ties)
    goal_diff = goals_for - goals_against
    key = ((points * 100 + wins) * 1000 + (goal_diff + 500)) * 1000 + goals_for
    key = key + rng.random(key.shape)
    order = np.argsort(-key, axis=1)
    positions = np.empty_like(order)
    np.put_along_axis(positions, order, np.arange(1, n_teams + 1)[None, :], axis=1)
    return positions, points.astype(np.int64)


def teams_of(played: pd.DataFrame, fixtures: pd.DataFrame) -> list[str]:
    return sorted(set(played.home) | set(played.away) | set(fixtures.home) | set(fixtures.away))


def summarize(
    positions: np.ndarray, points: np.ndarray, teams: list[str], top: int = 6, bottom: int = 4
) -> pd.DataFrame:
    """Turn simulated positions/points into per-team probabilities."""
    n_teams = len(teams)
    summary = pd.DataFrame(
        {
            "team": teams,
            "expected_points": points.mean(axis=0),
            "expected_position": positions.mean(axis=0),
            "p_title": (positions == 1).mean(axis=0),
            "p_top6": (positions <= top).mean(axis=0),
            "p_relegation": (positions > n_teams - bottom).mean(axis=0),
        }
    )
    return summary.sort_values("expected_position").reset_index(drop=True)


def position_matrix(positions: np.ndarray, teams: list[str]) -> pd.DataFrame:
    """P(team finishes in position p) – rows: teams, columns: positions 1..n."""
    n_teams = len(teams)
    counts = np.stack([(positions == p).mean(axis=0) for p in range(1, n_teams + 1)], axis=1)
    return pd.DataFrame(counts, index=teams, columns=range(1, n_teams + 1))
