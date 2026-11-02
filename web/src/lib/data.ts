// Server-only helpers: read the exported JSON at build time.
import { readFileSync } from "node:fs";
import path from "node:path";

import type {
  Accuracy,
  Fixture,
  History,
  Meta,
  ModelId,
  Predictions,
  ScoreMatrices,
  Scorelines,
  TableRow,
} from "./types";

const DATA_DIR = path.join(process.cwd(), "public", "data");

function read<T>(file: string): T {
  return JSON.parse(readFileSync(path.join(DATA_DIR, file), "utf-8")) as T;
}

export const getMeta = () => read<Meta>("meta.json");
export const getTable = () => read<{ season: number; rows: TableRow[] }>("table.json").rows;
export const getFixtures = () => read<{ fixtures: Fixture[] }>("fixtures.json").fixtures;
export const getScorelines = () => read<Scorelines>("scorelines.json");
export const getScoreMatrices = () => read<ScoreMatrices>("score_matrices.json");
export const getAccuracy = () => read<Accuracy>("accuracy.json");

export function getAllPredictions(models: ModelId[]): Record<ModelId, Predictions> {
  return Object.fromEntries(models.map((m) => [m, read<Predictions>(`predictions/${m}.json`)])) as Record<
    ModelId,
    Predictions
  >;
}

export function getAllHistory(models: ModelId[]): Record<ModelId, History> {
  return Object.fromEntries(models.map((m) => [m, read<History>(`history/${m}.json`)])) as Record<
    ModelId,
    History
  >;
}
