"""HUD theme dispatcher — google, google_v2, hybrid, hybrid_v2, vercel."""

from hud_google import HudWidget as GoogleHud, HudState
from hud_google_v2 import HudWidget as GoogleV2Hud
from hud_hybrid import HudWidget as HybridHud
from hud_hybrid_v2 import HudWidget as HybridV2Hud
from hud_vercel import HudWidget as VercelHud

__all__ = ["HudWidget", "HudState", "create_hud"]

THEMES = {
    "google":      GoogleHud,
    "google_v2":   GoogleV2Hud,
    "hybrid":      HybridHud,
    "hybrid_v2":   HybridV2Hud,
    "vercel":      VercelHud,
}


def create_hud(theme: str = "google"):
    """Create HUD widget for the given theme.

    Themes:
        "google"     — soft bars + shimmer
        "google_v2"  — spring + fluid waves + glow orb
        "hybrid"     — v1 bars + v2 waves + spring
        "hybrid_v2"  — ★ v1 bars + v1 shimmer + hybrid spring/glass/idle/success
        "vercel"     — sharp cyber
    """
    return THEMES.get(theme, GoogleHud)()


HudWidget = THEMES["hybrid_v2"]
