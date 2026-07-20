"""HUD theme dispatcher — picks google or vercel theme."""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from hud_google import HudWidget as GoogleHud, HudState
from hud_vercel import HudWidget as VercelHud

# Re-export HudState for external use
__all__ = ["HudWidget", "HudState", "create_hud"]


def create_hud(theme: str = "google"):
    """Create HUD widget for the given theme.

    Args:
        theme: "google" for soft/cute style, "vercel" for sharp/cyber style

    Returns:
        HudWidget instance (both share the same API)
    """
    if theme == "vercel":
        return VercelHud()
    return GoogleHud()


# Default for backward compatibility
HudWidget = GoogleHud
