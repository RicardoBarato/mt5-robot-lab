"""Screen text definitions."""

INTELLIGENCE_MODE_OPTIONS = [
    {
        "mode": "local_auto",
        "marker": "[✓]",
        "title": "Local automático",
        "description": "Testa variações programadas sem usar IA externa.",
        "selected": True,
    },
    {
        "mode": "codex_assisted",
        "marker": "[ ]",
        "title": "Codex assisted",
        "description": "Usa Codex para propor alterações MQL5 avançadas. Requer login/autorização da conta ChatGPT.",
        "selected": False,
    },
    {
        "mode": "seeds_only",
        "marker": "[ ]",
        "title": "Seeds only",
        "description": "Testa apenas robôs-base incluídos.",
        "selected": False,
    },
]

INTELLIGENCE_MODE_TEXT = """Tela: Modo de Inteligência

[✓] Local automático
    Testa variações programadas sem usar IA externa.

[ ] Codex assisted
    Usa Codex para propor alterações MQL5 avançadas.
    Requer login/autorização da conta ChatGPT.

[ ] Seeds only
    Testa apenas robôs-base incluídos.
"""

CHAMPION_DNA_PLACEHOLDER = [
    ("Candidate ID", "pending-candidate"),
    ("Net Profit", "dry-run only"),
    ("Main adjustments", "mutation summary will appear here"),
    ("Risk flags", "martingale/grid/no-stop flags recorded, not blocked"),
    ("Export package", "JSON, Markdown and spreadsheet summary"),
]

MT5_LOGIN_MESSAGE = """Para backtests reais, o MT5 Robot Lab precisa acessar os simbolos e historicos do seu MetaTrader 5.

Abra o MT5, conecte uma conta demo da sua corretora e depois clique em Detectar simbolos.

O MT5 Robot Lab nao precisa salvar sua senha.
"""
