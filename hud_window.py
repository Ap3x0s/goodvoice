"""HUD theme dispatcher — google, google_v2, hybrid, vercel."""

from hud_google import HudWidget as GoogleHud, HudState
from hud_google_v2 import HudWidget as GoogleV2Hud
from hud_hybrid import HudWidget as HybridHud
from hud_vercel import HudWidget as VercelHud

__all__ = ["HudWidget", "HudState", "create_hud"]

THEMES = {
    "google":     GoogleHud,
    "google_v2":  GoogleV2Hud,
    "hybrid":     HybridHud,
    "vercel":     VercelHud,
}


def create_hud(theme: str = "google"):
    """Create HUD widget for the given theme.

    Themes:
        "google"     — soft Catppuccin pill, simple bars
        "google_v2"  — spring physics, fluid waves, glow orb
        "hybrid"     — v1 bars + v2 waves + spring physics (best of both)
        "vercel"     — sharp cyber-minimalism
    """
    return THEMES.get(theme, GoogleHud)()


HudWidget = GoogleHud
