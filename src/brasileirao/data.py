"""Download and clean Brasileirão Série A match data from football-data.co.uk."""

from pathlib import Path

import pandas as pd
import requests

DATA_URL = "https://www.football-data.co.uk/new/BRA.csv"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "BRA.csv"

COLUMNS = {
    "Season": "season",
    "Date": "date",
    "Home": "home",
    "Away": "away",
    "HG": "home_goals",
    "AG": "away_goals",
    "Res": "result",
    # Average closing odds across bookmakers (used later by the market baseline)
    "AvgCH": "odds_home",
    "AvgCD": "odds_draw",
    "AvgCA": "odds_away",
}


def download(path: Path = RAW_PATH, refresh: bool = False) -> Path:
    """Download the raw CSV unless a cached copy already exists."""
    if path.exists() and not refresh:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(DATA_URL, timeout=60)
    response.raise_for_status()
    path.write_bytes(response.content)
    return path


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    """Select/rename columns, parse dates, drop unplayed matches and sort chronologically."""
    df = raw[list(COLUMNS)].rename(columns=COLUMNS)
    df["date"] = pd.to_datetime(df["date"], format="%d/%m/%Y")
    # Rows without a score are matches that never happened (e.g. Chapecoense x Atlético-MG, 2016)
    df = df.dropna(subset=["home_goals", "away_goals"])
    df = df.astype({"season": int, "home_goals": int, "away_goals": int})
    return df.sort_values(["date", "home"]).reset_index(drop=True)


def load_matches(refresh: bool = False) -> pd.DataFrame:
    """Return the clean match dataset (one row per played match)."""
    path = download(refresh=refresh)
    raw = pd.read_csv(path, encoding="utf-8-sig")
    return clean(raw)
