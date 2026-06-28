"""Design tokens for the desktop UI."""

COLORS = {
    "background": "#07080a",
    "surface": "#15171c",
    "surface_alt": "#1d2027",
    "text_primary": "#f5f1e8",
    "text_secondary": "#aeb4c0",
    "accent_gold": "#d2a84f",
    "accent_green": "#2fbf71",
    "accent_red": "#d95f59",
    "border": "#2b3038",
}

# Backward-compatible aliases for existing helpers.
COLORS.update(
    {
        "bg": COLORS["background"],
        "panel": COLORS["surface"],
        "panel_alt": COLORS["surface_alt"],
        "text": COLORS["text_primary"],
        "muted": COLORS["text_secondary"],
        "gold": COLORS["accent_gold"],
        "danger": COLORS["accent_red"],
    }
)

FONT_FAMILY = "Segoe UI"
FONT_TITLE = (FONT_FAMILY, 26, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 12)
FONT_SECTION = (FONT_FAMILY, 13, "bold")
FONT_BODY = (FONT_FAMILY, 10)
FONT_SMALL = (FONT_FAMILY, 9)

SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 14,
    "lg": 22,
    "xl": 32,
}

RADIUS = {
    "card": 8,
    "button": 8,
}
