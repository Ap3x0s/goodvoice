"""Premium floating HUD — PyQt6 with fluid animations and volume visualization."""

import sys
import math
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint, QSize,
    pyqtProperty, QRectF, QPointF
)
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QFontMetrics, QPen, QBrush,
    QRadialGradient, QLinearGradient, QPainterPath, QConicalGradient
)


# ── Palette ──────────────────────────────────────────────────────

class Pal:
    BG          = QColor(18, 18, 24, 220)      # deep dark, semi-transparent
    BG_RECORD   = QColor(24, 24, 32, 230)
    TEXT_DIM    = QColor(108, 112, 134)         # #6c7086
    TEXT_NORM   = QColor(205, 214, 244)         # #cdd6f4
    TEXT_BRIGHT = QColor(245, 224, 220)         # #f5e0dc
    ACCENT_PINK = QColor(243, 139, 168)         # #f38ba8
    ACCENT_PEACH= QColor(250, 179, 135)         # #fab387
    ACCENT_GREEN= QColor(166, 227, 161)         # #a6e3a1
    GLOW_PINK   = QColor(243, 139, 168, 60)
    SHIMMER_1   = QColor(137, 180, 250)         # #89b4fa
    SHIMMER_2   = QColor(203, 166, 247)         # #cba6f7
    SHIMMER_3   = QColor(243, 139, 168)         # #f38ba8


# ── HUD States ───────────────────────────────────────────────────

class HudState:
    HIDDEN    = "hidden"
    IDLE      = "idle"
    RECORDING = "recording"
    THINKING  = "thinking"
    SUCCESS   = "success"


# ── Main Widget ──────────────────────────────────────────────────

