"""Tkinter main window."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from app.core.app_config import load_app_config
from app.core.mt5_detection import detect_mt5
from app.ui.design_tokens import COLORS, FONT_BODY, FONT_SUBTITLE, FONT_TITLE
from app.ui.widgets import status_card


def launch_app(project_root: Path) -> None:
    config = load_app_config(project_root / "config" / "app.default.json")
    root = tk.Tk()
    root.title("MT5 Robot Lab")
    root.geometry("980x680")
    root.configure(bg=COLORS["bg"])

    header = tk.Frame(root, bg=COLORS["bg"], padx=24, pady=18)
    header.pack(fill="x")
    tk.Label(header, text="MT5 Robot Lab", bg=COLORS["bg"], fg=COLORS["text"], font=FONT_TITLE).pack(anchor="w")
    tk.Label(
        header,
        text="Local Strategy Tournament for MetaTrader 5",
        bg=COLORS["bg"],
        fg=COLORS["gold"],
        font=FONT_SUBTITLE,
    ).pack(anchor="w")

    grid = tk.Frame(root, bg=COLORS["bg"], padx=24, pady=8)
    grid.pack(fill="x")
    cards = [
        ("MT5 Status", "Not detected"),
        ("Selected Lab", config.default_lab),
        ("Symbol", config.default_symbol),
        ("Timeframe", config.default_timeframe),
        ("Initial Balance", f"USD {config.default_initial_balance_usd}"),
        ("Max Backtests", str(config.default_max_backtests)),
        ("Champion Count", str(config.default_champion_count)),
        ("Intelligence Mode", config.default_intelligence_mode),
    ]
    for index, (title, value) in enumerate(cards):
        card = status_card(grid, title, value)
        card.grid(row=index // 4, column=index % 4, padx=6, pady=6, sticky="nsew")
    for column in range(4):
        grid.columnconfigure(column, weight=1)

    actions = tk.Frame(root, bg=COLORS["bg"], padx=24, pady=18)
    actions.pack(fill="x")

    def detect() -> None:
        result = detect_mt5()
        messagebox.showinfo(
            "MT5 detection",
            f"terminal64.exe: {result.terminal64 or 'not found'}\n"
            f"metaeditor64.exe: {result.metaeditor64 or 'not found'}",
        )

    buttons = [
        ("Detect MT5", detect),
        ("Configure Tournament", lambda: messagebox.showinfo("Configure", "Bootstrap placeholder.")),
        ("Run Dry-Run Smoke", lambda: messagebox.showinfo("Dry-run", "Dry-run smoke is CLI-backed in this scaffold.")),
        ("Prepare Codex Packet", lambda: messagebox.showinfo("Codex", "Codex packet flow is optional and consent-gated.")),
        ("Open Reports Folder", lambda: messagebox.showinfo("Reports", str(project_root / "reports" / "public"))),
        ("Exit", root.destroy),
    ]
    for label, command in buttons:
        tk.Button(
            actions,
            text=label,
            command=command,
            bg=COLORS["gold"],
            fg="#000000",
            font=FONT_BODY,
            padx=12,
            pady=8,
        ).pack(side="left", padx=5)

    root.mainloop()
