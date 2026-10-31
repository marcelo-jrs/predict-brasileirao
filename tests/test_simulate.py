import numpy as np
import pandas as pd
import pytest

from brasileirao.fixtures import league_table, remaining_fixtures
from brasileirao.simulate import scoreline_distribution, simulate_season, summarize, teams_of

SCORELINES = {
    "H": pd.DataFrame({"home_goals": [1], "away_goals": [0], "freq": [1.0]}),
    "D": pd.DataFrame({"home_goals": [0], "away_goals": [0], "freq": [1.0]}),
    "A": pd.DataFrame({"home_goals": [0], "away_goals": [1], "freq": [1.0]}),
}


def _season():
    played = pd.DataFrame(
        {"season": 2026, "home": ["A", "C"], "away": ["B", "D"], "home_goals": [3, 0], "away_goals": [0, 0]}
    )
    fixtures = remaining_fixtures(played, 2026)
    return played, fixtures


def test_deterministic_simulation_matches_manual_table():
    played, fixtures = _season()
    probs = np.tile([1.0, 0.0, 0.0], (len(fixtures), 1))  # every home team wins 1-0
    positions, points = simulate_season(played, fixtures, probs, SCORELINES, n_sims=5)

    final = pd.concat(
        [played, fixtures.assign(season=2026, home_goals=1, away_goals=0)], ignore_index=True
    )
    expected = league_table(final)
    teams = teams_of(played, fixtures)
    for i, team in enumerate(teams):
        row = expected[expected.team == team]
        assert (positions[:, i] == row.index[0]).all()
        assert (points[:, i] == row.points.iloc[0]).all()


def test_positions_are_permutations_and_probabilities_add_up():
    played, fixtures = _season()
    probs = np.tile([0.45, 0.27, 0.28], (len(fixtures), 1))
    positions, points = simulate_season(played, fixtures, probs, SCORELINES, n_sims=2000)
    n_teams = positions.shape[1]
    assert (np.sort(positions, axis=1) == np.arange(1, n_teams + 1)).all()

    summary = summarize(positions, points, teams_of(played, fixtures), top=1, bottom=1)
    assert summary.p_title.sum() == pytest.approx(1)
    assert summary.p_top6.sum() == pytest.approx(1)
    assert summary.p_relegation.sum() == pytest.approx(1)


def test_scoreline_distribution_is_consistent_with_result():
    matches = pd.DataFrame(
        {"home_goals": [1, 2, 0, 1], "away_goals": [0, 0, 0, 3], "result": ["H", "H", "D", "A"]}
    )
    dist = scoreline_distribution(matches)
    assert dist["H"].freq.sum() == pytest.approx(1)
    assert (dist["H"].home_goals > dist["H"].away_goals).all()
    assert (dist["A"].home_goals < dist["A"].away_goals).all()
