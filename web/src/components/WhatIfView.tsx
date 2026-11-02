"use client";

import { useDeferredValue, useMemo, useState } from "react";

import { deltaPoints, formatDate, pct } from "@/lib/format";
import { getDict, type Lang } from "@/lib/i18n";
import { simulate, type SimInput, type TeamResult } from "@/lib/simulator";
import type { Fixture, Meta, Outcome, ScoreMatrices, Scorelines, TableRow } from "@/lib/types";

import { useModel } from "./ModelProvider";
import { ModelSelector } from "./ModelSelector";
import { TeamName } from "./TeamName";

const N_SIMS = 10_000;

function Delta({ value, goodWhenUp }: { value: number; goodWhenUp: boolean }) {
  const text = deltaPoints(value);
  if (!text) return null;
  const good = value > 0 === goodWhenUp;
  return <span className={`ml-1 text-xs ${good ? "text-emerald-500" : "text-rose-500"}`}>{text}</span>;
}

export function WhatIfView({
  lang,
  meta,
  table,
  fixtures,
  scorelines,
  scoreMatrices,
}: {
  lang: Lang;
  meta: Meta;
  table: TableRow[];
  fixtures: Fixture[];
  scorelines: Scorelines;
  scoreMatrices: ScoreMatrices;
}) {
  const t = getDict(lang);
  const { model } = useModel();
  const [fixed, setFixed] = useState<Record<number, Outcome>>({});
  const [team, setTeam] = useState("");
  const deferredFixed = useDeferredValue(fixed);
  const name = (id: string) => meta.teams[id]?.name ?? id;

  const baseInput = useMemo((): SimInput => {
    const common = { table, fixtures, nSims: N_SIMS, ...meta.zones };
    const matrices = scoreMatrices[model];
    return matrices
      ? { ...common, scoreMatrices: matrices }
      : { ...common, probs: fixtures.map((f) => f.probs[model]), scorelines };
  }, [table, fixtures, meta.zones, scoreMatrices, scorelines, model]);

  const baseline = useMemo(() => byTeam(simulate(baseInput)), [baseInput]);
  const scenario = useMemo(() => simulate({ ...baseInput, fixed: deferredFixed }), [baseInput, deferredFixed]);
  const pending = fixed !== deferredFixed;

  const nFixed = Object.keys(fixed).length;
  const pick = (id: number, outcome: Outcome) =>
    setFixed((prev) => {
      const next = { ...prev };
      if (next[id] === outcome) delete next[id];
      else next[id] = outcome;
      return next;
    });

  const shown = fixtures
    .filter((f) => !team || f.home === team || f.away === team)
    .sort((a, b) => (a.date ?? "9999").localeCompare(b.date ?? "9999"));
  const groups = new Map<string, Fixture[]>();
  for (const f of shown) {
    const day = f.date ? f.date.slice(0, 10) : "";
    groups.set(day, [...(groups.get(day) ?? []), f]);
  }

  const results = [...scenario].sort((a, b) => a.expected_position - b.expected_position);
  const current = new Map(table.map((r) => [r.team, r]));

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-bold sm:text-3xl">{t.whatif.title}</h1>
        <p className="max-w-3xl text-muted">{t.whatif.intro}</p>
      </div>
      <ModelSelector lang={lang} />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
        <section className="rounded-xl border border-border bg-surface p-4">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <h2 className="font-semibold">{t.whatif.games}</h2>
            <div className="flex items-center gap-2">
              <select
                value={team}
                onChange={(e) => setTeam(e.target.value)}
                aria-label={t.whatif.filterTeam}
                className="rounded-md border border-border bg-surface px-2 py-1 text-sm"
              >
                <option value="">{t.whatif.allTeams}</option>
                {[...table]
                  .sort((a, b) => name(a.team).localeCompare(name(b.team)))
                  .map((r) => (
                    <option key={r.team} value={r.team}>
                      {name(r.team)}
                    </option>
                  ))}
              </select>
              <button
                onClick={() => setFixed({})}
                disabled={nFixed === 0}
                className="rounded-md border border-border px-2 py-1 text-sm text-muted enabled:hover:text-foreground disabled:opacity-40"
              >
                {t.whatif.reset}
              </button>
            </div>
          </div>
          <p className="mb-3 text-xs text-muted">{t.whatif.fixed(nFixed)}</p>

          <div className="max-h-[70vh] space-y-4 overflow-y-auto pr-1">
            {[...groups.entries()].map(([day, games]) => (
              <div key={day || "tbc"}>
                <h3 className="mb-1.5 text-xs font-medium uppercase tracking-wide text-muted">
                  {day ? formatDate(day, lang) : t.whatif.noDate}
                </h3>
                <ul className="space-y-2">
                  {games.map((f) => {
                    const probs = f.probs[model];
                    const options: [Outcome, string, number][] = [
                      ["H", meta.teams[f.home]?.short ?? f.home, probs[0]],
                      ["D", "=", probs[1]],
                      ["A", meta.teams[f.away]?.short ?? f.away, probs[2]],
                    ];
                    return (
                      <li key={f.id} className="rounded-lg border border-border p-2">
                        <div className="mb-1.5 flex flex-wrap items-center gap-x-1.5 text-sm font-medium">
                          <TeamName team={f.home} name={name(f.home)} />
                          <span className="text-muted">×</span>
                          <TeamName team={f.away} name={name(f.away)} />
                          {f.date && <span className="ml-auto text-xs font-normal text-muted">{f.date.slice(11, 16)}</span>}
                        </div>
                        <div className="grid grid-cols-3 gap-1.5">
                          {options.map(([outcome, label, p]) => {
                            const on = fixed[f.id] === outcome;
                            return (
                              <button
                                key={outcome}
                                onClick={() => pick(f.id, outcome)}
                                aria-pressed={on}
                                className={`rounded-md border px-2 py-1 text-xs transition-colors ${
                                  on ? "border-accent bg-accent text-white" : "border-border hover:border-accent"
                                }`}
                              >
                                <span className="font-semibold">{label}</span>{" "}
                                <span className={on ? "" : "text-muted"}>{pct(p)}</span>
                              </button>
                            );
                          })}
                        </div>
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
          </div>
        </section>

        <section className={`rounded-xl border border-border bg-surface p-4 transition-opacity ${pending ? "opacity-60" : ""}`}>
          <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
            <h2 className="font-semibold">{t.whatif.result}</h2>
            <span className="text-xs text-muted">{pending ? t.whatif.simulating : t.whatif.sims(N_SIMS)}</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-xs uppercase tracking-wide text-muted">
                <tr className="border-b border-border">
                  <th className="py-2 pr-2">{t.home.team}</th>
                  <th className="px-2 py-2 text-right">{t.home.pts}</th>
                  <th className="px-2 py-2 text-right">{t.home.expPts}</th>
                  <th className="px-2 py-2 text-right">{t.home.pTitle}</th>
                  <th className="px-2 py-2 text-right">{t.home.pTop6}</th>
                  <th className="px-2 py-2 text-right">{t.home.pReleg}</th>
                </tr>
              </thead>
              <tbody>
                {results.map((r) => {
                  const b = baseline.get(r.team)!;
                  return (
                    <tr key={r.team} className="border-b border-border last:border-0">
                      <td className="py-1.5 pr-2 font-medium">
                        <TeamName team={r.team} name={name(r.team)} short={meta.teams[r.team]?.short} />
                      </td>
                      <td className="tabular px-2 py-1.5 text-right text-muted">{current.get(r.team)?.points}</td>
                      <td className="tabular px-2 py-1.5 text-right">{r.expected_points.toFixed(0)}</td>
                      <td className="tabular whitespace-nowrap px-2 py-1.5 text-right">
                        {pct(r.p_title)}
                        <Delta value={r.p_title - b.p_title} goodWhenUp />
                      </td>
                      <td className="tabular whitespace-nowrap px-2 py-1.5 text-right">
                        {pct(r.p_top6)}
                        <Delta value={r.p_top6 - b.p_top6} goodWhenUp />
                      </td>
                      <td className="tabular whitespace-nowrap px-2 py-1.5 text-right">
                        {pct(r.p_relegation)}
                        <Delta value={r.p_relegation - b.p_relegation} goodWhenUp={false} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-xs text-muted">{t.whatif.changeNote}</p>
        </section>
      </div>
    </div>
  );
}

function byTeam(results: TeamResult[]): Map<string, TeamResult> {
  return new Map(results.map((r) => [r.team, r]));
}
