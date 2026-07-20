"""Vercel / Cyber-Minimalism HUD — sharp, aggressive, high-tech."""

import sys
import math
import random
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QPen, QBrush,
    QRadialGradient, QLinearGradient, QPainterPath, QConicalGradient,
    QFontDatabase,
)


# ── Palette ──────────────────────────────────────────────────────

class VercelPal:
    BG           = QColor(10, 10, 10, 240)       # #0A0A0A
    BG_REC       = QColor(0, 0, 0, 245)          # pure black
    BORDER       = QColor(255, 255, 255, 20)     # subtle white border
    BORDER_GLOW  = QColor(124, 58, 237, 60)      # #7C3AED violet glow
    TEXT_DIM     = QColor(120, 120, 130)          # muted
    TEXT_NORM    = QColor(255, 255, 255)          # pure white
    ACCENT_VIOLET= QColor(124, 58, 237)          # #7C3AED
    ACCENT_BLUE  = QColor(0, 112, 243)           # #0070F3
    ACCENT_GREEN = QColor(0, 200, 83)            # #00C853
    ACCENT_WHITE = QColor(255, 255, 255)
    DOT_GRID     = QColor(255, 255, 255, 8)


# ── States ───────────────────────────────────────────────────────

class HudState:
    HIDDEN    = "hidden"
    IDLE      = "idle"
    RECORDING = "recording"
    THINKING  = "thinking"
    SUCCESS   = "success"


# ── Vercel HUD Widget ───────────────────────────────────────────

