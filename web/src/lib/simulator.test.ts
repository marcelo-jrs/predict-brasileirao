import { readFileSync } from "node:fs";
import path from "node:path";

import { describe, expect, it } from "vitest";

import { mulberry32, simulate } from "./simulator";
import type { Fixture, Predictions, ScoreMatrices, Scorelines, TableRow } from "./types";

const DATA = path.join(__dirname, "..", "..", "public", "data");
const read = <T>(file: string): T => JSON.parse(readFileSync(path.join(DATA, file), "utf-8")) as T;

const table = read<{ rows: TableRow[] }>("table.json").rows;
const fixtures = read<{ fixtures: Fixture[] }>("fixtures.json").fixtures;
const scorelines = read<Scorelines>("scorelines.json");
const matrices = read<ScoreMatrices>("score_matrices.json");

// Monte Carlo noise: with 20k sims on both sides, the standard error of a difference is at most ~0.5 points
const TOLERANCE = 0.025;

function expectParity(model: "market" | "elo" | "poisson", results: ReturnType<typeof simulate>) {
  const python = new Map(read<Predictions>(`predictions/${model}.json`).teams.map((t) => [t.team, t]));
  for (const r of results) {
    const p = python.get(r.team)!;
    expect(Math.abs(r.p_title - p.p_title)).toBeLessThan(TOLERANCE);
    expect(Math.abs(r.p_top6 - p.p_top6)).toBeLessThan(TOLERANCE);
    expect(Math.abs(r.p_relegation - p.p_relegation)).toBeLessThan(TOLERANCE);
    expect(Math.abs(r.expected_points - p.expected_points)).toBeLessThan(0.3);
  }
}

describe("simulator parity with the Python export", () => {
  it.each(["market", "elo"] as const)("%s (probabilities + historical scorelines)", (model) => {
    const results = simulate({
      table,
      fixtures,
      probs: fixtures.map((f) => f.probs[model]),
      scorelines,
      nSims: 20_000,
    });
    expectParity(model, results);
  });

  it("poisson (score matrices)", () => {
    const results = simulate({ table, fixtures, scoreMatrices: matrices.poisson, nSims: 20_000 });
    expectParity("poisson", results);
  });
});

describe("simulator invariants", () => {
  const results = simulate({
    table,
    fixtures,
    probs: fixtures.map((f) => f.probs.market),
    scorelines,
    nSims: 2_000,
  });

  it("probabilities add up across teams", () => {
    const sum = (k: "p_title" | "p_top6" | "p_relegation") => results.reduce((acc, r) => acc + r[k], 0);
    expect(sum("p_title")).toBeCloseTo(1, 6);
    expect(sum("p_top6")).toBeCloseTo(6, 6);
    expect(sum("p_relegation")).toBeCloseTo(4, 6);
    for (const r of results) expect(r.positions.reduce((a, b) => a + b, 0)).toBeCloseTo(1, 6);
  });

  it("a team can't finish with fewer points than it has", () => {
    for (const r of results) {
      const row = table.find((t) => t.team === r.team)!;
      expect(r.expected_points).toBeGreaterThanOrEqual(row.points);
    }
  });

  it("fixing results moves the chances in the right direction", () => {
    const team = "Corinthians";
    const games = fixtures.map((f, i) => [f, i] as const).filter(([f]) => f.home === team || f.away === team);
    const fixedOutcome = (win: boolean) =>
      Object.fromEntries(
        games.map(([f, i]) => [i, (f.home === team) === win ? "H" : "A"] as const),
      ) as Record<number, "H" | "A">;
    const run = (fixed: Record<number, "H" | "A">) =>
      simulate({
        table,
        fixtures,
        probs: fixtures.map((f) => f.probs.market),
        scorelines,
        fixed,
        nSims: 2_000,
      }).find((r) => r.team === team)!;
    const allWins = run(fixedOutcome(true));
    const allLosses = run(fixedOutcome(false));
    const row = table.find((t) => t.team === team)!;
    expect(allWins.expected_points).toBeCloseTo(row.points + 3 * games.length, 6);
    expect(allLosses.expected_points).toBeCloseTo(row.points, 6);
    expect(allWins.p_relegation).toBeLessThan(allLosses.p_relegation);
  });

  it("fixed results are respected by the score-matrix path too", () => {
    const fixed = Object.fromEntries(fixtures.map((_, i) => [i, "D" as const]));
    const res = simulate({ table, fixtures, scoreMatrices: matrices.poisson, fixed, nSims: 200 });
    for (const r of res) {
      const row = table.find((t) => t.team === r.team)!;
      const remaining = fixtures.filter((f) => f.home === r.team || f.away === r.team).length;
      expect(r.expected_points).toBeCloseTo(row.points + remaining, 6);
    }
  });

  it("is reproducible with the same seed", () => {
    const a = mulberry32(7);
    const b = mulberry32(7);
    expect([a(), a(), a()]).toEqual([b(), b(), b()]);
  });
});
