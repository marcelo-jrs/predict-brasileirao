// Monte Carlo simulation of the rest of the season – a TypeScript port of src/brasileirao/simulate.py.
//
// For every simulated season, each remaining game gets a result and a score:
//   - "probs" models (Elo, market): draw home/draw/away from the model's chances, then a typical
//     historical scoreline for that result;
//   - "score matrix" models (Poisson): draw the exact score from the model's score grid.
// Results the user has fixed (what-if) are kept, only their score is drawn.
// Teams are then ranked by points, wins, goal difference, goals scored (then at random).

import type { Outcome, Probs, Scorelines, TableRow } from "./types";

export interface SimFixture {
  home: string;
  away: string;
}

export interface SimInput {
  table: TableRow[];
  fixtures: SimFixture[];
  probs?: Probs[];
  scorelines?: Scorelines;
  scoreMatrices?: number[][][];
  fixed?: Record<number, Outcome>; // fixture index -> forced result
  nSims: number;
  seed?: number;
  libertadores?: number;
  relegation?: number;
}

export interface TeamResult {
  team: string;
  p_title: number;
  p_top6: number;
  p_relegation: number;
  expected_points: number;
  expected_position: number;
  positions: number[];
}

const OUTCOMES: Outcome[] = ["H", "D", "A"];

/** Small, fast, seedable PRNG (mulberry32) so results are reproducible. */
export function mulberry32(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

interface Sampler {
  cum: Float64Array; // cumulative weights (not necessarily summing to 1)
  home: Int32Array;
  away: Int32Array;
}

function makeSampler(items: [number, number, number][]): Sampler {
  const cum = new Float64Array(items.length);
  const home = new Int32Array(items.length);
  const away = new Int32Array(items.length);
  let total = 0;
  items.forEach(([h, a, w], i) => {
    total += w;
    cum[i] = total;
    home[i] = h;
    away[i] = a;
  });
  return { cum, home, away };
}

function draw(s: Sampler, rand: () => number): number {
  const u = rand() * s.cum[s.cum.length - 1];
  let lo = 0;
  let hi = s.cum.length - 1;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (s.cum[mid] > u) hi = mid;
    else lo = mid + 1;
  }
  return lo;
}

function outcomeOf(home: number, away: number): Outcome {
  return home > away ? "H" : home === away ? "D" : "A";
}

/** Per fixture: one sampler for "any result" and one per result (used when the result is fixed). */
function matrixSamplers(matrix: number[][]): { all: Sampler; byOutcome: Record<Outcome, Sampler> } {
  const cells: [number, number, number][] = [];
  matrix.forEach((row, i) => row.forEach((p, j) => cells.push([i, j, p])));
  const byOutcome = Object.fromEntries(
    OUTCOMES.map((o) => [o, makeSampler(cells.filter(([i, j]) => outcomeOf(i, j) === o))]),
  ) as Record<Outcome, Sampler>;
  return { all: makeSampler(cells), byOutcome };
}

export function simulate(input: SimInput): TeamResult[] {
  const { table, fixtures, nSims } = input;
  const libertadores = input.libertadores ?? 6;
  const relegation = input.relegation ?? 4;
  const rand = mulberry32(input.seed ?? 42);
  const fixed = input.fixed ?? {};

  const teams = table.map((r) => r.team);
  const n = teams.length;
  const index = new Map(teams.map((t, i) => [t, i]));
  const homeIdx = fixtures.map((f) => index.get(f.home)!);
  const awayIdx = fixtures.map((f) => index.get(f.away)!);

  const usesMatrices = input.scoreMatrices !== undefined;
  if (!usesMatrices && (!input.probs || !input.scorelines)) {
    throw new Error("simulate needs either scoreMatrices or probs + scorelines");
  }
  const matrix = usesMatrices ? input.scoreMatrices!.map(matrixSamplers) : [];
  const scoreline = usesMatrices
    ? null
    : (Object.fromEntries(OUTCOMES.map((o) => [o, makeSampler(input.scorelines![o])])) as Record<Outcome, Sampler>);

  const basePoints = table.map((r) => r.points);
  const baseWins = table.map((r) => r.wins);
  const baseFor = table.map((r) => r.goals_for);
  const baseAgainst = table.map((r) => r.goals_against);

  const points = new Int32Array(n);
  const wins = new Int32Array(n);
  const goalsFor = new Int32Array(n);
  const goalsAgainst = new Int32Array(n);
  const key = new Float64Array(n);
  const order = teams.map((_, i) => i);

  const positionCounts = teams.map(() => new Float64Array(n));
  const pointsSum = new Float64Array(n);

  for (let s = 0; s < nSims; s++) {
    for (let t = 0; t < n; t++) {
      points[t] = basePoints[t];
      wins[t] = baseWins[t];
      goalsFor[t] = baseFor[t];
      goalsAgainst[t] = baseAgainst[t];
    }

    for (let f = 0; f < fixtures.length; f++) {
      const forced = fixed[f];
      let hg: number;
      let ag: number;
      if (usesMatrices) {
        const sampler = forced ? matrix[f].byOutcome[forced] : matrix[f].all;
        const cell = draw(sampler, rand);
        hg = sampler.home[cell];
        ag = sampler.away[cell];
      } else {
        let outcome = forced;
        if (!outcome) {
          const [pH, pD] = input.probs![f];
          const u = rand();
          outcome = u < pH ? "H" : u < pH + pD ? "D" : "A";
        }
        const sampler = scoreline![outcome];
        const cell = draw(sampler, rand);
        hg = sampler.home[cell];
        ag = sampler.away[cell];
      }

      const h = homeIdx[f];
      const a = awayIdx[f];
      goalsFor[h] += hg;
      goalsAgainst[h] += ag;
      goalsFor[a] += ag;
      goalsAgainst[a] += hg;
      if (hg > ag) {
        points[h] += 3;
        wins[h] += 1;
      } else if (hg < ag) {
        points[a] += 3;
        wins[a] += 1;
      } else {
        points[h] += 1;
        points[a] += 1;
      }
    }

    // Same packed sort key as the Python version: points, wins, goal difference, goals for, random
    for (let t = 0; t < n; t++) {
      const gd = goalsFor[t] - goalsAgainst[t];
      key[t] = ((points[t] * 100 + wins[t]) * 1000 + (gd + 500)) * 1000 + goalsFor[t] + rand();
    }
    order.sort((x, y) => key[y] - key[x]);
    for (let p = 0; p < n; p++) {
      positionCounts[order[p]][p] += 1;
    }
    for (let t = 0; t < n; t++) pointsSum[t] += points[t];
  }

  return teams.map((team, t) => {
    const positions = Array.from(positionCounts[t], (c) => c / nSims);
    const sumRange = (from: number, to: number) => positions.slice(from, to).reduce((x, y) => x + y, 0);
    return {
      team,
      p_title: positions[0],
      p_top6: sumRange(0, libertadores),
      p_relegation: sumRange(n - relegation, n),
      expected_points: pointsSum[t] / nSims,
      expected_position: positions.reduce((acc, p, i) => acc + p * (i + 1), 0),
      positions,
    };
  });
}
