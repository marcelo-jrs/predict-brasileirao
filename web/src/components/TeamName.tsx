import { teamColors } from "@/lib/teams";

/** Two-colour club badge + display name. */
export function TeamName({ team, name, short }: { team: string; name: string; short?: string }) {
  const [primary, secondary] = teamColors(team);
  return (
    <span className="inline-flex items-center gap-2">
      <span
        aria-hidden
        className="inline-block h-3.5 w-3.5 shrink-0 rounded-full border border-border"
        style={{ background: `linear-gradient(135deg, ${primary} 50%, ${secondary} 50%)` }}
      />
      {short ? (
        <>
          <span className="hidden sm:inline">{name}</span>
          <span className="sm:hidden">{short}</span>
        </>
      ) : (
        <span>{name}</span>
      )}
    </span>
  );
}
