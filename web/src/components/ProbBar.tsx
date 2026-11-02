import { pct } from "@/lib/format";

const COLORS = {
  title: "bg-amber-500",
  top: "bg-top",
  bottom: "bg-bottom",
} as const;

/** A percentage with a small horizontal bar behind it. */
export function ProbBar({ p, kind }: { p: number; kind: keyof typeof COLORS }) {
  return (
    <div className="relative h-6 min-w-16 overflow-hidden rounded bg-background">
      <div className={`absolute inset-y-0 left-0 ${COLORS[kind]} opacity-25`} style={{ width: `${100 * p}%` }} />
      <span className="tabular relative z-10 flex h-full items-center justify-end pr-1.5 text-sm">{pct(p)}</span>
    </div>
  );
}
