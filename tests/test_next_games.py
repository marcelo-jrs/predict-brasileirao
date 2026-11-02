import numpy as np
import pandas as pd
import pytest

from brasileirao.fixtures import remaining_fixtures
from brasileirao.next_games import conditional_relegation, next_games, pct, relegation_risk
from brasileirao.simulate import simulate_season, teams_of

SCORELINES = {
    "H": pd.DataFrame({"home_goals": [1], "away_goals": [0], "freq": [1.0]}),
    "D": pd.DataFrame({"home_goals": [0], "away_goals": [0], "freq": [1.0]}),
    "A": pd.DataFrame({"home_goals": [0], "away_goals": [1], "freq": [1.0]}),
}


def _simulated_season(n_sims=4000):
    played = pd.DataFrame(
        {
            "season": 2026,
            "home": ["A", "C", "E"],
            "away": ["B", "D", "F"],
            "home_goals": [2, 0, 1],
            "away_goals": [0, 0, 1],
        }
    )
    fixtures = remaining_fixtures(played, 2026)
    probs = np.tile([0.45, 0.27, 0.28], (len(fixtures), 1))
    positions, _, outcomes = simulate_season(
        played, fixtures, probs, SCORELINES, n_sims=n_sims, return_outcomes=True
    )
    return played, fixtures, positions, outcomes


def test_return_outcomes_keeps_the_default_return_unchanged():
    played, fixtures, positions, outcomes = _simulated_season(n_sims=50)
    probs = np.tile([0.45, 0.27, 0.28], (len(fixtures), 1))
    default = simulate_season(played, fixtures, probs, SCORELINES, n_sims=50)
    assert len(default) == 2
    assert (default[0] == positions).all()
    assert outcomes.shape == (50, len(fixtures))
    assert set(np.unique(outcomes)) <= {0, 1, 2}


def test_conditional_risks_average_back_to_todays_risk():
    """Law of total probability: today = P(win)*risk_if_win + P(draw)*risk_if_draw + P(lose)*risk_if_lose."""
    played, fixtures, positions, outcomes = _simulated_season()
    teams = teams_of(played, fixtures)
    today = relegation_risk(positions, bottom=2)
    for f, (home, away) in enumerate(fixtures.itertuples(index=False)):
        for team, is_home in ((home, True), (away, False)):
            t = teams.index(team)
            risk = conditional_relegation(positions, outcomes, f, t, is_home, bottom=2)
            win, lose = (0, 2) if is_home else (2, 0)
            freq = {name: (outcomes[:, f] == code).mean() for name, code in [("win", win), ("draw", 1), ("lose", lose)]}
            assert sum(freq[r] * risk[r] for r in freq) == pytest.approx(today[t])


def test_winning_never_hurts_on_average():
    played, fixtures, positions, outcomes = _simulated_season()
    teams = teams_of(played, fixtures)
    home, away = fixtures.iloc[0]
    risk = conditional_relegation(positions, outcomes, 0, teams.index(home), True, bottom=2)
    assert risk["win"] <= risk["draw"] <= risk["lose"]


def test_conditional_relegation_handcrafted():
    # 2 teams, 4 sims; team 0 is relegated (position 2 with bottom=1) only when it loses (outcome 2 at home)
    positions = np.array([[1, 2], [2, 1], [1, 2], [2, 1]])
    outcomes = np.array([[0], [2], [1], [2]])
    risk = conditional_relegation(positions, outcomes, fixture=0, team=0, is_home=True, bottom=1)
    assert risk == {"win": 0.0, "draw": 0.0, "lose": 1.0}
    away_view = conditional_relegation(positions, outcomes, fixture=0, team=1, is_home=False, bottom=1)
    assert away_view == {"win": 0.0, "draw": 1.0, "lose": 1.0}


def test_next_games_picks_first_unplayed_game_per_team_and_dedupes():
    fixtures = pd.DataFrame({"home": ["A", "C", "A", "E"], "away": ["B", "D", "C", "F"]})
    schedule = pd.DataFrame(
        {
            "date": pd.to_datetime(["2026-11-05", "2026-11-03", "2026-11-10", "2026-11-04", "2026-11-02"]),
            "home": ["A", "C", "A", "E", "X"],
            "away": ["B", "D", "C", "F", "Y"],  # X x Y is not a pending fixture -> ignored
        }
    )
    games, missing = next_games(schedule, fixtures, ["A", "B", "C", "G"])
    assert list(zip(games.home, games.away)) == [("C", "D"), ("A", "B")]  # sorted by date, A/B game once
    assert list(games.fixture) == [1, 0]
    assert missing == ["G"]


def test_pct_formatting():
    assert pct(0.0) == "<1%"
    assert pct(0.004) == "<1%"
    assert pct(0.45) == "45%"
    assert pct(1.0) == ">99%"
    assert pct(float("nan")) == "n/a"
