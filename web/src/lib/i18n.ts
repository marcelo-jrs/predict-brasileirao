export const LANGS = ["pt", "en"] as const;
export type Lang = (typeof LANGS)[number];

export const isLang = (value: string): value is Lang => (LANGS as readonly string[]).includes(value);

const pt = {
  siteTitle: "Brasileirão 2026 · Previsões",
  siteDescription:
    "Chances de título, Libertadores e rebaixamento no Brasileirão Série A 2026, calculadas simulando o resto do campeonato 20 mil vezes.",
  nav: {
    home: "Classificação",
    models: "Modelos",
    history: "Histórico",
    whatif: "E se…?",
    accuracy: "Precisão",
    how: "Como funciona",
  },
  switchLang: "English",
  model: "Modelo",
  models: {
    market: { name: "Mercado", blurb: "força dos times aprendida com as odds das casas de apostas" },
    elo: { name: "Elo", blurb: "força dos times aprendida com os resultados" },
    poisson: { name: "Poisson", blurb: "ataque e defesa aprendidos com os placares" },
  },
  freshness: (date: string, played: number, remaining: number) =>
    `Jogos até ${date} · ${played} disputados · ${remaining} restantes`,
  updated: (date: string) => `Atualizado em ${date}`,
  home: {
    title: "Quem vai para a Libertadores? Quem cai?",
    intro:
      "Simulamos os jogos restantes 20 mil vezes. A porcentagem é a fração das simulações em que o time terminou naquela situação.",
    titleRace: "Título",
    libertadores: "Libertadores (G6)",
    relegation: "Rebaixamento (Z4)",
    noRace: "Já está decidido",
    table: "Classificação e chances",
    pos: "#",
    team: "Time",
    pts: "Pts",
    played: "J",
    gd: "SG",
    form: "Últimos 5",
    expPts: "Pts previstos",
    pTitle: "Título",
    pTop6: "G6",
    pReleg: "Z4",
    legendTop: "Libertadores (1º–6º)",
    legendBottom: "Rebaixamento (17º–20º)",
  },
  modelsPage: {
    title: "Comparando os modelos",
    intro:
      "Três modelos diferentes, três jeitos de medir a força dos times. Quando concordam, a previsão é mais confiável; quando discordam, vale olhar de perto.",
    chances: "Chances por modelo",
    disagree: "Maior divergência",
    spread: "Diferença (máx − mín)",
    strengths: "Força dos times",
    strengthNote:
      "Escalas diferentes: Elo (1500 = média), Mercado (0 = média), Poisson (1,0 = média; ataque = gols feitos, defesa = quanto evita gols).",
    attack: "Ataque",
    defence: "Defesa",
    nextGames: "Próximos jogos",
    home: "Casa",
    draw: "Empate",
    away: "Fora",
    metric: "Métrica",
  },
  historyPage: {
    title: "Como as chances mudaram",
    intro:
      "Cada ponto é o que o modelo teria dito naquela segunda-feira, usando só os jogos disputados até então. O último ponto é hoje.",
    metric: "Mostrar",
    teams: "Times",
    reset: "Times em disputa",
    clear: "Limpar",
    today: "hoje",
    expectedPoints: "Pontos previstos",
  },
  whatif: {
    title: "E se…?",
    intro:
      "Escolha resultados para os próximos jogos e veja as chances mudarem na hora. Jogos sem resultado escolhido continuam sendo sorteados pelo modelo.",
    reset: "Limpar resultados",
    fixed: (n: number) => (n === 1 ? "1 resultado escolhido" : `${n} resultados escolhidos`),
    games: "Jogos restantes",
    result: "Chances com os seus resultados",
    change: "Δ",
    changeNote: "Δ = diferença em pontos percentuais em relação à previsão sem os seus resultados.",
    filterTeam: "Filtrar por time",
    allTeams: "Todos os times",
    noDate: "Data a definir",
    simulating: "Simulando…",
    sims: (n: number) => `${n.toLocaleString("pt-BR")} simulações`,
  },
  accuracyPage: {
    title: "Os modelos acertam?",
    intro: (tune: string, test: string, n: number) =>
      `Escolhemos as configurações dos modelos com as temporadas ${tune} e depois previmos cada um dos ${n.toLocaleString("pt-BR")} jogos de ${test}, usando só informação disponível antes de cada jogo.`,
    leaderboard: "Ranking (menor é melhor)",
    model: "Modelo",
    logLoss: "Log-loss",
    brier: "Brier",
    logLossHelp:
      "Log-loss: quanto o modelo “se surpreendeu” com o que aconteceu. Dar 1% de chance a algo que acontece custa muito caro.",
    brierHelp: "Brier: erro médio ao quadrado entre as chances previstas e o que aconteceu (0 = perfeito).",
    benchmark: "referência (só existe minutos antes do jogo)",
    calibration: "Calibração",
    calibrationHelp:
      "Se um modelo diz “30%”, isso deveria acontecer em ~30% das vezes. Pontos perto da linha tracejada = modelo bem calibrado.",
    predicted: "Chance prevista",
    observed: "Frequência real",
    perfect: "Perfeito",
    names: {
      baseline: "Sempre a média (casa/empate/fora)",
      elo_fixed_draws: "Elo + empates fixos",
      elo: "Elo",
      poisson: "Poisson",
      dixon_coles: "Dixon-Coles",
      market: "Mercado (ratings das odds)",
      closing_odds: "Odds finais das casas",
    } as Record<string, string>,
  },
  footer: {
    source: "Dados: football-data.co.uk e ESPN. Projeto de estudo de ciência de dados.",
    code: "Código no GitHub",
  },
};