class HudWidget(QWidget):
    """Animated pill-shaped HUD with reactive volume visualization."""

    W = 340
    H = 60
    CORNER_R = 30

    def __init__(self):
        super().__init__()
        self._state = HudState.HIDDEN
        self._rms = 0.0
        self._display_rms = 0.0
        self._phase = 0.0
        self._shimmer_phase = 0.0
        self._text = ""
        self._opacity = 0.0
        self._scale = 0.9
        self._glow_radius = 0.0
        self._success_flash = 0.0

        # Window setup
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(self.W, self.H)

        # Position: bottom center
        self._reposition()

        # Animation timer — 60 FPS
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)  # ~60fps

    def _reposition(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.W) // 2
        y = screen.height() - 120
        self.move(x, y)

    # ── Public API ───────────────────────────────────────────────

    def set_state(self, state: str):
        if state == self._state:
            return
        old = self._state
        self._state = state

        if state == HudState.IDLE:
            self._text = "Right Ctrl"
            self.show()
            self.raise_()
            self.activateWindow()

        elif state == HudState.RECORDING:
            self._text = ""
            self.show()
            self.raise_()

        elif state == HudState.THINKING:
            self._text = ""

        elif state == HudState.SUCCESS:
            self._success_flash = 1.0

        elif state == HudState.HIDDEN:
            self.hide()

    def set_rms(self, rms: float):
        """Set current RMS volume (0.0 - ~1.0). Called from audio thread."""
        self._rms = min(1.0, rms * 4.0)  # amplify for visual

    def set_text(self, text: str):
        self._text = text

    # ── Animation tick ───────────────────────────────────────────

    def _tick(self):
        # Smooth RMS lerp
        target = self._rms if self._state == HudState.RECORDING else 0.0
        self._display_rms += (target - self._display_rms) * 0.15

        # Phase for wave animation
        if self._state == HudState.RECORDING:
            self._phase += 0.08 + self._display_rms * 0.12
        elif self._state == HudState.THINKING:
            self._phase += 0.04

        # Shimmer phase
        if self._state == HudState.THINKING:
            self._shimmer_phase += 0.03

        # Success flash decay
        if self._success_flash > 0:
            self._success_flash -= 0.04
            if self._success_flash < 0:
                self._success_flash = 0

        # Opacity transitions
        target_opacity = {
            HudState.HIDDEN: 0.0,
            HudState.IDLE: 0.95,
            HudState.RECORDING: 1.0,
            HudState.THINKING: 0.98,
            HudState.SUCCESS: 1.0,
        }.get(self._state, 0.0)
        self._opacity += (target_opacity - self._opacity) * 0.12

        # Scale transitions
        target_scale = {
            HudState.HIDDEN: 0.85,
            HudState.IDLE: 1.0,
            HudState.RECORDING: 1.02,
            HudState.THINKING: 1.0,
            HudState.SUCCESS: 1.05,
        }.get(self._state, 0.85)
        self._scale += (target_scale - self._scale) * 0.1

        # Glow
        target_glow = {
            HudState.HIDDEN: 0.0,
            HudState.IDLE: 8.0,
            HudState.RECORDING: 16.0 + self._display_rms * 20.0,
            HudState.THINKING: 12.0,
            HudState.SUCCESS: 24.0,
        }.get(self._state, 0.0)
        self._glow_radius += (target_glow - self._glow_radius) * 0.12

        self.update()

    # ── Painting ─────────────────────────────────────────────────

    def paintEvent(self, event):
        if self._opacity < 0.01:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Apply scale
        painter.translate(self.W / 2, self.H / 2)
        painter.scale(self._scale, self._scale)
        painter.translate(-self.W / 2, -self.H / 2)

        # Global opacity
        painter.setOpacity(self._opacity)

        # Draw glow
        self._draw_glow(painter)

        # Draw pill background
        self._draw_pill(painter)

        # Draw visualization
        if self._state == HudState.RECORDING:
            self._draw_waveform(painter)
        elif self._state == HudState.THINKING:
            self._draw_shimmer(painter)
        elif self._state == HudState.SUCCESS:
            self._draw_success(painter)

        # Draw text
        self._draw_text(painter)

        painter.end()

    def _draw_glow(self, p: QPainter):
        """Draw soft glow behind pill."""
        if self._glow_radius < 1:
            return

        color = {
            HudState.RECORDING: Pal.ACCENT_PINK,
            HudState.THINKING: Pal.SHIMMER_2,
            HudState.SUCCESS: Pal.ACCENT_GREEN,
        }.get(self._state, Pal.TEXT_DIM)

        glow = QColor(color)
        glow.setAlpha(int(40 + self._glow_radius * 1.5))

        center = QPointF(self.W / 2, self.H / 2)
        grad = QRadialGradient(center, self._glow_radius * 2)
        grad.setColorAt(0, glow)
        grad.setColorAt(1, QColor(0, 0, 0, 0))

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawEllipse(center, self._glow_radius * 2, self._glow_radius * 2)

    def _draw_pill(self, p: QPainter):
        """Draw pill-shaped background with glass effect."""
        r = self.CORNER_R
        rect = QRectF(0, 0, self.W, self.H)

        # Base color
        if self._state == HudState.RECORDING:
            bg = Pal.BG_RECORD
        else:
            bg = Pal.BG

        path = QPainterPath()
        path.addRoundedRect(rect, r, r)

        # Fill
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(bg))
        p.drawPath(path)

        # Subtle border
        border_color = QColor(255, 255, 255, 15)
        p.setPen(QPen(border_color, 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

    def _draw_waveform(self, p: QPainter):
        """Draw reactive audio waveform bars."""
        rms = self._display_rms
        num_bars = 7
        bar_w = 4
        gap = 5
        total = num_bars * bar_w + (num_bars - 1) * gap
        start_x = 22
        base_y = self.H / 2 + 10
        max_h = 22

        for i in range(num_bars):
            # Multiple sine waves for organic feel
            phase = self._phase + i * 0.6
            wave = (
                abs(math.sin(phase)) * 0.5
                + abs(math.sin(phase * 2.1 + 0.3)) * 0.3
                + abs(math.sin(phase * 0.7 + 1.2)) * 0.2
            )
            # Mix with RMS for reactivity
            h = wave * 0.4 + rms * wave * 0.6
            h = max(0.08, min(1.0, h))
            bar_h = h * max_h

            x1 = start_x + i * (bar_w + gap)
            y1 = base_y - bar_h
            x2 = x1 + bar_w
            y2 = base_y

            # Color gradient based on intensity
            intensity = h
            r = int(243 * intensity + 166 * (1 - intensity))
            g = int(139 * intensity + 139 * (1 - intensity))
            b = int(248 * intensity + 229 * (1 - intensity))
            alpha = int(180 + 75 * intensity)
            color = QColor(r, g, b, alpha)

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(color))

            # Rounded bar
            bar_path = QPainterPath()
            bar_path.addRoundedRect(QRectF(x1, y1, bar_w, bar_h), 2, 2)
            p.drawPath(bar_path)

    def _draw_shimmer(self, p: QPainter):
        """Draw thinking shimmer gradient."""
        t = self._shimmer_phase

        # Create rotating conical gradient
        center = QPointF(self.W / 2, self.H / 2)
        grad = QConicalGradient(center, t * 360)
        grad.setColorAt(0.0, QColor(137, 180, 250, 30))
        grad.setColorAt(0.3, QColor(203, 166, 247, 40))
        grad.setColorAt(0.6, QColor(243, 139, 168, 30))
        grad.setColorAt(1.0, QColor(137, 180, 250, 30))

        r = self.CORNER_R
        path = QPainterPath()
        path.addRoundedRect(QRectF(4, 4, self.W - 8, self.H - 8), r - 4, r - 4)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawPath(path)

        # Also draw dots
        num_dots = 3
        for i in range(num_dots):
            dot_t = (t * 2 + i * 0.33) % 1.0
            x = self.W / 2 + math.cos(dot_t * math.pi * 2) * 30
            y = self.H / 2 + math.sin(dot_t * math.pi * 2) * 5
            dot_r = 2.5 + math.sin(dot_t * math.pi * 2) * 1
            alpha = int(120 + 80 * math.sin(dot_t * math.pi))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(203, 166, 247, alpha)))
            p.drawEllipse(QPointF(x, y), dot_r, dot_r)

    def _draw_success(self, p: QPainter):
        """Draw success flash / checkmark."""
        if self._success_flash > 0:
            # Flash overlay
            flash_alpha = int(60 * self._success_flash)
            r = self.CORNER_R
            path = QPainterPath()
            path.addRoundedRect(QRectF(2, 2, self.W - 4, self.H - 4), r - 2, r - 2)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(166, 227, 161, flash_alpha)))
            p.drawPath(path)

        # Checkmark
        cx, cy = self.W / 2, self.H / 2
        size = 12
        p.setPen(QPen(Pal.ACCENT_GREEN, 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(
            QPointF(cx - size * 0.6, cy),
            QPointF(cx - size * 0.1, cy + size * 0.5)
        )
        p.drawLine(
            QPointF(cx - size * 0.1, cy + size * 0.5),
            QPointF(cx + size * 0.7, cy - size * 0.4)
        )

    def _draw_text(self, p: QPainter):
        """Draw centered text."""
        if not self._text:
            return

        font = QFont("Segoe UI", 14)
        p.setFont(font)

        # Color based on state
        color = {
            HudState.IDLE: Pal.TEXT_DIM,
            HudState.RECORDING: Pal.ACCENT_PINK,
            HudState.THINKING: Pal.SHIMMER_2,
            HudState.SUCCESS: Pal.ACCENT_GREEN,
        }.get(self._state, Pal.TEXT_NORM)

        p.setPen(color)
        p.drawText(QRectF(0, 0, self.W, self.H), Qt.AlignmentFlag.AlignCenter, self._text)


# ── Launcher (standalone test) ───────────────────────────────────

def launch_standalone():
    """Test HUD standalone."""
    app = QApplication(sys.argv)
    hud = HudWidget()
    hud.show()

    # Demo sequence
    def demo():
        import time

        # Idle
        hud.set_state(HudState.IDLE)

        QTimer.singleShot(1500, lambda: (
            hud.set_state(HudState.RECORDING),
            # Simulate volume
            _simulate_volume(hud, duration_ms=3000),
        ))

        QTimer.singleShot(4500, lambda: (
            hud.set_state(HudState.THINKING),
            hud.set_text(""),
        ))

        QTimer.singleShot(6500, lambda: (
            hud.set_state(HudState.SUCCESS),
            hud.set_text("1, 2, 3, 4, 5"),
        ))

        QTimer.singleShot(8000, lambda: (
            hud.set_state(HudState.HIDDEN),
            app.quit(),
        ))

    QTimer.singleShot(200, demo)
    sys.exit(app.exec())


def _simulate_volume(hud, duration_ms=3000):
    """Simulate volume changes for demo."""
    import random
    start = QTimer()
    elapsed = [0]

    def tick():
        elapsed[0] += 33
        if elapsed[0] >= duration_ms:
            start.stop()
            return
        # Simulate speech-like volume
        rms = random.uniform(0.1, 0.6) * (1 + 0.3 * math.sin(elapsed[0] / 200))
        hud.set_rms(rms)

    start.timeout.connect(tick)
    start.start(33)


if __name__ == "__main__":
    launch_standalone()
