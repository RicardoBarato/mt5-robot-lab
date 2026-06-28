"""Desktop screen registry and navigation controller."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.app_config import AppConfig
from app.core.tournament_config import default_tournament_config


@dataclass(frozen=True)
class ScreenDefinition:
    id: str
    title: str
    subtitle: str
    cards: tuple[tuple[str, str], ...]
    body_lines: tuple[str, ...]
    primary_action: str


SCREEN_ORDER = (
    "welcome",
    "lab_selection",
    "mt5_setup",
    "symbol_timeframe",
    "intelligence_mode",
    "tournament_setup",
    "running_backtests",
    "champions_ranking",
    "champion_dna",
    "export_spreadsheet",
    "settings",
)

SCREEN_TITLES = {
    "welcome": "Welcome",
    "lab_selection": "Lab Selection",
    "mt5_setup": "MT5 Setup",
    "symbol_timeframe": "Symbol and Timeframe",
    "intelligence_mode": "Intelligence Mode",
    "tournament_setup": "Tournament Setup",
    "running_backtests": "Running Backtests",
    "champions_ranking": "Champions Ranking",
    "champion_dna": "Champion DNA",
    "export_spreadsheet": "Export Spreadsheet",
    "settings": "Settings",
}

SYMBOL_PRESETS = ("XAUUSD", "USTEC", "US30", "EURUSD", "GBPUSD", "BTCUSD")
TIMEFRAME_PRESETS = ("M1", "M5", "M15", "M30", "H1", "H4", "D1")

INTELLIGENCE_MODE_OPTIONS = (
    {
        "mode": "local_auto",
        "marker": "[\u2713]",
        "title": "Local automatico",
        "description": "Testa variacoes programadas sem usar IA externa.",
        "selected": True,
    },
    {
        "mode": "codex_assisted",
        "marker": "[ ]",
        "title": "Codex assisted",
        "description": "Usa Codex para propor alteracoes MQL5 avancadas. Requer login/autorizacao da conta ChatGPT.",
        "selected": False,
    },
    {
        "mode": "seeds_only",
        "marker": "[ ]",
        "title": "Seeds only",
        "description": "Testa apenas robos-base incluidos.",
        "selected": False,
    },
)

INTELLIGENCE_MODE_TEXT = """Tela: Modo de Inteligencia

[\u2713] Local automatico
    Testa variacoes programadas sem usar IA externa.

[ ] Codex assisted
    Usa Codex para propor alteracoes MQL5 avancadas.
    Requer login/autorizacao da conta ChatGPT.

[ ] Seeds only
    Testa apenas robos-base incluidos.
"""

CHAMPION_DNA_PLACEHOLDER = (
    ("Candidate ID", "pending-candidate"),
    ("Net Profit", "dry-run only"),
    ("Main adjustments", "mutation summary will appear here"),
    ("Risk flags", "martingale/grid/no-stop flags recorded, not blocked"),
    ("Export package", "JSON, Markdown and spreadsheet summary"),
)

MT5_LOGIN_MESSAGE = """Para backtests reais, o MT5 Robot Lab precisa acessar os simbolos e historicos do seu MetaTrader 5.

Abra o MT5, conecte uma conta demo da sua corretora e depois clique em Detectar simbolos.

