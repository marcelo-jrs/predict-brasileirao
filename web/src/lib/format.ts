import type { Lang } from "./i18n";

/** Probability as a short percentage. Simulations can't prove certainty, so extremes show as <1% / >99%. */
export function pct(p: number, digits = 0): string {
  if (p <= 0) return "–";
  if (p < 0.005) return "<1%";
  if (p >= 0.995) return ">99%";
  return `${(100 * p).toFixed(digits)}%`;
}

/** Signed change in percentage points, e.g. "+12" / "−3"; empty when below half a point. */
export function deltaPoints(delta: number): string {
  const points = Math.round(100 * delta);
  if (points === 0) return "";
  return points > 0 ? `+${points}` : `−${-points}`;
}

const LOCALES: Record<Lang, string> = { pt: "pt-BR", en: "en-GB" };

export function formatDate(iso: string, lang: Lang, withTime = false): string {
  const date = new Date(iso.length === 10 ? `${iso}T12:00:00` : iso);
  return date.toLocaleDateString(LOCALES[lang], {
    day: "2-digit",
    month: "short",
    ...(withTime ? { hour: "2-digit", minute: "2-digit" } : { year: "numeric" }),
  });
}

export function formatNumber(value: number, lang: Lang, digits = 1): string {
  return value.toLocaleString(LOCALES[lang], { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

/** "02 Nov" / "02 de nov." without the year (chart axes). */
export function formatShortDate(iso: string, lang: Lang): string {
  return new Date(`${iso.slice(0, 10)}T12:00:00`).toLocaleDateString(LOCALES[lang], { day: "2-digit", month: "short" });
}
