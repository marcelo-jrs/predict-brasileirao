"use client";

import { useMemo, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { formatDate, formatShortDate, pct } from "@/lib/format";
import { getDict, type Lang } from "@/lib/i18n";
import { teamColors } from "@/lib/teams";
import type { History, Meta, ModelId, Predictions, TableRow } from "@/lib/types";

import { useModel } from "./ModelProvider";
import { ModelSelector } from "./ModelSelector";

type Metric = "p_top6" | "p_relegation" | "p_title" | "expected_points";

// Distinct colours for lines (club colours are often black/white, which makes lines indistinguishable)
const LINE_COLORS = ["#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4", "#46c0c0", "#f032e6", "#9a6324", "#808000", "#000075"];

export function HistoryView({
  lang,
  meta,
  table,
  history,
  predictions,
}: {
  lang: Lang;
  meta: Meta;
  table: TableRow[];
  history: Record<ModelId, History>;
  predictions: Record<ModelId, Predictions>;
}) {
  const t = getDict(lang);
  const { model } = useModel();
  const [metric, setMetric] = useState<Metric>("p_relegation");
  const [picked, setPicked] = useState<string[] | null>(null);

  const metricLabel: Record<Metric, string> = {
    p_top6: t.home.libertadores,
    p_relegation: t.home.relegation,
    p_title: t.home.titleRace,
    expected_points: t.historyPage.expectedPoints,
  };

  const current = useMemo(() => new Map(predictions[model].teams.map((p) => [p.team, p])), [predictions, model]);

  // Default selection: teams whose chance is still open today (or the top 6 for projected points)
  const contenders = useMemo(() => {
    if (metric === "expected_points") return table.slice(0, 6).map((r) => r.team);
    return table
      .map((r) => r.team)
      .filter((team) => {
        const p = current.get(team)![metric];
        return p >= 0.01 && p <= 0.99;
      });
  }, [metric, table, current]);
  const selected = picked ?? contenders;

  const data = useMemo(() => {
    const points = history[model].snapshots.map((s) => ({
      date: s.date,
      ...Object.fromEntries(selected.map((team) => [team, s.teams[team]?.[metric] ?? null])),
    }));
    points.push({
      date: meta.data_through,
      ...Object.fromEntries(selected.map((team) => [team, current.get(team)?.[metric] ?? null])),
    });
    return points;
  }, [history, model, selected, metric, meta.data_through, current]);

  const isProb = metric !== "expected_points";
  const toggle = (team: string) =>
    setPicked((prev) => {
      const base = prev ?? contenders;
      return base.includes(team) ? base.filter((x) => x !== team) : [...base, team];
    });

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold sm:text-3xl">{t.historyPage.title}</h1>
        <p className="max-w-3xl text-muted">{t.historyPage.intro}</p>
      </div>
      <ModelSelector lang={lang} />

      <section className="space-y-4 rounded-xl border border-border bg-surface p-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm text-muted">{t.historyPage.metric}:</span>
          <div className="inline-flex flex-wrap rounded-lg border border-border p-0.5 text-sm">
            {(Object.keys(metricLabel) as Metric[]).map((k) => (
              <button
                key={k}
                onClick={() => {
                  setMetric(k);
                  setPicked(null);
                }}
                className={`rounded-md px-3 py-1 ${k === metric ? "bg-accent text-white" : "text-muted hover:text-foreground"}`}
              >
                {metricLabel[k]}
              </button>
            ))}
          </div>
        </div>

        <div className="h-[420px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis
                dataKey="date"
                tickFormatter={(d: string) => formatShortDate(d, lang)}
                stroke="var(--muted)"
                fontSize={12}
                minTickGap={24}
              />
              <YAxis
                domain={isProb ? [0, 1] : ["auto", "auto"]}
                tickFormatter={(v: number) => (isProb ? `${Math.round(100 * v)}%` : String(Math.round(v)))}
                stroke="var(--muted)"
                fontSize={12}
                width={44}
              />
              <Tooltip
                contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8 }}
                labelFormatter={(d) => formatDate(String(d), lang)}
                formatter={(v, team) => [
                  typeof v === "number" ? (isProb ? pct(v) : v.toFixed(1)) : "–",
                  meta.teams[String(team)]?.name ?? String(team),
                ]}
                itemSorter={(item) => -(Number(item.value) || 0)}
              />
              <Legend formatter={(team) => meta.teams[String(team)]?.name ?? String(team)} />
              {selected.map((team, i) => (
                <Line
                  key={team}
                  type="monotone"
                  dataKey={team}
                  stroke={LINE_COLORS[i % LINE_COLORS.length]}
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div>
          <div className="mb-2 flex flex-wrap items-center gap-2 text-sm">
            <span className="text-muted">{t.historyPage.teams}:</span>
            <button onClick={() => setPicked(null)} className="rounded-md border border-border px-2 py-0.5 text-xs hover:text-foreground">
              {t.historyPage.reset}
            </button>
            <button onClick={() => setPicked([])} className="rounded-md border border-border px-2 py-0.5 text-xs hover:text-foreground">
              {t.historyPage.clear}
            </button>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {table.map((r) => {
              const on = selected.includes(r.team);
              const dot = on ? LINE_COLORS[selected.indexOf(r.team) % LINE_COLORS.length] : teamColors(r.team)[0];
              return (
                <button
                  key={r.team}
                  onClick={() => toggle(r.team)}
                  aria-pressed={on}
                  className={`rounded-full border px-2.5 py-0.5 text-xs ${
                    on ? "border-accent bg-accent/15 text-foreground" : "border-border text-muted hover:text-foreground"
                  }`}
                >
                  <span className="mr-1 inline-block h-2 w-2 rounded-full" style={{ background: dot }} />
                  {meta.teams[r.team]?.name ?? r.team}
                </button>
              );
            })}
          </div>
        </div>
      </section>
    </div>
  );
}
