"""HUD theme dispatcher — picks google, google_v2, or vercel theme."""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from hud_google import HudWidget as GoogleHud, HudState
from hud_google_v2 import HudWidget as GoogleV2Hud
from hud_vercel import HudWidget as VercelHud

__all__ = ["HudWidget", "HudState", "create_hud"]

THEMES = {
    "google": GoogleHud,
    "google_v2": GoogleV2Hud,
    "vercel": VercelHud,
}


def create_hud(theme: str = "google"):
    """Create HUD widget for the given theme.

    Themes:
        "google"     — soft Catppuccin pill, waves, shimmer
        "google_v2"  — premium v2: spring physics, fluid waves, glow orb, glassmorphism
        "vercel"     — sharp cyber-minimalism, oscilloscope, beam scan
    """
    cls = THEMES.get(theme, GoogleHud)
    return cls()


# Default
HudWidget = GoogleHud
