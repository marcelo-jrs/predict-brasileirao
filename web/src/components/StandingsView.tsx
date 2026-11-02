"use client";

import { getDict, type Lang } from "@/lib/i18n";
import type { Meta, ModelId, Predictions, TableRow } from "@/lib/types";

import { useModel } from "./ModelProvider";
import { ModelSelector } from "./ModelSelector";
import { ProbBar } from "./ProbBar";
import { TeamName } from "./TeamName";

const FORM_COLORS = { W: "bg-emerald-500", D: "bg-slate-400", L: "bg-rose-500" } as const;

function RaceCard({
  title,
  items,
  kind,
  emptyText,
  teams,
}: {
  title: string;
  items: { team: string; p: number }[];
  kind: "title" | "top" | "bottom";
  emptyText: string;
  teams: Meta["teams"];
}) {
  const sure = items.filter((i) => i.p >= 0.995);
  const open = items.filter((i) => i.p >= 0.005 && i.p < 0.995).sort((a, b) => b.p - a.p);
  return (
    <section className="rounded-xl border border-border bg-surface p-4">
      <h2 className="mb-3 font-semibold">{title}</h2>
      {sure.length > 0 && (
        <p className="mb-2 text-sm text-muted">
          {sure.map((i) => teams[i.team]?.name ?? i.team).join(", ")} <span className="font-medium">&gt;99%</span>
        </p>
      )}
      {open.length === 0 ? (
        <p className="text-sm text-muted">{emptyText}</p>
      ) : (
        <ul className="space-y-1.5">
          {open.map((i) => (
            <li key={i.team} className="grid grid-cols-[1fr_6rem] items-center gap-2 text-sm">
              <TeamName team={i.team} name={teams[i.team]?.name ?? i.team} />
              <ProbBar p={i.p} kind={kind} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function StandingsView({
  lang,
  meta,
  table,
  predictions,
}: {
  lang: Lang;
  meta: Meta;
  table: TableRow[];
  predictions: Record<ModelId, Predictions>;
}) {
  const t = getDict(lang);
  const { model } = useModel();
  const byTeam = new Map(predictions[model].teams.map((p) => [p.team, p]));
  const { libertadores, relegation } = meta.zones;
  const n = table.length;

  const race = (key: "p_title" | "p_top6" | "p_relegation") =>
    predictions[model].teams.map((p) => ({ team: p.team, p: p[key] }));

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold sm:text-3xl">{t.home.title}</h1>
        <p className="max-w-3xl text-muted">{t.home.intro}</p>
      </div>

      <ModelSelector lang={lang} />

      <div className="grid gap-4 md:grid-cols-3">
        <RaceCard title={t.home.titleRace} items={race("p_title")} kind="title" emptyText={t.home.noRace} teams={meta.teams} />
        <RaceCard title={t.home.libertadores} items={race("p_top6")} kind="top" emptyText={t.home.noRace} teams={meta.teams} />
        <RaceCard
          title={t.home.relegation}
          items={race("p_relegation")}
          kind="bottom"
          emptyText={t.home.noRace}
          teams={meta.teams}
        />
      </div>

      <section className="rounded-xl border border-border bg-surface">
        <h2 className="px-4 pt-4 font-semibold">{t.home.table}</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-xs uppercase tracking-wide text-muted">
              <tr className="border-b border-border">
                <th className="px-3 py-2">{t.home.pos}</th>
                <th className="px-3 py-2">{t.home.team}</th>
                <th className="px-2 py-2 text-right">{t.home.pts}</th>
                <th className="px-2 py-2 text-right">{t.home.played}</th>
                <th className="px-2 py-2 text-right">{t.home.gd}</th>
                <th className="hidden px-2 py-2 md:table-cell">{t.home.form}</th>
                <th className="px-2 py-2 text-right">{t.home.expPts}</th>
                <th className="px-2 py-2 text-right">{t.home.pTitle}</th>
                <th className="px-2 py-2 text-right">{t.home.pTop6}</th>
                <th className="px-2 py-2 text-right">{t.home.pReleg}</th>
              </tr>
            </thead>
            <tbody>
              {table.map((row) => {
                const p = byTeam.get(row.team)!;
                const zone =
                  row.position <= libertadores
                    ? "border-l-top"
                    : row.position > n - relegation
                      ? "border-l-bottom"
                      : "border-l-transparent";
                return (
                  <tr key={row.team} className="border-b border-border last:border-0 hover:bg-background">
                    <td className={`border-l-4 px-3 py-1.5 tabular ${zone}`}>{row.position}</td>
                    <td className="px-3 py-1.5 font-medium">
                      <TeamName team={row.team} name={meta.teams[row.team]?.name ?? row.team} short={meta.teams[row.team]?.short} />
                    </td>
                    <td className="tabular px-2 py-1.5 text-right font-semibold">{row.points}</td>
                    <td className="tabular px-2 py-1.5 text-right text-muted">{row.played}</td>
                    <td className="tabular px-2 py-1.5 text-right text-muted">
                      {row.goal_diff > 0 ? `+${row.goal_diff}` : row.goal_diff}
                    </td>
                    <td className="hidden px-2 py-1.5 md:table-cell">
                      <span className="flex gap-1">
                        {row.form.map((r, i) => (
                          <span key={i} title={r} className={`inline-block h-2.5 w-2.5 rounded-full ${FORM_COLORS[r]}`} />
                        ))}
                      </span>
                    </td>
                    <td className="tabular px-2 py-1.5 text-right">{p.expected_points.toFixed(0)}</td>
                    <td className="px-1 py-1">
                      <ProbBar p={p.p_title} kind="title" />
                    </td>
                    <td className="px-1 py-1">
                      <ProbBar p={p.p_top6} kind="top" />
                    </td>
                    <td className="px-1 py-1">
                      <ProbBar p={p.p_relegation} kind="bottom" />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div className="flex flex-wrap gap-4 px-4 py-3 text-xs text-muted">
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-3 w-1 bg-top" /> {t.home.legendTop}
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-3 w-1 bg-bottom" /> {t.home.legendBottom}
          </span>
        </div>
      </section>
    </div>
  );
}
