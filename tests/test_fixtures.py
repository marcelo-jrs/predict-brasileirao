import pandas as pd

from brasileirao.data import load_matches
from brasileirao.fixtures import league_table, remaining_fixtures, season_teams


def _match(home, away, hg, ag, season=2026):
    return {"season": season, "home": home, "away": away, "home_goals": hg, "away_goals": ag}


def test_league_table_points_and_tiebreakers():
    matches = pd.DataFrame(
        [
            _match("A", "B", 2, 0),  # A win
            _match("B", "C", 1, 1),  # draw
            _match("C", "A", 1, 0),  # C win
        ]
    )
    table = league_table(matches)
    # A and C both have 3 pts; B has 1 pt and must be last
    assert table.loc[3, "team"] == "B"
    assert table.loc[3, "points"] == 1
    assert set(table.loc[[1, 2], "team"]) == {"A", "C"}
    assert (table.points == 3 * table.wins + table.draws).all()


def test_goal_difference_breaks_tie():
    matches = pd.DataFrame([_match("A", "B", 5, 0), _match("C", "D", 1, 0)])
    table = league_table(matches)
    assert list(table.team[:2]) == ["A", "C"]


def test_played_plus_remaining_is_full_round_robin():
    matches = load_matches()
    season = matches.season.max()
    n_teams = len(season_teams(matches, season))
    played = (matches.season == season).sum()
    remaining = len(remaining_fixtures(matches, season))
    assert played + remaining == n_teams * (n_teams - 1)


def test_completed_season_has_no_remaining_fixtures():
    matches = load_matches()
    assert remaining_fixtures(matches, 2025).empty
