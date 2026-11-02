"""Display names and short codes for teams (the data uses football-data.co.uk's ASCII names)."""

TEAMS = {
    # football-data name: (display name, 3-letter code)
    "America MG": ("América-MG", "AME"),
    "Athletico-PR": ("Athletico-PR", "CAP"),
    "Atletico GO": ("Atlético-GO", "ACG"),
    "Atletico-MG": ("Atlético-MG", "CAM"),
    "Avai": ("Avaí", "AVA"),
    "Bahia": ("Bahia", "BAH"),
    "Botafogo RJ": ("Botafogo", "BOT"),
    "Bragantino": ("Bragantino", "RBB"),
    "CSA": ("CSA", "CSA"),
    "Ceara": ("Ceará", "CEA"),
    "Chapecoense-SC": ("Chapecoense", "CHA"),
    "Corinthians": ("Corinthians", "COR"),
    "Coritiba": ("Coritiba", "CFC"),
    "Criciuma": ("Criciúma", "CRI"),
    "Cruzeiro": ("Cruzeiro", "CRU"),
    "Cuiaba": ("Cuiabá", "CUI"),
    "Figueirense": ("Figueirense", "FIG"),
    "Flamengo RJ": ("Flamengo", "FLA"),
    "Fluminense": ("Fluminense", "FLU"),
    "Fortaleza": ("Fortaleza", "FOR"),
    "Goias": ("Goiás", "GOI"),
    "Gremio": ("Grêmio", "GRE"),
    "Internacional": ("Internacional", "INT"),
    "Joinville": ("Joinville", "JEC"),
    "Juventude": ("Juventude", "JUV"),
    "Mirassol": ("Mirassol", "MIR"),
    "Nautico": ("Náutico", "NAU"),
    "Palmeiras": ("Palmeiras", "PAL"),
    "Parana": ("Paraná", "PAR"),
    "Ponte Preta": ("Ponte Preta", "PON"),
    "Portuguesa": ("Portuguesa", "POR"),
    "Remo": ("Remo", "REM"),
    "Santa Cruz": ("Santa Cruz", "STA"),
    "Santos": ("Santos", "SAN"),
    "Sao Paulo": ("São Paulo", "SAO"),
    "Sport Recife": ("Sport", "SPT"),
    "Vasco": ("Vasco", "VAS"),
    "Vitoria": ("Vitória", "VIT"),
}


def display_name(team: str) -> str:
    return TEAMS.get(team, (team, ""))[0]


def short_code(team: str) -> str:
    return TEAMS.get(team, ("", team[:3].upper()))[1]