O MT5 Robot Lab nao precisa salvar sua senha.
"""


class NavigationController:
    """Small headless controller used by both tests and the Tkinter shell."""

    def __init__(self, screens: list[ScreenDefinition], default_screen: str = "welcome") -> None:
        if not screens:
            raise ValueError("screens cannot be empty")
        self.available_screens = [screen.id for screen in screens]
        self._screens = {screen.id: screen for screen in screens}
        if default_screen not in self._screens:
            raise ValueError(f"unknown default screen: {default_screen}")
        self.current_screen = default_screen

    def go_to_screen(self, screen_id: str) -> ScreenDefinition:
        if screen_id not in self._screens:
            raise ValueError(f"unknown screen: {screen_id}")
        self.current_screen = screen_id
        return self._screens[screen_id]

    def next_screen(self) -> ScreenDefinition:
        index = self.available_screens.index(self.current_screen)
        next_index = min(index + 1, len(self.available_screens) - 1)
        self.current_screen = self.available_screens[next_index]
        return self._screens[self.current_screen]

    def previous_screen(self) -> ScreenDefinition:
        index = self.available_screens.index(self.current_screen)
        previous_index = max(index - 1, 0)
        self.current_screen = self.available_screens[previous_index]
        return self._screens[self.current_screen]

    def get_current_definition(self) -> ScreenDefinition:
        return self._screens[self.current_screen]


def build_screen_registry(config: AppConfig) -> list[ScreenDefinition]:
    """Build the ordered product screen registry without opening the GUI."""

    tournament = default_tournament_config()
    tournament_review = (
        f"Lab: {tournament.lab_name}",
        f"Symbol: {tournament.requested_symbol}",
        f"Timeframe: {tournament.timeframe}",
        f"Years: {tournament.backtest_years}",
        f"Initial balance: USD {tournament.initial_balance_usd}",
        f"Max backtests: {tournament.max_backtests}",
        f"Champion count: {tournament.champion_count}",
        f"Intelligence mode: {tournament.intelligence_mode}",
        f"Outputs: {', '.join(tournament.output_formats)}",
        "MT5 real run: disabled in this MVP",
    )

    return [
        ScreenDefinition(
            id="welcome",
            title="MT5 Robot Lab",
            subtitle="Local Strategy Tournament for MetaTrader 5",
            cards=(
                ("Product", config.product_name),
                ("Mode", "desktop bootstrap"),
                ("MT5 real run", "disabled"),
                ("CLI required for user", str(config.cli_required_for_end_user).lower()),
            ),
            body_lines=("Start from setup or open settings. No real MT5 execution is enabled in this MVP.",),
            primary_action="Start Setup",
        ),
        ScreenDefinition(
            id="lab_selection",
            title="Lab Selection",
            subtitle="Choose the external robot laboratory used by the desktop product.",
            cards=(
                ("Lab", tournament.lab_name),
                ("Path", tournament.lab_path),
                ("Role", "external XAUUSD ranking archive"),
                ("Write access", "not used by this MVP"),
            ),
            body_lines=("The app displays the external lab reference but does not edit E:\\ea-xau.",),
            primary_action="Continue",
        ),
        ScreenDefinition(
            id="mt5_setup",
            title="MT5 Setup",
            subtitle="Detect local MetaTrader 5 tools without running a real backtest.",
            cards=(
                ("MT5 Terminal", "not detected"),
                ("MetaEditor", "not detected"),
                ("Account", "user logs in inside MT5"),
                ("Real execution", "not enabled"),
            ),
            body_lines=("Use Detect MT5 to locate terminal64.exe and metaeditor64.exe only.",),
            primary_action="Detect MT5",
        ),
        ScreenDefinition(
            id="symbol_timeframe",
            title="Symbol and Timeframe",
            subtitle="Select the requested asset and timeframe before any future smoke.",
            cards=(
                ("requested_symbol", tournament.requested_symbol),
                ("broker_symbol", "optional"),
                ("timeframe", tournament.timeframe),
                ("Symbol presets", ", ".join(SYMBOL_PRESETS)),
                ("Timeframes", ", ".join(TIMEFRAME_PRESETS)),
            ),
            body_lines=("Broker symbols may vary; real symbol validation is planned for a later MVP.",),
            primary_action="Continue",
        ),
        ScreenDefinition(
            id="intelligence_mode",
            title="Intelligence Mode",
            subtitle="Choose how candidates are prepared.",
            cards=tuple((option["title"], option["description"]) for option in INTELLIGENCE_MODE_OPTIONS),
            body_lines=(INTELLIGENCE_MODE_TEXT,),
            primary_action="Use Local Automatic",
        ),
        ScreenDefinition(
            id="tournament_setup",
            title="Tournament Setup",
            subtitle="Review dry-run tournament defaults.",
            cards=(
                ("Backtest years", str(tournament.backtest_years)),
                ("Initial balance USD", str(tournament.initial_balance_usd)),
                ("Max backtests", str(tournament.max_backtests)),
                ("Champion count", str(tournament.champion_count)),
                ("Output formats", ", ".join(tournament.output_formats)),
            ),
            body_lines=("Tournament Review:", *tournament_review),
            primary_action="Validate Config",
        ),
        ScreenDefinition(
            id="running_backtests",
            title="Running Backtests",
            subtitle="Execution placeholder.",
            cards=(
                ("State", "Ready for dry-run smoke"),
                ("Real MT5", "not enabled"),
                ("Strategy Tester", "not launched"),
                ("Tournament 100", "not started"),
            ),
            body_lines=("Real MT5 execution is not enabled in this MVP.",),
            primary_action="Run Dry-Run Smoke",
        ),
        ScreenDefinition(
            id="champions_ranking",
            title="Champions Ranking",
            subtitle="Ranking placeholder.",
            cards=(
                ("Top Champions", "empty"),
                ("Tournament", "not run"),
                ("Ranking source", "future dry-run or MT5 report"),
                ("Risk", "recorded, not hidden"),
            ),
            body_lines=("No real tournament has been run yet.",),
            primary_action="Open Champion DNA",
        ),
        ScreenDefinition(
            id="champion_dna",
            title="Champion DNA",
            subtitle="Candidate explanation package.",
            cards=CHAMPION_DNA_PLACEHOLDER,
            body_lines=("Champion DNA will record parameter changes, source changes, metrics and risk flags.",),
            primary_action="Continue",
        ),
        ScreenDefinition(
            id="export_spreadsheet",
            title="Export Spreadsheet",
            subtitle="Report export placeholder.",
            cards=(
                ("CSV", "planned"),
                ("Markdown", "planned"),
                ("XLSX", "optional"),
                ("Private reports", "not exported"),
            ),
            body_lines=("CSV/MD/XLSX export will be generated by the export reports module.",),
            primary_action="Open Reports Folder",
        ),
        ScreenDefinition(
            id="settings",
            title="Settings",
            subtitle="Product boundaries and local configuration.",
            cards=(
                ("Config path", "config/app.default.json"),
                ("Local tournament config", "config/local.tournament.json"),
                ("Reports path", "reports/public"),
                ("MT5 terminal path", "placeholder only"),
                ("MT5 MetaEditor path", "placeholder only"),
                ("Codex assisted mode", "optional"),
                ("CLI required for end user", str(config.cli_required_for_end_user).lower()),
            ),
            body_lines=("Passwords, tokens, broker credentials and local MT5 logs are not stored.",),
            primary_action="Back to Welcome",
        ),
    ]
