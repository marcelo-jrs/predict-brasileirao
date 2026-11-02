"""Download and clean Brasileirão Série A match data.

Main source: football-data.co.uk (all seasons since 2012, with betting odds), but it is only updated a
couple of times a week. The most recent games of the current season are topped up from ESPN's public
scoreboard (results only, no odds).
"""

import unicodedata
import warnings
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

DATA_URL = "https://www.football-data.co.uk/new/BRA.csv"
ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/bra.1/scoreboard"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = PROJECT_ROOT / "data" / "raw" / "BRA.csv"
ESPN_PATH = PROJECT_ROOT / "data" / "raw" / "espn_recent.csv"

# ESPN name (accents removed) -> football-data name, only where they differ
ESPN_TEAM_NAMES = {
    "Botafogo": "Botafogo RJ",
    "Chapecoense": "Chapecoense-SC",
    "Flamengo": "Flamengo RJ",
    "Red Bull Bragantino": "Bragantino",
    "Vasco da Gama": "Vasco",
}

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


def load_matches(refresh: bool = False, top_up: bool = True) -> pd.DataFrame:
    """Return the clean match dataset (one row per played match).

    With `top_up=True`, games of the current season played after football-data's last update are
    added from ESPN (their odds columns are empty).
    """
    path = download(refresh=refresh)
    raw = pd.read_csv(path, encoding="utf-8-sig")
    matches = clean(raw)
    if not top_up:
        return matches
    return add_recent_matches(matches, recent_espn_matches(matches, refresh=refresh))


def add_recent_matches(matches: pd.DataFrame, recent: pd.DataFrame) -> pd.DataFrame:
    """Append `recent` games of the current season that are not in `matches` yet.

    In a double round-robin each (home, away) pair is played once per season, so it identifies a game.
    """
    if recent.empty:
        return matches
    season = matches.season.max()
    known = set(zip(matches.loc[matches.season == season, "home"], matches.loc[matches.season == season, "away"]))
    new = recent[[(h, a) not in known for h, a in zip(recent.home, recent.away)]]
    combined = pd.concat([matches, new.assign(season=season)], ignore_index=True)
    return combined.sort_values(["date", "home"]).reset_index(drop=True)


def espn_to_football_data(name: str) -> str:
    plain = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return ESPN_TEAM_NAMES.get(plain, plain)


def fetch_espn_results(start: date, end: date) -> pd.DataFrame:
    """Finished Série A games between `start` and `end` (inclusive) from ESPN's scoreboard."""
    rows = []
    day = start
    while day <= end:
        response = requests.get(ESPN_URL, params={"dates": day.strftime("%Y%m%d")}, timeout=30)
        response.raise_for_status()
        for event in response.json().get("events", []):
            competition = event["competitions"][0]
            if competition["status"]["type"]["name"] != "STATUS_FULL_TIME":
                continue
            side = {c["homeAway"]: c for c in competition["competitors"]}
            rows.append(
                {
                    "date": pd.Timestamp(event["date"]).tz_convert(None).normalize(),
                    "home": espn_to_football_data(side["home"]["team"]["displayName"]),
                    "away": espn_to_football_data(side["away"]["team"]["displayName"]),
                    "home_goals": int(side["home"]["score"]),
                    "away_goals": int(side["away"]["score"]),
                }
            )
        day += timedelta(days=1)
    df = pd.DataFrame(rows, columns=["date", "home", "away", "home_goals", "away_goals"])
    df["result"] = "D"
    df.loc[df.home_goals > df.away_goals, "result"] = "H"
    df.loc[df.home_goals < df.away_goals, "result"] = "A"
    return df.drop_duplicates(["home", "away"])


# Games with these statuses have no reliable date (or will not be played)
ESPN_SKIP_STATUSES = {"STATUS_FULL_TIME", "STATUS_POSTPONED", "STATUS_CANCELED", "STATUS_ABANDONED"}


def fetch_espn_schedule(start: date, end: date) -> pd.DataFrame:
    """Série A games scheduled (not finished) between `start` and `end` (inclusive), from ESPN.

    ESPN's scoreboard takes one date per request, so this makes one request per day.
    """
    rows = []
    day = start
    while day <= end:
        response = requests.get(ESPN_URL, params={"dates": day.strftime("%Y%m%d")}, timeout=30)
        response.raise_for_status()
        for event in response.json().get("events", []):
            competition = event["competitions"][0]
            if competition["status"]["type"]["name"] in ESPN_SKIP_STATUSES:
                continue
            side = {c["homeAway"]: c for c in competition["competitors"]}
            rows.append(
                {
                    # ESPN times are UTC; convert to Brasília time so late-night games keep their local date
                    "date": pd.Timestamp(event["date"]).tz_convert("America/Sao_Paulo").tz_localize(None),
                    "home": espn_to_football_data(side["home"]["team"]["displayName"]),
                    "away": espn_to_football_data(side["away"]["team"]["displayName"]),
                }
            )
        day += timedelta(days=1)
    df = pd.DataFrame(rows, columns=["date", "home", "away"])
    return df.drop_duplicates(["home", "away"]).sort_values("date").reset_index(drop=True)


def recent_espn_matches(matches: pd.DataFrame, refresh: bool = False, path: Path = ESPN_PATH) -> pd.DataFrame:
    """ESPN results since football-data's last game (cached in `path`; re-fetched with `refresh`)."""
    if path.exists() and not refresh:
        recent = pd.read_csv(path, parse_dates=["date"])
    else:
        season = matches.season.max()
        start = matches.loc[matches.season == season, "date"].max().date() - timedelta(days=1)
        try:
            recent = fetch_espn_results(start, date.today())
        except requests.RequestException as error:
            warnings.warn(f"Could not fetch recent results from ESPN ({error}); using football-data only.")
            return pd.DataFrame()
        path.parent.mkdir(parents=True, exist_ok=True)
        recent.to_csv(path, index=False)

    season_teams = set(matches.loc[matches.season == matches.season.max(), "home"])
    unknown = (set(recent.home) | set(recent.away)) - season_teams
    if unknown:
        raise ValueError(f"ESPN team names not mapped to football-data names: {sorted(unknown)}")
    return recent
