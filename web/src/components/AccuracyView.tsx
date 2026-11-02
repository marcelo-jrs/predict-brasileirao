"use client";

import { useState } from "react";
import { CartesianGrid, Legend, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from "recharts";

import { pct } from "@/lib/format";
import { getDict, type Lang } from "@/lib/i18n";
import type { Accuracy } from "@/lib/types";

const MODEL_COLORS: Record<string, string> = {
  market: "#10b981",
  elo: "#3b82f6",
  poisson: "#f59e0b",
  closing_odds: "#a855f7",
};

export function AccuracyView({ lang, accuracy }: { lang: Lang; accuracy: Accuracy }) {
  const t = getDict(lang);
  const a = t.accuracyPage;
  const calibrated = Object.keys(accuracy.calibration);
  const [shown, setShown] = useState<string[]>(["market", "elo"]);

  const board = [...accuracy.leaderboard].sort((x, y) => x.log_loss - y.log_loss);
  const baseline = accuracy.leaderboard.find((m) => m.id === "baseline")!.log_loss;
  const best = Math.min(...board.map((m) => m.log_loss));

  // Each point: average predicted chance in a 10%-wide bin vs how often it really happened (tiny bins skipped)
  const series = Object.fromEntries(
    calibrated.map((id) => [
      id,
      accuracy.calibration[id].filter((c) => c.n >= 30).map((c) => ({ x: c.predicted, y: c.observed, n: c.n })),
    ]),
  );

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold sm:text-3xl">{a.title}</h1>
        <p className="max-w-3xl text-muted">
          {a.intro(
            `${accuracy.tune_seasons[0]}–${accuracy.tune_seasons[1]}`,
            `${accuracy.test_seasons[0]}–${accuracy.test_seasons[1]}`,
            accuracy.n_matches,
          )}
        </p>
      </div>

      <section className="rounded-xl border border-border bg-surface p-4">
        <h2 className="mb-3 font-semibold">{a.leaderboard}</h2>
        <table className="w-full text-sm">
          <thead className="text-left text-xs uppercase tracking-wide text-muted">
            <tr className="border-b border-border">
              <th className="py-2 pr-3">{a.model}</th>
              <th className="w-1/2 px-3 py-2">{a.logLoss}</th>
              <th className="px-3 py-2 text-right">{a.brier}</th>
            </tr>
          </thead>
          <tbody>
            {board.map((m) => {
              // Bar = share of the gap between "know nothing" and the best model that this model closes
              const closed = Math.max(0, (baseline - m.log_loss) / (baseline - best));
              const benchmark = m.id === "closing_odds";
              return (
                <tr key={m.id} className="border-b border-border last:border-0">
                  <td className="py-1.5 pr-3">
                    <span className={benchmark ? "italic" : "font-medium"}>{a.names[m.id] ?? m.name}</span>
                    {benchmark && <span className="block text-xs text-muted">{a.benchmark}</span>}
                  </td>
                  <td className="px-3 py-1.5">
                    <div className="flex items-center gap-2">
                      <div className="h-2 flex-1 rounded bg-background">
                        <div
                          className={`h-2 rounded ${benchmark ? "bg-purple-500/60" : "bg-accent"}`}
                          style={{ width: `${100 * closed}%` }}
                        />
                      </div>
                      <span className="tabular w-14 text-right">{m.log_loss.toFixed(4)}</span>
                    </div>
                  </td>
                  <td className="tabular px-3 py-1.5 text-right">{m.brier.toFixed(4)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <div className="mt-3 space-y-1 text-xs text-muted">
          <p>{a.logLossHelp}</p>
          <p>{a.brierHelp}</p>
        </div>
      </section>

      <section className="rounded-xl border border-border bg-surface p-4">
        <h2 className="mb-1 font-semibold">{a.calibration}</h2>
        <p className="mb-3 max-w-3xl text-sm text-muted">{a.calibrationHelp}</p>
        <div className="mb-3 flex flex-wrap gap-1.5">
          {calibrated.map((id) => {
            const on = shown.includes(id);
            return (
              <button
                key={id}
                onClick={() => setShown((s) => (on ? s.filter((x) => x !== id) : [...s, id]))}
                aria-pressed={on}
                className={`rounded-full border px-2.5 py-0.5 text-xs ${on ? "border-accent bg-accent/15" : "border-border text-muted"}`}
              >
                <span className="mr-1 inline-block h-2 w-2 rounded-full" style={{ background: MODEL_COLORS[id] }} />
                {a.names[id] ?? id}
              </button>
            );
          })}
        </div>
        <div className="mx-auto aspect-square w-full max-w-xl">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 8, right: 16, bottom: 32, left: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis
                dataKey="x"
                type="number"
                domain={[0, 1]}
                ticks={[0, 0.2, 0.4, 0.6, 0.8, 1]}
                tickFormatter={(v: number) => `${Math.round(100 * v)}%`}
                stroke="var(--muted)"
                fontSize={12}
                label={{ value: a.predicted, position: "insideBottom", offset: -12, fill: "var(--muted)", fontSize: 12 }}
              />
              <YAxis
                dataKey="y"
                type="number"
                domain={[0, 1]}
                ticks={[0, 0.2, 0.4, 0.6, 0.8, 1]}
                tickFormatter={(v: number) => `${Math.round(100 * v)}%`}
                stroke="var(--muted)"
                fontSize={12}
                label={{ value: a.observed, angle: -90, position: "insideLeft", fill: "var(--muted)", fontSize: 12 }}
              />
              <Tooltip
                contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8 }}
                formatter={(v, key) => [typeof v === "number" ? pct(v, 1) : "–", key === "x" ? a.predicted : a.observed]}
              />
              <Legend verticalAlign="top" height={32} />
              <Scatter
                name={a.perfect}
                data={[
                  { x: 0, y: 0 },
                  { x: 1, y: 1 },
                ]}
                line={{ stroke: "var(--muted)", strokeDasharray: "5 5" }}
                shape={() => <g />}
                legendType="plainline"
                fill="var(--muted)"
                isAnimationActive={false}
              />
              {shown.map((id) => (
                <Scatter
                  key={id}
                  name={a.names[id] ?? id}
                  data={series[id]}
                  fill={MODEL_COLORS[id]}
                  line={{ stroke: MODEL_COLORS[id], strokeWidth: 2 }}
                  isAnimationActive={false}
                />
              ))}
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  );
}
