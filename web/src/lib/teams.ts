// Club colours (primary, secondary) for the small team badges.
const COLORS: Record<string, [string, string]> = {
  "Athletico-PR": ["#c8102e", "#111111"],
  "Atletico-MG": ["#111111", "#ffffff"],
  Bahia: ["#0057a8", "#e30613"],
  "Botafogo RJ": ["#111111", "#ffffff"],
  Bragantino: ["#e4002b", "#ffffff"],
  "Chapecoense-SC": ["#00843d", "#ffffff"],
  Corinthians: ["#ffffff", "#111111"],
  Coritiba: ["#00544d", "#ffffff"],
  Cruzeiro: ["#0033a0", "#ffffff"],
  "Flamengo RJ": ["#c8102e", "#111111"],
  Fluminense: ["#7a1e3a", "#007a3d"],
  Gremio: ["#0d80bf", "#111111"],
  Internacional: ["#e30613", "#ffffff"],
  Mirassol: ["#ffd100", "#00843d"],
  Palmeiras: ["#006437", "#ffffff"],
  Remo: ["#002d72", "#ffffff"],
  Santos: ["#ffffff", "#111111"],
  "Sao Paulo": ["#e30613", "#111111"],
  Vasco: ["#111111", "#ffffff"],
  Vitoria: ["#e30613", "#111111"],
};

export function teamColors(team: string): [string, string] {
  return COLORS[team] ?? ["#94a3b8", "#e2e8f0"];
}