type Dict = typeof pt;

const en: Dict = {
  siteTitle: "Brasileirão 2026 · Predictions",
  siteDescription:
    "Title, Libertadores and relegation chances for the 2026 Brazilian Série A, from simulating the rest of the season 20,000 times.",
  nav: {
    home: "Standings",
    models: "Models",
    history: "History",
    whatif: "What if…?",
    accuracy: "Accuracy",
    how: "How it works",
  },
  switchLang: "Português",
  model: "Model",
  models: {
    market: { name: "Market", blurb: "team strength learned from bookmakers' odds" },
    elo: { name: "Elo", blurb: "team strength learned from results" },
    poisson: { name: "Poisson", blurb: "attack and defence learned from scores" },
  },
  freshness: (date: string, played: number, remaining: number) =>
    `Games up to ${date} · ${played} played · ${remaining} remaining`,
  updated: (date: string) => `Updated ${date}`,
  home: {
    title: "Who makes the Libertadores? Who goes down?",
    intro:
      "We simulate the remaining games 20,000 times. Each percentage is the share of simulations in which the team ended up there.",
    titleRace: "Title",
    libertadores: "Libertadores (top 6)",
    relegation: "Relegation (bottom 4)",
    noRace: "Already decided",
    table: "Standings and chances",
    pos: "#",
    team: "Team",
    pts: "Pts",
    played: "P",
    gd: "GD",
    form: "Last 5",
    expPts: "Proj. pts",
    pTitle: "Title",
    pTop6: "Top 6",
    pReleg: "Bottom 4",
    legendTop: "Libertadores (1st–6th)",
    legendBottom: "Relegation (17th–20th)",
  },
  modelsPage: {
    title: "Comparing the models",
    intro:
      "Three models, three ways of measuring team strength. When they agree, the forecast is more trustworthy; when they disagree, it's worth a closer look.",
    chances: "Chances by model",
    disagree: "Biggest disagreement",
    spread: "Spread (max − min)",
    strengths: "Team strength",
    strengthNote:
      "Different scales: Elo (1500 = average), Market (0 = average), Poisson (1.0 = average; attack = goals scored, defence = goals prevented).",
    attack: "Attack",
    defence: "Defence",
    nextGames: "Next games",
    home: "Home",
    draw: "Draw",
    away: "Away",
    metric: "Metric",
  },
  historyPage: {
    title: "How the chances changed",
    intro:
      "Each point is what the model would have said on that Monday, using only the games played by then. The last point is today.",
    metric: "Show",
    teams: "Teams",
    reset: "Teams in contention",
    clear: "Clear",
    today: "today",
    expectedPoints: "Projected points",
  },
  whatif: {
    title: "What if…?",
    intro:
      "Pick results for upcoming games and watch the chances change instantly. Games you leave open are still drawn by the model.",
    reset: "Clear results",
    fixed: (n: number) => (n === 1 ? "1 result picked" : `${n} results picked`),
    games: "Remaining games",
    result: "Chances with your results",
    change: "Δ",
    changeNote: "Δ = change in percentage points compared with the forecast without your results.",
    filterTeam: "Filter by team",
    allTeams: "All teams",
    noDate: "Date TBC",
    simulating: "Simulating…",
    sims: (n: number) => `${n.toLocaleString("en-GB")} simulations`,
  },
  accuracyPage: {
    title: "Are the models any good?",
    intro: (tune: string, test: string, n: number) =>
      `We chose each model's settings using the ${tune} seasons, then predicted every one of the ${n.toLocaleString("en-GB")} games of ${test}, using only information available before each game.`,
    leaderboard: "Leaderboard (lower is better)",
    model: "Model",
    logLoss: "Log-loss",
    brier: "Brier",
    logLossHelp:
      "Log-loss: how “surprised” the model was by what happened. Giving 1% to something that then happens is very costly.",
    brierHelp: "Brier: mean squared gap between the predicted chances and what happened (0 = perfect).",
    benchmark: "benchmark (only exists minutes before kick-off)",
    calibration: "Calibration",
    calibrationHelp:
      "When a model says “30%”, it should happen about 30% of the time. Points near the dashed line = well-calibrated model.",
    predicted: "Predicted chance",
    observed: "Actual frequency",
    perfect: "Perfect",
    names: {
      baseline: "Always the average (home/draw/away)",
      elo_fixed_draws: "Elo + fixed draw rate",
      elo: "Elo",
      poisson: "Poisson",
      dixon_coles: "Dixon-Coles",
      market: "Market (ratings from odds)",
      closing_odds: "Bookmakers' closing odds",
    },
  },
  footer: {
    source: "Data: football-data.co.uk and ESPN. A data-science learning project.",
    code: "Code on GitHub",
  },
};

const DICTS: Record<Lang, Dict> = { pt, en };

export const getDict = (lang: Lang): Dict => DICTS[lang];
export type { Dict };
