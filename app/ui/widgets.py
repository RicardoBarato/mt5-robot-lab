"""Small tkinter widget helpers."""

from __future__ import annotations

import tkinter as tk

from app.ui.design_tokens import COLORS, FONT_BODY


def status_card(parent: tk.Widget, title: str, value: str) -> tk.Frame:
    frame = tk.Frame(parent, bg=COLORS["panel"], padx=12, pady=10)
    tk.Label(frame, text=title, bg=COLORS["panel"], fg=COLORS["muted"], font=FONT_BODY).pack(anchor="w")
    tk.Label(frame, text=value, bg=COLORS["panel"], fg=COLORS["text"], font=FONT_BODY).pack(anchor="w")
    return frame
