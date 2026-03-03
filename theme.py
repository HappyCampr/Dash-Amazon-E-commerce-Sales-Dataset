from __future__ import annotations

LIGHT_THEME = {
    "bg": "#ffffff",
    "text": "#000000",
    "container_bg": "#ffffff",
    "border": "#ddd",
    "card_bg": "#f0f6ff",
    "card_border": "#2c7dd7",
    "accent_blue": "#2c7dd7",
    "accent_green": "#1bb083",
    "accent_dark_blue": "#1957ab",
}

DARK_THEME = {
    "bg": "#1a1a1a",
    "text": "#e8e8e8",
    "container_bg": "#242424",
    "border": "#404040",
    "card_bg": "#303030",
    "card_border": "#5ba3e8",
    "accent_blue": "#5ba3e8",
    "accent_green": "#4dd7a8",
    "accent_dark_blue": "#5b87d4",
}


def get_theme(theme_name: str) -> dict:
    return DARK_THEME if theme_name == "dark" else LIGHT_THEME