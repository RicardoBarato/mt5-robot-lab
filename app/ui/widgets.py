"""Small tkinter widget helpers."""

from __future__ import annotations

import tkinter as tk

from app.ui.design_tokens import COLORS, FONT_BODY, FONT_SECTION, FONT_SMALL, SPACING


def status_card(parent: tk.Widget, title: str, value: str) -> tk.Frame:
    frame = tk.Frame(
        parent,
        bg=COLORS["surface"],
        padx=SPACING["md"],
        pady=SPACING["md"],
        highlightbackground=COLORS["border"],
        highlightthickness=1,
    )
    tk.Label(frame, text=title, bg=COLORS["surface"], fg=COLORS["text_secondary"], font=FONT_SMALL).pack(anchor="w")
    tk.Label(frame, text=value, bg=COLORS["surface"], fg=COLORS["text_primary"], font=FONT_SECTION).pack(
        anchor="w", pady=(SPACING["xs"], 0)
    )
    return frame


def action_button(parent: tk.Widget, label: str, command: object, *, primary: bool = False) -> tk.Button:
    background = COLORS["accent_gold"] if primary else COLORS["surface_alt"]
    foreground = "#07080a" if primary else COLORS["text_primary"]
    return tk.Button(
        parent,
        text=label,
        command=command,
        bg=background,
        fg=foreground,
        activebackground=COLORS["accent_gold"],
        activeforeground="#07080a",
        relief="flat",
        borderwidth=0,
        font=FONT_BODY,
        padx=14,
        pady=9,
        cursor="hand2",
    )


def option_card(parent: tk.Widget, marker: str, title: str, description: str, *, selected: bool = False) -> tk.Frame:
    bg = COLORS["surface_alt"] if selected else COLORS["surface"]
    border = COLORS["accent_gold"] if selected else COLORS["border"]
    frame = tk.Frame(parent, bg=bg, padx=SPACING["md"], pady=SPACING["sm"], highlightbackground=border, highlightthickness=1)
    tk.Label(frame, text=f"{marker} {title}", bg=bg, fg=COLORS["text_primary"], font=FONT_SECTION).pack(anchor="w")
    tk.Label(frame, text=description, bg=bg, fg=COLORS["text_secondary"], font=FONT_SMALL, justify="left", wraplength=290).pack(
        anchor="w", pady=(SPACING["xs"], 0)
    )
    return frame
