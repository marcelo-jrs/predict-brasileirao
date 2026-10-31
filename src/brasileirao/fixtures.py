"""Build league tables and the list of remaining fixtures for a season."""

from itertools import permutations

import pandas as pd

POINTS = {"W": 3, "D": 1, "L": 0}
# CBF tiebreakers (head-to-head and disciplinary criteria are ignored – they almost never matter)
SORT_KEYS = ["points", "wins", "goal_diff", "goals_for"]


def team_rows(matches: pd.DataFrame) -> pd.DataFrame:
    """Reshape matches (one row per match) into long format (one row per team per match)."""
    home = pd.DataFrame(
        {
            "team": matches["home"],
            "goals_for": matches["home_goals"],
            "goals_against": matches["away_goals"],
        }
    )
    away = pd.DataFrame(
        {
            "team": matches["away"],
            "goals_for": matches["away_goals"],
            "goals_against": matches["home_goals"],
        }
    )
    long = pd.concat([home, away], ignore_index=True)
    long["wins"] = (long.goals_for > long.goals_against).astype(int)
    long["draws"] = (long.goals_for == long.goals_against).astype(int)
    long["losses"] = (long.goals_for < long.goals_against).astype(int)
    return long


def league_table(matches: pd.DataFrame, teams: list[str] | None = None) -> pd.DataFrame:
    """Return the standings, sorted by CBF tiebreakers, with a 1-based `position` index.

    `teams` guarantees every team appears even if it has no matches yet.
    """
    long = team_rows(matches)
    table = long.groupby("team").agg(
        played=("wins", "size"),
        wins=("wins", "sum"),
        draws=("draws", "sum"),
        losses=("losses", "sum"),
        goals_for=("goals_for", "sum"),
        goals_against=("goals_against", "sum"),
    )
    if teams is not None:
        table = table.reindex(teams, fill_value=0)
    table["goal_diff"] = table.goals_for - table.goals_against
    table["points"] = 3 * table.wins + table.draws
    table = table.sort_values(SORT_KEYS, ascending=False).reset_index(names="team")
    table.index = pd.RangeIndex(1, len(table) + 1, name="position")
    return table


def season_teams(matches: pd.DataFrame, season: int) -> list[str]:
    s = matches[matches.season == season]
    return sorted(set(s.home) | set(s.away))


def remaining_fixtures(matches: pd.DataFrame, season: int) -> pd.DataFrame:
    """All (home, away) pairs of the double round-robin not yet played in `season`."""
    teams = season_teams(matches, season)
    played = set(zip(matches.loc[matches.season == season, "home"], matches.loc[matches.season == season, "away"]))
    pending = [(h, a) for h, a in permutations(teams, 2) if (h, a) not in played]
    return pd.DataFrame(pending, columns=["home", "away"])
