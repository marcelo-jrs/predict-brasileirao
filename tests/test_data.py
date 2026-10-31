import pandas as pd
import pytest

from brasileirao.data import clean, load_matches


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
