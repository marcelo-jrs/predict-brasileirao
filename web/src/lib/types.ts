// Types of the JSON files written by `python -m brasileirao.export` (see web/README.md).

export type ModelId = "market" | "elo" | "poisson";
export type Outcome = "H" | "D" | "A";
export type Probs = [number, number, number]; // home win, draw, away win

export interface Meta {
  season: number;
  data_through: string;
  generated_at: string;
  n_sims: number;
  models: ModelId[];
  default_model: ModelId;
  games_played: number;
  games_remaining: number;
  zones: { libertadores: number; relegation: number };
  teams: Record<string, { name: string; short: string }>;
}

export interface TableRow {
  position: number;
  team: string;
  played: number;
  wins: number;
  draws: number;
  losses: number;
  goals_for: number;
  goals_against: number;
  goal_diff: number;
  points: number;
  form: ("W" | "D" | "L")[];
}

export interface TeamPrediction {
  team: string;
  expected_points: number;
  expected_position: number;
  p_title: number;
  p_top6: number;
  p_relegation: number;
  positions: number[];
  strength: Record<string, number | null>;
}

export interface Predictions {
  model: ModelId;
  n_sims: number;
  teams: TeamPrediction[];
}

export interface Fixture {
  id: number;
  home: string;
  away: string;
  date: string | null;
  probs: Record<ModelId, Probs>;
}

/** [home goals, away goals, frequency] */
export type Scoreline = [number, number, number];
export type Scorelines = Record<Outcome, Scoreline[]>;

/** model -> one (G x G) grid per fixture: P(home scores i, away scores j) */
export type ScoreMatrices = Partial<Record<ModelId, number[][][]>>;

export interface Snapshot {
  date: string;
  games: number;
  teams: Record<string, { p_title: number; p_top6: number; p_relegation: number; expected_points: number }>;
}

export interface History {
  model: ModelId;
  season: number;
  snapshots: Snapshot[];
}

export interface Accuracy {
  tune_seasons: [number, number];
  test_seasons: [number, number];
  n_matches: number;
  leaderboard: { id: string; name: string; log_loss: number; brier: number }[];
  calibration: Record<string, { bin: number; predicted: number; observed: number; n: number }[]>;
}
