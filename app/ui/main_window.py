"""Tkinter main window."""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from app.core.app_config import load_app_config
from app.core.mt5_detection import detect_mt5
from app.ui.design_tokens import COLORS, FONT_SECTION, FONT_SMALL, FONT_SUBTITLE, FONT_TITLE, SPACING
from app.ui.screens import NavigationController, ScreenDefinition, build_screen_registry
from app.ui.widgets import action_button, option_card, status_card


class DesktopNavigationShell:
    """Tkinter shell for the headless navigation registry."""

    def __init__(self, root: tk.Tk, project_root: Path) -> None:
        self.project_root = project_root
        self.config = load_app_config(project_root / "config" / "app.default.json")
        self.screens = build_screen_registry(self.config)
        self.controller = NavigationController(self.screens)
        self.root = root
        self.nav_buttons: dict[str, tk.Button] = {}

        self.root.title("MT5 Robot Lab")
        self.root.geometry("1180x760")
        self.root.minsize(1080, 700)
        self.root.configure(bg=COLORS["background"])

        self.shell = tk.Frame(root, bg=COLORS["background"], padx=SPACING["lg"], pady=SPACING["lg"])
        self.shell.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(
            self.shell,
            bg=COLORS["surface"],
            padx=SPACING["sm"],
            pady=SPACING["md"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            width=250,
        )
        self.sidebar.pack(side="left", fill="y", padx=(0, SPACING["lg"]))
        self.sidebar.pack_propagate(False)

        self.main = tk.Frame(self.shell, bg=COLORS["background"])
        self.main.pack(side="left", fill="both", expand=True)

        self.header = tk.Frame(self.main, bg=COLORS["background"])
        self.header.pack(fill="x", pady=(0, SPACING["lg"]))

        self.content = tk.Frame(self.main, bg=COLORS["background"])
        self.content.pack(fill="both", expand=True)

        self.footer = tk.Frame(self.main, bg=COLORS["background"])
        self.footer.pack(fill="x", pady=(SPACING["lg"], 0))

        self._build_sidebar()
        self._render_current_screen()

    def _build_sidebar(self) -> None:
        tk.Label(
            self.sidebar,
            text="MT5 Robot Lab",
            bg=COLORS["surface"],
            fg=COLORS["text_primary"],
            font=FONT_SECTION,
        ).pack(anchor="w", pady=(0, SPACING["xs"]))
        tk.Label(
            self.sidebar,
            text="Desktop Navigation v2",
            bg=COLORS["surface"],
            fg=COLORS["accent_gold"],
            font=FONT_SMALL,
        ).pack(anchor="w", pady=(0, SPACING["md"]))

        for screen in self.screens:
            button = tk.Button(
                self.sidebar,
                text=screen.title,
                command=lambda screen_id=screen.id: self._go_to(screen_id),
                bg=COLORS["surface"],
                fg=COLORS["text_secondary"],
                activebackground=COLORS["surface_alt"],
                activeforeground=COLORS["text_primary"],
                relief="flat",
                borderwidth=0,
                anchor="w",
                padx=SPACING["sm"],
                pady=SPACING["sm"],
                font=FONT_SMALL,
                cursor="hand2",
            )
            button.pack(fill="x", pady=1)
            self.nav_buttons[screen.id] = button

    def _go_to(self, screen_id: str) -> None:
        self.controller.go_to_screen(screen_id)
        self._render_current_screen()

    def _next(self) -> None:
        self.controller.next_screen()
        self._render_current_screen()

    def _previous(self) -> None:
        self.controller.previous_screen()
        self._render_current_screen()

    def _clear(self, frame: tk.Frame) -> None:
        for child in frame.winfo_children():
            child.destroy()

    def _update_nav_state(self) -> None:
        for screen_id, button in self.nav_buttons.items():
            active = screen_id == self.controller.current_screen
            button.configure(
                bg=COLORS["surface_alt"] if active else COLORS["surface"],
                fg=COLORS["accent_gold"] if active else COLORS["text_secondary"],
            )

    def _render_current_screen(self) -> None:
        self._clear(self.header)
        self._clear(self.content)
        self._clear(self.footer)
        self._update_nav_state()
        screen = self.controller.get_current_definition()
        self._render_header(screen)
        self._render_screen_body(screen)
        self._render_footer(screen)

    def _render_header(self, screen: ScreenDefinition) -> None:
        title_area = tk.Frame(self.header, bg=COLORS["background"])
        title_area.pack(side="left", fill="x", expand=True)
        tk.Label(
            title_area,
            text=screen.title,
            bg=COLORS["background"],
            fg=COLORS["text_primary"],
            font=FONT_TITLE,
        ).pack(anchor="w")
        tk.Label(
            title_area,
            text=screen.subtitle,
            bg=COLORS["background"],
            fg=COLORS["accent_gold"],
            font=FONT_SUBTITLE,
            wraplength=760,
            justify="left",
        ).pack(anchor="w", pady=(SPACING["xs"], 0))

        badge = tk.Frame(
            self.header,
            bg=COLORS["surface_alt"],
            padx=SPACING["md"],
            pady=SPACING["sm"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        badge.pack(side="right", anchor="n")
        tk.Label(badge, text="NO REAL MT5", bg=COLORS["surface_alt"], fg=COLORS["accent_green"], font=FONT_SECTION).pack()
        tk.Label(badge, text="MVP-001", bg=COLORS["surface_alt"], fg=COLORS["text_secondary"], font=FONT_SMALL).pack()

    def _render_screen_body(self, screen: ScreenDefinition) -> None:
        cards = tk.Frame(self.content, bg=COLORS["background"])
        cards.pack(fill="x", pady=(0, SPACING["md"]))
        for index, (title, value) in enumerate(screen.cards):
            card = status_card(cards, title, value)
            card.grid(row=index // 2, column=index % 2, padx=SPACING["xs"], pady=SPACING["xs"], sticky="nsew")
        cards.columnconfigure(0, weight=1)
        cards.columnconfigure(1, weight=1)

        body = tk.Frame(
            self.content,
            bg=COLORS["surface"],
            padx=SPACING["md"],
            pady=SPACING["md"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        body.pack(fill="both", expand=True)

        if screen.id == "intelligence_mode":
            for title, value in screen.cards:
                selected = title == "Local automatico"
                marker = "[\u2713]" if selected else "[ ]"
                option_card(body, marker, title, value, selected=selected).pack(fill="x", pady=(0, SPACING["sm"]))
            return

        for line in screen.body_lines:
            tk.Label(
                body,
                text=line,
                bg=COLORS["surface"],
                fg=COLORS["text_primary"],
                font=FONT_SUBTITLE,
                wraplength=780,
                justify="left",
            ).pack(anchor="w", pady=(0, SPACING["sm"]))

    def _render_footer(self, screen: ScreenDefinition) -> None:
        action_button(self.footer, "Previous", self._previous).pack(side="left", padx=(0, SPACING["sm"]))
        action_button(self.footer, "Next", self._next, primary=True).pack(side="left", padx=(0, SPACING["sm"]))
        action_button(self.footer, screen.primary_action, lambda: self._primary_action(screen), primary=True).pack(
            side="left", padx=(0, SPACING["sm"])
        )
        action_button(self.footer, "Settings", lambda: self._go_to("settings")).pack(side="left", padx=(0, SPACING["sm"]))
        action_button(self.footer, "Exit", self.root.destroy).pack(side="right")

    def _primary_action(self, screen: ScreenDefinition) -> None:
        if screen.id == "welcome":
            self._go_to("lab_selection")
            return
        if screen.id == "settings":
            self._go_to("welcome")
            return
        if screen.id == "mt5_setup":
            result = detect_mt5()
            messagebox.showinfo(
                "MT5 detection",
                f"terminal64.exe: {result.terminal64 or 'not found'}\n"
                f"metaeditor64.exe: {result.metaeditor64 or 'not found'}",
            )
            return
        if screen.id == "export_spreadsheet":
            messagebox.showinfo("Reports", str(self.project_root / "reports" / "public"))
            return
        messagebox.showinfo(screen.title, f"{screen.primary_action} is a placeholder in MVP-001.")


def launch_app(project_root: Path) -> None:
    root = tk.Tk()
    DesktopNavigationShell(root, project_root)
    root.mainloop()
