// Social preview image (Open Graph), rendered at build time from the latest predictions.
import { ImageResponse } from "next/og";

import { getAllPredictions, getMeta } from "./data";
import { formatShortDate, pct } from "./format";
import { getDict, type Lang } from "./i18n";
import { teamColors } from "./teams";

export const OG_SIZE = { width: 1200, height: 630 };

const COPY = {
  pt: {
    headline: "Quem vai para a Libertadores? Quem cai?",
    top: "Libertadores (G6)",
    bottom: "Rebaixamento (Z4)",
    footer: (date: string) => `20 mil simulações · jogos até ${date}`,
  },
  en: {
    headline: "Who makes the Libertadores? Who goes down?",
    top: "Libertadores (top 6)",
    bottom: "Relegation (bottom 4)",
    footer: (date: string) => `20,000 simulations · games up to ${date}`,
  },
};

const BG = "#0d1016";
const SURFACE = "#161a22";
const MUTED = "#98a1b2";
const TOP = "#5aa2ff";
const BOTTOM = "#ff6b6b";

/** Teams whose fate is still open (between 1% and 99%), most likely first. */
function race(items: { team: string; p: number }[], n: number) {
  return items
    .filter((i) => i.p >= 0.01 && i.p <= 0.99)
    .sort((a, b) => b.p - a.p)
    .slice(0, n);
}

function Column({
  title,
  color,
  rows,
  names,
}: {
  title: string;
  color: string;
  rows: { team: string; p: number }[];
  names: Record<string, { name: string }>;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, background: SURFACE, borderRadius: 20, padding: 28 }}>
      <div style={{ display: "flex", flexShrink: 0, fontSize: 30, color, marginBottom: 18 }}>{title}</div>
      {rows.map(({ team, p }) => {
        const [primary, secondary] = teamColors(team);
        return (
          <div key={team} style={{ display: "flex", flexShrink: 0, alignItems: "center", marginBottom: 12 }}>
            <div
              style={{
                display: "flex",
                width: 22,
                height: 22,
                borderRadius: 11,
                marginRight: 14,
                border: "2px solid #39404d",
                backgroundImage: `linear-gradient(135deg, ${primary} 50%, ${secondary} 50%)`,
              }}
            />
            <div style={{ display: "flex", flex: 1, fontSize: 30, color: "#e7eaf0" }}>{names[team]?.name ?? team}</div>
            <div style={{ display: "flex", position: "relative", width: 170, height: 38, borderRadius: 8, background: BG }}>
              <div style={{ display: "flex", width: `${100 * p}%`, height: "100%", borderRadius: 8, background: color, opacity: 0.35 }} />
              <div
                style={{
                  display: "flex",
                  position: "absolute",
                  right: 10,
                  top: 2,
                  fontSize: 28,
                  color: "#e7eaf0",
                }}
              >
                {pct(p)}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function renderOgImage(lang: Lang) {
  const meta = getMeta();
  const model = meta.default_model;
  const teams = getAllPredictions([model])[model].teams;
  const copy = COPY[lang];
  const top = race(teams.map((t) => ({ team: t.team, p: t.p_top6 })), 5);
  const bottom = race(teams.map((t) => ({ team: t.team, p: t.p_relegation })), 5);

  return new ImageResponse(
    (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          width: "100%",
          height: "100%",
          background: BG,
          padding: "44px 56px",
          fontFamily: "sans-serif",
        }}
      >
        <div style={{ display: "flex", fontSize: 30, color: MUTED }}>⚽ {getDict(lang).siteTitle}</div>
        <div style={{ display: "flex", flexShrink: 0, fontSize: 48, color: "#ffffff", marginTop: 6, marginBottom: 28, whiteSpace: "nowrap" }}>
          {copy.headline}
        </div>
        <div style={{ display: "flex", gap: 28, flex: 1 }}>
          <Column title={copy.top} color={TOP} rows={top} names={meta.teams} />
          <Column title={copy.bottom} color={BOTTOM} rows={bottom} names={meta.teams} />
        </div>
        <div style={{ display: "flex", flexShrink: 0, justifyContent: "space-between", marginTop: 22, fontSize: 24, color: MUTED }}>
          <div style={{ display: "flex" }}>{copy.footer(formatShortDate(meta.data_through, lang))}</div>
          <div style={{ display: "flex", color: "#35c27f" }}>predict-brasileirao.vercel.app</div>
        </div>
      </div>
    ),
    OG_SIZE,
  );
}
