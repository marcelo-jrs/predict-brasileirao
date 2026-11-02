"use client";

import { useState } from "react";

import { formatDate, formatNumber, pct } from "@/lib/format";
import { getDict, type Lang } from "@/lib/i18n";
import type { Fixture, Meta, ModelId, Predictions, TableRow } from "@/lib/types";

import { TeamName } from "./TeamName";

type Metric = "p_top6" | "p_relegation" | "p_title";

export function ModelsView({
  lang,
  meta,
  table,
  predictions,
  fixtures,
}: {
  lang: Lang;
  meta: Meta;
  table: TableRow[];
  predictions: Record<ModelId, Predictions>;
  fixtures: Fixture[];
}) {
  const t = getDict(lang);
  const [metric, setMetric] = useState<Metric>("p_relegation");
  const models = meta.models;
  const name = (team: string) => meta.teams[team]?.name ?? team;
  const lookup = Object.fromEntries(
    models.map((m) => [m, new Map(predictions[m].teams.map((p) => [p.team, p]))]),
  ) as Record<ModelId, Map<string, Predictions["teams"][number]>>;

  const metricLabel: Record<Metric, string> = {
    p_top6: t.home.libertadores,
    p_relegation: t.home.relegation,
    p_title: t.home.titleRace,
  };

  const rows = table
    .map((row) => {
      const values = models.map((m) => lookup[m].get(row.team)![metric]);
      return { row, values, spread: Math.max(...values) - Math.min(...values) };
    })
    .filter((r) => Math.max(...r.values) >= 0.005 && Math.min(...r.values) < 0.995);
  const maxSpread = Math.max(0, ...rows.map((r) => r.spread));

  const upcoming = fixtures
    .filter((f) => f.date)
    .sort((a, b) => a.date!.localeCompare(b.date!))
    .slice(0, 10);

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold sm:text-3xl">{t.modelsPage.title}</h1>
        <p className="max-w-3xl text-muted">{t.modelsPage.intro}</p>
        <ul className="text-sm text-muted">
          {models.map((m) => (
            <li key={m}>
              <span className="font-medium text-foreground">{t.models[m].name}</span> – {t.models[m].blurb}
            </li>
          ))}
        </ul>
      </div>

      <section className="rounded-xl border border-border bg-surface p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 className="font-semibold">{t.modelsPage.chances}</h2>
          <div className="inline-flex rounded-lg border border-border p-0.5 text-sm">
            {(Object.keys(metricLabel) as Metric[]).map((k) => (
              <button
                key={k}
                onClick={() => setMetric(k)}
                className={`rounded-md px-3 py-1 ${k === metric ? "bg-accent text-white" : "text-muted hover:text-foreground"}`}
              >
                {metricLabel[k]}
              </button>
            ))}
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-xs uppercase tracking-wide text-muted">
              <tr className="border-b border-border">
                <th className="py-2 pr-3">{t.home.team}</th>
                {models.map((m) => (
                  <th key={m} className="px-3 py-2 text-right">
                    {t.models[m].name}
                  </th>
                ))}
                <th className="px-3 py-2 text-right">{t.modelsPage.spread}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(({ row, values, spread }) => (
                <tr key={row.team} className="border-b border-border last:border-0">
                  <td className="py-1.5 pr-3 font-medium">
                    <TeamName team={row.team} name={name(row.team)} />
                  </td>
                  {values.map((v, i) => (
                    <td key={models[i]} className="tabular px-3 py-1.5 text-right">
                      {pct(v)}
                    </td>
                  ))}
                  <td className="tabular px-3 py-1.5 text-right">
                    <span
                      className={`rounded px-1.5 py-0.5 ${spread === maxSpread && spread >= 0.05 ? "bg-amber-500/20 font-semibold" : "text-muted"}`}
                      title={spread === maxSpread ? t.modelsPage.disagree : undefined}
                    >
                      {Math.round(100 * spread)} pp
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-xl border border-border bg-surface p-4">
        <h2 className="mb-1 font-semibold">{t.modelsPage.nextGames}</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-xs uppercase tracking-wide text-muted">
              <tr className="border-b border-border">
                <th className="py-2 pr-3" />
                <th className="py-2 pr-3" />
                {models.map((m) => (
                  <th key={m} className="px-3 py-2 text-center">
                    {t.models[m].name}
                    <div className="font-normal normal-case">
                      {t.modelsPage.home} / {t.modelsPage.draw} / {t.modelsPage.away}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {upcoming.map((f) => (
                <tr key={f.id} className="border-b border-border last:border-0">
                  <td className="whitespace-nowrap py-1.5 pr-3 text-muted">{formatDate(f.date!, lang, true)}</td>
                  <td className="py-1.5 pr-3 font-medium">
                    <span className="flex flex-wrap items-center gap-x-1.5">
                      <TeamName team={f.home} name={name(f.home)} /> <span className="text-muted">×</span>
                      <TeamName team={f.away} name={name(f.away)} />
                    </span>
                  </td>
                  {models.map((m) => (
                    <td key={m} className="tabular whitespace-nowrap px-3 py-1.5 text-center">
                      {f.probs[m].map((p) => pct(p)).join(" / ")}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="rounded-xl border border-border bg-surface p-4">
        <h2 className="mb-1 font-semibold">{t.modelsPage.strengths}</h2>
        <p className="mb-3 text-xs text-muted">{t.modelsPage.strengthNote}</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-xs uppercase tracking-wide text-muted">
              <tr className="border-b border-border">
                <th className="py-2 pr-3">{t.home.team}</th>
                <th className="px-3 py-2 text-right">{t.models.market.name}</th>
                <th className="px-3 py-2 text-right">{t.models.elo.name}</th>
                <th className="px-3 py-2 text-right">
                  {t.models.poisson.name} · {t.modelsPage.attack}
                </th>
                <th className="px-3 py-2 text-right">
                  {t.models.poisson.name} · {t.modelsPage.defence}
                </th>
              </tr>
            </thead>
            <tbody>
              {[...predictions.market.teams]
                .sort((a, b) => (b.strength.market_rating ?? 0) - (a.strength.market_rating ?? 0))
                .map((p) => {
                  const elo = lookup.elo.get(p.team)?.strength.elo;
                  const poisson = lookup.poisson.get(p.team)?.strength;
                  return (
                    <tr key={p.team} className="border-b border-border last:border-0">
                      <td className="py-1.5 pr-3 font-medium">
                        <TeamName team={p.team} name={name(p.team)} />
                      </td>
                      <td className="tabular px-3 py-1.5 text-right">
                        {formatNumber(p.strength.market_rating ?? 0, lang, 2)}
                      </td>
                      <td className="tabular px-3 py-1.5 text-right">{elo != null ? Math.round(elo) : "–"}</td>
                      <td className="tabular px-3 py-1.5 text-right">
                        {poisson?.attack != null ? formatNumber(poisson.attack, lang, 2) : "–"}
                      </td>
                      <td className="tabular px-3 py-1.5 text-right">
                        {poisson?.defence != null ? formatNumber(poisson.defence, lang, 2) : "–"}
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