class HudWidget(QWidget):
    """Sharp, high-contrast pill HUD with kinetic visualizer."""

    W = 380
    H = 52
    CORNER_R = 6  # sharp corners, not rounded

    def __init__(self):
        super().__init__()
        self._state = HudState.HIDDEN
        self._rms = 0.0
        self._display_rms = 0.0
        self._phase = 0.0
        self._beam_phase = 0.0
        self._shimmer_phase = 0.0
        self._text = ""
        self._opacity = 0.0
        self._scale = 0.95
        self._border_glow = 0.0
        self._beam_progress = -1.0
        self._success_flash = 0.0
        self._wave_history = [0.0] * 48  # 1D waveform buffer
        self._corner_marks = True
        self._tick_count = 0

        # Monospace font
        self._font = QFont("Consolas", 13)
        self._font_small = QFont("Consolas", 10)
        self._font_bold = QFont("Consolas", 13)
        self._font_bold.setBold(True)

        # Window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFixedSize(self.W, self.H)
        self._reposition()

        # 60 FPS timer
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    def _reposition(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.W) // 2
        y = screen.height() - 120
        self.move(x, y)

    # ── Public API ───────────────────────────────────────────────

    def set_state(self, state: str):
        if state == self._state:
            return
        self._state = state

        if state == HudState.IDLE:
            self._text = "[ RIGHT CTRL ]"
            self.show()
            self.raise_()

        elif state == HudState.RECORDING:
            self._text = ""
            self._wave_history = [0.0] * 48
            self.show()
            self.raise_()

        elif state == HudState.THINKING:
            self._text = ""
            self._beam_progress = 0.0

        elif state == HudState.SUCCESS:
            self._success_flash = 1.0

        elif state == HudState.HIDDEN:
            self.hide()

    def set_rms(self, rms: float):
        self._rms = min(1.0, rms * 4.0)

    def set_text(self, text: str):
        self._text = text

    # ── Animation tick ───────────────────────────────────────────

    def _tick(self):
        self._tick_count += 1
        target_rms = self._rms if self._state == HudState.RECORDING else 0.0
        self._display_rms += (target_rms - self._display_rms) * 0.25  # fast attack

        # Phase
        if self._state == HudState.RECORDING:
            self._phase += 0.15 + self._display_rms * 0.2
            # Push to wave history
            if self._tick_count % 2 == 0:
                self._wave_history.pop(0)
                self._wave_history.append(self._display_rms)

        elif self._state == HudState.THINKING:
            self._beam_phase += 0.06
            self._shimmer_phase += 0.04
            # Animate beam
            if self._beam_progress < 1.0:
                self._beam_progress += 0.02

        # Success flash decay
        if self._success_flash > 0:
            self._success_flash -= 0.05

        # Opacity
        target_op = {
            HudState.HIDDEN: 0.0,
            HudState.IDLE: 1.0,
            HudState.RECORDING: 1.0,
            HudState.THINKING: 1.0,
            HudState.SUCCESS: 1.0,
        }.get(self._state, 0.0)
        self._opacity += (target_op - self._opacity) * 0.15

        # Scale
        target_sc = {
            HudState.HIDDEN: 0.92,
            HudState.IDLE: 1.0,
            HudState.RECORDING: 1.01,
            HudState.THINKING: 1.0,
            HudState.SUCCESS: 1.03,
        }.get(self._state, 0.92)
        self._scale += (target_sc - self._scale) * 0.12

        # Border glow
        target_glow = {
            HudState.HIDDEN: 0.0,
            HudState.IDLE: 15.0,
            HudState.RECORDING: 20.0 + self._display_rms * 30.0,
            HudState.THINKING: 18.0,
            HudState.SUCCESS: 30.0,
        }.get(self._state, 0.0)
        self._border_glow += (target_glow - self._border_glow) * 0.15

        self.update()

    # ── Paint ────────────────────────────────────────────────────

    def paintEvent(self, event):
        if self._opacity < 0.01:
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.translate(self.W / 2, self.H / 2)
        p.scale(self._scale, self._scale)
        p.translate(-self.W / 2, -self.H / 2)
        p.setOpacity(self._opacity)

        self._draw_bg(p)
        self._draw_border(p)
        self._draw_corner_marks(p)
        self._draw_dot_grid(p)

        if self._state == HudState.RECORDING:
            self._draw_waveform(p)
        elif self._state == HudState.THINKING:
            self._draw_beam(p)
            self._draw_shimmer(p)
        elif self._state == HudState.SUCCESS:
            self._draw_success(p)

        self._draw_text(p)

        p.end()

    def _draw_bg(self, p: QPainter):
        bg = VercelPal.BG_REC if self._state == HudState.RECORDING else VercelPal.BG
        r = self.CORNER_R
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, self.W, self.H), r, r)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(bg))
        p.drawPath(path)

    def _draw_border(self, p: QPainter):
        """Animated glowing border."""
        r = self.CORNER_R
        rect = QRectF(0.5, 0.5, self.W - 1, self.H - 1)
        path = QPainterPath()
        path.addRoundedRect(rect, r, r)

        # Base border
        p.setPen(QPen(VercelPal.BORDER, 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

        # Glow border
        if self._border_glow > 2:
            glow_color = {
                HudState.RECORDING: VercelPal.ACCENT_VIOLET,
                HudState.THINKING: VercelPal.ACCENT_BLUE,
                HudState.SUCCESS: VercelPal.ACCENT_GREEN,
            }.get(self._state, VercelPal.BORDER_GLOW)

            glow = QColor(glow_color)
            glow.setAlpha(int(min(80, self._border_glow * 2)))
            p.setPen(QPen(glow, 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(path)

    def _draw_corner_marks(self, p: QPainter):
        """Small cross marks at corners — tech detail."""
        if not self._corner_marks:
            return
        size = 5
        color = QColor(255, 255, 255, 30)
        p.setPen(QPen(color, 1))

        corners = [
            (8, 8), (self.W - 8, 8),
            (8, self.H - 8), (self.W - 8, self.H - 8),
        ]
        for cx, cy in corners:
            p.drawLine(QPointF(cx - size, cy), QPointF(cx + size, cy))
            p.drawLine(QPointF(cx, cy - size), QPointF(cx, cy + size))

    def _draw_dot_grid(self, p: QPainter):
        """Subtle dot grid background."""
        spacing = 20
        dot_r = 0.8
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(VercelPal.DOT_GRID))
        for x in range(spacing, self.W, spacing):
            for y in range(spacing, self.H, spacing):
                p.drawEllipse(QPointF(x, y), dot_r, dot_r)

    def _draw_waveform(self, p: QPainter):
        """Sharp, aggressive 1D waveform — digital oscilloscope style."""
        n = len(self._wave_history)
        if n < 2:
            return

        start_x = 22
        end_x = self.W - 22
        w = end_x - start_x
        mid_y = self.H / 2
        max_amp = 16

        # Draw waveform as sharp polyline
        path = QPainterPath()
        first = True
        for i, rms in enumerate(self._wave_history):
            x = start_x + (i / (n - 1)) * w
            # Sharp random offset for digital look
            noise = math.sin(self._phase * 3 + i * 0.7) * rms * 4
            y = mid_y - rms * max_amp * math.sin(self._phase + i * 0.3) + noise
            if first:
                path.moveTo(x, y)
                first = False
            else:
                path.lineTo(x, y)

        # Violet stroke
        p.setPen(QPen(VercelPal.ACCENT_VIOLET, 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

        # Mirror waveform (below center)
        path2 = QPainterPath()
        first = True
        for i, rms in enumerate(self._wave_history):
            x = start_x + (i / (n - 1)) * w
            noise = math.sin(self._phase * 3 + i * 0.7 + 1) * rms * 3
            y = mid_y + rms * max_amp * math.sin(self._phase + i * 0.3 + 0.5) + noise
            if first:
                path2.moveTo(x, y)
                first = False
            else:
                path2.lineTo(x, y)

        p.setPen(QPen(QColor(124, 58, 237, 120), 1))
        p.drawPath(path2)

        # Center line
        p.setPen(QPen(QColor(255, 255, 255, 15), 1, Qt.PenStyle.DotLine))
        p.drawLine(QPointF(start_x, mid_y), QPointF(end_x, mid_y))

    def _draw_beam(self, p: QPainter):
        """Scanning beam effect along the border."""
        if self._beam_progress < 0 or self._beam_progress > 1:
            return

        # Beam position along perimeter
        perim = 2 * (self.W + self.H)
        pos = self._beam_progress * perim
        beam_len = 80

        r = self.CORNER_R
        rect = QRectF(0, 0, self.W, self.H)

        # Draw bright segment
        beam_color = QColor(0, 112, 243, 180)
        p.setPen(QPen(beam_color, 2))
        p.setBrush(Qt.BrushStyle.NoBrush)

        # Simplified: draw a glowing dot at the beam position
        angle = self._beam_phase * math.pi * 2
        cx = self.W / 2 + math.cos(angle) * (self.W / 2 - 10)
        cy = self.H / 2 + math.sin(angle) * (self.H / 2 - 10)

        grad = QRadialGradient(QPointF(cx, cy), 12)
        grad.setColorAt(0, QColor(0, 112, 243, 200))
        grad.setColorAt(0.5, QColor(124, 58, 237, 80))
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawEllipse(QPointF(cx, cy), 12, 12)

    def _draw_shimmer(self, p: QPainter):
        """Fast monospace shimmer text."""
        t = self._shimmer_phase
        chars = "▓░▒█▓░▒█"
        text = ""
        for i in range(12):
            idx = int((t * 4 + i) % len(chars))
            text += chars[idx]

        p.setFont(self._font_small)
        p.setPen(QColor(255, 255, 255, 60))
        p.drawText(QRectF(0, 0, self.W, self.H), Qt.AlignmentFlag.AlignCenter, text)

    def _draw_success(self, p: QPainter):
        """Sharp white/green flash + geometric checkmark."""
        if self._success_flash > 0:
            alpha = int(40 * self._success_flash)
            r = self.CORNER_R
            path = QPainterPath()
            path.addRoundedRect(QRectF(2, 2, self.W - 4, self.H - 4), r, r)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(0, 200, 83, alpha)))
            p.drawPath(path)

        # Sharp geometric checkmark
        cx, cy = self.W / 2, self.H / 2
        s = 10
        p.setPen(QPen(VercelPal.ACCENT_GREEN, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.FlatCap))
        p.drawLine(QPointF(cx - s, cy), QPointF(cx - s * 0.3, cy + s * 0.7))
        p.drawLine(QPointF(cx - s * 0.3, cy + s * 0.7), QPointF(cx + s, cy - s * 0.5))

    def _draw_text(self, p: QPainter):
        if not self._text:
            return

        # Monospace for all text
        if self._state == HudState.IDLE:
            p.setFont(self._font_small)
        else:
            p.setFont(self._font)

        color = {
            HudState.IDLE: VercelPal.TEXT_DIM,
            HudState.RECORDING: VercelPal.ACCENT_VIOLET,
            HudState.THINKING: VercelPal.ACCENT_BLUE,
            HudState.SUCCESS: VercelPal.ACCENT_GREEN,
        }.get(self._state, VercelPal.TEXT_NORM)

        p.setPen(color)
        p.drawText(QRectF(0, 0, self.W, self.H), Qt.AlignmentFlag.AlignCenter, self._text)

    def run(self):
        self.show()
        sys.exit(QApplication.instance().exec() if QApplication.instance() else QApplication(sys.argv).exec())

    def destroy(self):
        self.hide()


# ── Standalone test ──────────────────────────────────────────────

def launch_standalone():
    app = QApplication(sys.argv)
    hud = HudWidget()
    hud.show()

    def demo():
        hud.set_state(HudState.IDLE)
        QTimer.singleShot(1500, lambda: (
            hud.set_state(HudState.RECORDING),
            _sim_vol(hud, 3000),
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


def _sim_vol(hud, dur=3000):
    t = [0]
    def tick():
        t[0] += 33
        if t[0] >= dur:
            return
        rms = random.uniform(0.1, 0.7) * (1 + 0.4 * math.sin(t[0] / 150))
        hud.set_rms(rms)
    timer = QTimer()
    timer.timeout.connect(tick)
    timer.start(33)


if __name__ == "__main__":
    launch_standalone()
