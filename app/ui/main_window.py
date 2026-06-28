"""Tkinter main window."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from app.core.app_config import load_app_config
from app.core.mt5_detection import detect_mt5
from app.ui.design_tokens import COLORS, FONT_SECTION, FONT_SMALL, FONT_SUBTITLE, FONT_TITLE, SPACING
from app.ui.screens import CHAMPION_DNA_PLACEHOLDER, INTELLIGENCE_MODE_OPTIONS
from app.ui.widgets import action_button, option_card, status_card


def launch_app(project_root: Path) -> None:
    config = load_app_config(project_root / "config" / "app.default.json")
    root = tk.Tk()
    root.title("MT5 Robot Lab")
    root.geometry("1160x760")
    root.minsize(1040, 680)
    root.configure(bg=COLORS["background"])

    shell = tk.Frame(root, bg=COLORS["background"], padx=SPACING["xl"], pady=SPACING["lg"])
    shell.pack(fill="both", expand=True)

    header = tk.Frame(shell, bg=COLORS["background"])
    header.pack(fill="x")
    title_area = tk.Frame(header, bg=COLORS["background"])
    title_area.pack(side="left", fill="x", expand=True)
    tk.Label(
        title_area,
        text="MT5 Robot Lab",
        bg=COLORS["background"],
        fg=COLORS["text_primary"],
        font=FONT_TITLE,
    ).pack(anchor="w")
    tk.Label(
        title_area,
        text="Local Strategy Tournament for MetaTrader 5",
        bg=COLORS["background"],
        fg=COLORS["accent_gold"],
        font=FONT_SUBTITLE,
    ).pack(anchor="w", pady=(SPACING["xs"], 0))
    tk.Label(
        title_area,
        text="Desktop scaffold only: no real MT5 run, no real backtest, no live trading.",
        bg=COLORS["background"],
        fg=COLORS["text_secondary"],
        font=FONT_SMALL,
    ).pack(anchor="w", pady=(SPACING["xs"], 0))

    badge = tk.Frame(
        header,
        bg=COLORS["surface_alt"],
        padx=SPACING["md"],
        pady=SPACING["sm"],
        highlightbackground=COLORS["border"],
        highlightthickness=1,
    )
    badge.pack(side="right", anchor="n")
    tk.Label(badge, text="BOOTSTRAP MODE", bg=COLORS["surface_alt"], fg=COLORS["accent_green"], font=FONT_SECTION).pack()
    tk.Label(badge, text="dry-run only", bg=COLORS["surface_alt"], fg=COLORS["text_secondary"], font=FONT_SMALL).pack()

    grid = tk.Frame(shell, bg=COLORS["background"], pady=SPACING["lg"])
    grid.pack(fill="x")
    cards = [
        ("MT5 Status", "Not detected"),
        ("Selected Lab", config.default_lab),
        ("Symbol / Timeframe", f"{config.default_symbol} / {config.default_timeframe}"),
        ("Initial Balance", f"USD {config.default_initial_balance_usd:,}"),
        ("Max Backtests", str(config.default_max_backtests)),
        ("Champion Count", str(config.default_champion_count)),
        ("Intelligence Mode", config.default_intelligence_mode),
    ]
    for index, (title, value) in enumerate(cards):
        card = status_card(grid, title, value)
        card.grid(row=index // 4, column=index % 4, padx=SPACING["xs"], pady=SPACING["xs"], sticky="nsew")
    for column in range(4):
        grid.columnconfigure(column, weight=1)

    actions = tk.Frame(
        shell,
        bg=COLORS["surface"],
        padx=SPACING["md"],
        pady=SPACING["md"],
        highlightbackground=COLORS["border"],
        highlightthickness=1,
    )
    actions.pack(fill="x", pady=(0, SPACING["lg"]))

    def detect() -> None:
        result = detect_mt5()
        messagebox.showinfo(
            "MT5 detection",
            f"terminal64.exe: {result.terminal64 or 'not found'}\n"
            f"metaeditor64.exe: {result.metaeditor64 or 'not found'}",
        )

    buttons = [
        ("Detect MT5", detect, True),
        (
            "Configure Tournament",
            lambda: messagebox.showinfo("Configure", "Tournament setup screen is planned for the next product pass."),
            False,
        ),
        (
            "Run Dry-Run Smoke",
            lambda: messagebox.showinfo("Dry-run", "Dry-run smoke remains non-MT5 and validation-only in this scaffold."),
            False,
        ),
        (
            "Prepare Codex Packet",
            lambda: messagebox.showinfo(
                "Codex", "Codex assisted mode is optional and requires explicit user authorization."
            ),
            False,
        ),
        ("Open Reports Folder", lambda: messagebox.showinfo("Reports", str(project_root / "reports" / "public")), False),
        ("Exit", root.destroy, False),
    ]
    for label, command, primary in buttons:
        action_button(actions, label, command, primary=primary).pack(side="left", padx=(0, SPACING["sm"]))

    content = tk.Frame(shell, bg=COLORS["background"])
    content.pack(fill="both", expand=True)

    intelligence = tk.Frame(content, bg=COLORS["background"])
    intelligence.grid(row=0, column=0, sticky="nsew", padx=(0, SPACING["md"]))
    tk.Label(
        intelligence,
        text="Modo de Inteligencia",
        bg=COLORS["background"],
        fg=COLORS["text_primary"],
        font=FONT_SECTION,
    ).pack(anchor="w", pady=(0, SPACING["sm"]))
    for option in INTELLIGENCE_MODE_OPTIONS:
        option_card(
            intelligence,
            option["marker"],
            option["title"],
            option["description"],
            selected=bool(option["selected"]),
        ).pack(fill="x", pady=(0, SPACING["sm"]))

    champion = tk.Frame(
        content,
        bg=COLORS["surface"],
        padx=SPACING["md"],
        pady=SPACING["md"],
        highlightbackground=COLORS["border"],
        highlightthickness=1,
    )
    champion.grid(row=0, column=1, sticky="nsew")
    tk.Label(champion, text="Champion DNA", bg=COLORS["surface"], fg=COLORS["text_primary"], font=FONT_SECTION).pack(
        anchor="w"
    )
    tk.Label(
        champion,
        text="Best candidate summary will appear here after a dry-run or tournament.",
        bg=COLORS["surface"],
        fg=COLORS["text_secondary"],
        font=FONT_SMALL,
        wraplength=420,
        justify="left",
    ).pack(anchor="w", pady=(SPACING["xs"], SPACING["md"]))
    for label, value in CHAMPION_DNA_PLACEHOLDER:
        row = tk.Frame(champion, bg=COLORS["surface"])
        row.pack(fill="x", pady=SPACING["xs"])
        tk.Label(
            row,
            text=label,
            width=18,
            anchor="w",
            bg=COLORS["surface"],
            fg=COLORS["text_secondary"],
            font=FONT_SMALL,
        ).pack(side="left")
        tk.Label(
            row,
            text=value,
            anchor="w",
            bg=COLORS["surface"],
            fg=COLORS["text_primary"],
            font=FONT_SMALL,
            wraplength=300,
        ).pack(side="left", fill="x", expand=True)

    content.columnconfigure(0, weight=1)
    content.columnconfigure(1, weight=1)
    content.rowconfigure(0, weight=1)

    footer = tk.Label(
        shell,
        text="Research software foundation. Not financial advice. No execution approval.",
        bg=COLORS["background"],
        fg=COLORS["text_secondary"],
        font=FONT_SMALL,
    )
    footer.pack(anchor="w", pady=(SPACING["md"], 0))

    root.mainloop()
