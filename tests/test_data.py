import pandas as pd
import pytest

from brasileirao.data import add_recent_matches, clean, espn_to_football_data, load_matches


@pytest.fixture(scope="module")
def matches():
    return load_matches()


def test_clean_drops_unplayed_and_renames():
    raw = pd.DataFrame(
        {
            "Season": [2016, 2016],
            "Date": ["10/12/2016", "11/12/2016"],
            "Home": ["A", "Chapecoense-SC"],
            "Away": ["B", "Atletico-MG"],
            "HG": [2, None],
            "AG": [1, None],
            "Res": ["H", None],
            "AvgCH": [2.0, 2.0],
            "AvgCD": [3.0, 3.0],
            "AvgCA": [4.0, 4.0],
        }
    )
    df = clean(raw)
    assert len(df) == 1
    assert df.loc[0, "home_goals"] == 2
    assert df["date"].dtype.kind == "M"


def test_complete_seasons_have_380_matches(matches):
    counts = matches.groupby("season").size()
    complete = counts.drop(index=[2016, matches["season"].max()])
    assert (complete == 380).all()


def test_result_matches_score(matches):
    expected = pd.Series("D", index=matches.index)
    expected[matches.home_goals > matches.away_goals] = "H"
    expected[matches.home_goals < matches.away_goals] = "A"
    assert (expected == matches.result).all()


def test_no_team_plays_itself(matches):
    assert (matches.home != matches.away).all()


def test_no_duplicate_games_after_top_up(matches):
    assert not matches.duplicated(["season", "home", "away"]).any()


def test_espn_names_are_translated():
    assert espn_to_football_data("Vasco da Gama") == "Vasco"
    assert espn_to_football_data("Grêmio") == "Gremio"
    assert espn_to_football_data("São Paulo") == "Sao Paulo"
    assert espn_to_football_data("Red Bull Bragantino") == "Bragantino"
    assert espn_to_football_data("Palmeiras") == "Palmeiras"


def test_add_recent_matches_skips_games_already_known():
    base = pd.DataFrame(
        {"season": [2026], "date": pd.to_datetime(["2026-10-29"]), "home": ["A"], "away": ["B"],
         "home_goals": [1], "away_goals": [0], "result": ["H"]}
    )
    recent = pd.DataFrame(
        {"date": pd.to_datetime(["2026-10-29", "2026-10-30"]), "home": ["A", "C"], "away": ["B", "A"],
         "home_goals": [9, 2], "away_goals": [9, 0], "result": ["D", "H"]}
    )
    combined = add_recent_matches(base, recent)
    assert len(combined) == 2
    assert combined.loc[combined.home == "A", "home_goals"].item() == 1  # football-data row kept
    assert combined.loc[combined.home == "C", "season"].item() == 2026
