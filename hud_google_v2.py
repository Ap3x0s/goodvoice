"""Google/Soft AI HUD v2 — premium fluid animations, spring physics, glassmorphism."""

import sys
import math
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QPen, QBrush,
    QRadialGradient, QLinearGradient, QPainterPath, QConicalGradient,
)


# ── Palette ──────────────────────────────────────────────────────

class Pal:
    BG           = QColor(18, 18, 24, 210)
    BG_REC       = QColor(22, 22, 30, 225)
    TEXT_DIM     = QColor(108, 112, 134)
    TEXT_NORM    = QColor(205, 214, 244)
    TEXT_BRIGHT  = QColor(245, 224, 220)
    ACCENT_PINK  = QColor(243, 139, 168)
    ACCENT_PEACH = QColor(250, 179, 135)
    ACCENT_GREEN = QColor(166, 227, 161)
    SHIMMER_1    = QColor(137, 180, 250)
    SHIMMER_2    = QColor(203, 166, 247)
    SHIMMER_3    = QColor(243, 139, 168)
    GLASS_TOP    = QColor(255, 255, 255, 22)
    GLASS_INNER  = QColor(255, 255, 255, 6)


# ── States ───────────────────────────────────────────────────────

class HudState:
    HIDDEN    = "hidden"
    IDLE      = "idle"
    RECORDING = "recording"
    THINKING  = "thinking"
    SUCCESS   = "success"


# ── Spring physics ───────────────────────────────────────────────

class Spring:
    """Damped spring for smooth elastic transitions."""
    def __init__(self, stiffness=0.08, damping=0.7):
        self.value = 0.0
        self.target = 0.0
        self.velocity = 0.0
        self.stiffness = stiffness
        self.damping = damping

    def update(self):
        force = (self.target - self.value) * self.stiffness
        self.velocity = (self.velocity + force) * self.damping
        self.value += self.velocity
        return self.value

    def set(self, value):
        self.value = value
        self.velocity = 0


# ── Main Widget ──────────────────────────────────────────────────

class HudWidget(QWidget):
    """Premium pill HUD with fluid waves, glow orb, spring physics, glassmorphism."""

    W = 360
    H = 64
    CORNER_R = 32

    def __init__(self):
        super().__init__()
        self._state = HudState.HIDDEN
        self._rms = 0.0
        self._display_rms = 0.0
        self._phase = 0.0
        self._orb_phase = 0.0
        self._text = ""
        self._success_flash = 0.0
        self._pulse_ring = 0.0

        # Spring physics
        self._spring_scale = Spring(stiffness=0.12, damping=0.65)
        self._spring_scale.set(0.85)
        self._spring_scale.target = 0.85
        self._spring_glow = Spring(stiffness=0.06, damping=0.75)
        self._spring_glow.set(0)
        self._spring_glow.target = 0

        # Orb morph progress (0 = waves, 1 = orb)
        self._orb_morph = 0.0

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

        # 60 FPS
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
            self._text = "Right Ctrl"
            self._spring_scale.target = 1.0
            self._spring_glow.target = 10.0
            self._orb_morph = 0.0
            self.show()
            self.raise_()

        elif state == HudState.RECORDING:
            self._text = ""
            self._spring_scale.target = 1.03
            self._spring_glow.target = 25.0
            self._orb_morph = 0.0
            self.show()
            self.raise_()

        elif state == HudState.THINKING:
            self._text = ""
            self._spring_scale.target = 1.0
            self._spring_glow.target = 18.0
            self._orb_morph = 0.0  # will animate to 1.0

        elif state == HudState.SUCCESS:
            self._spring_scale.target = 1.06
            self._spring_glow.target = 30.0
            self._success_flash = 1.0
            self._pulse_ring = 1.0

        elif state == HudState.HIDDEN:
            self._spring_scale.target = 0.85
            self._spring_glow.target = 0.0

    def set_rms(self, rms: float):
        self._rms = min(1.0, rms * 4.0)

    def set_text(self, text: str):
        self._text = text

    # ── Tick ─────────────────────────────────────────────────────

    def _tick(self):
        # Spring updates
        self._spring_scale.update()
        self._spring_glow.update()

        # RMS lerp
        target_rms = self._rms if self._state == HudState.RECORDING else 0.0
        self._display_rms += (target_rms - self._display_rms) * 0.18

        # Phase
        if self._state == HudState.RECORDING:
            self._phase += 0.06 + self._display_rms * 0.15
        elif self._state == HudState.THINKING:
            self._phase += 0.03
            self._orb_phase += 0.04
            # Morph waves to orb
            self._orb_morph += (1.0 - self._orb_morph) * 0.04
        elif self._state == HudState.IDLE:
            self._phase += 0.015

        # Success decay
        if self._success_flash > 0:
            self._success_flash -= 0.035
        if self._pulse_ring > 0:
            self._pulse_ring -= 0.025

        # Hide when springs settle near hidden
        if (self._state == HudState.HIDDEN
                and abs(self._spring_scale.value - 0.85) < 0.01
                and abs(self._spring_glow.value) < 0.5):
            self.hide()
            return

        self.update()

    # ── Paint ────────────────────────────────────────────────────

    def paintEvent(self, event):
        sc = self._spring_scale.value
        if sc < 0.01:
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Scale transform
        p.translate(self.W / 2, self.H / 2)
        p.scale(sc, sc)
        p.translate(-self.W / 2, -self.H / 2)

        # Global opacity tied to scale
        opacity = min(1.0, (sc - 0.7) / 0.3)
        p.setOpacity(max(0.0, opacity))

        self._draw_dynamic_glow(p)
        self._draw_pulse_ring(p)
        self._draw_pill(p)
        self._draw_glass_highlight(p)

        if self._state == HudState.RECORDING:
            self._draw_fluid_waves(p)
        elif self._state == HudState.THINKING:
            self._draw_glow_orb(p)
        elif self._state == HudState.SUCCESS:
            self._draw_success(p)
        elif self._state == HudState.IDLE:
            self._draw_idle_breath(p)

        self._draw_text(p)
        p.end()

    # ── Dynamic glow ─────────────────────────────────────────────

    def _draw_dynamic_glow(self, p: QPainter):
        """Radial glow that pulses with RMS volume."""
        glow_r = self._spring_glow.value
        if glow_r < 1:
            return

        color = {
            HudState.RECORDING: Pal.ACCENT_PINK,
            HudState.THINKING: Pal.SHIMMER_2,
            HudState.SUCCESS: Pal.ACCENT_GREEN,
        }.get(self._state, Pal.SHIMMER_1)

        # Outer glow
        glow = QColor(color)
        glow.setAlpha(int(25 + glow_r * 1.2))
        center = QPointF(self.W / 2, self.H / 2)
        grad = QRadialGradient(center, glow_r * 2.5)
        grad.setColorAt(0, glow)
        grad.setColorAt(0.5, QColor(color.red(), color.green(), color.blue(), int(glow.alpha() * 0.3)))
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawEllipse(center, glow_r * 2.5, glow_r * 2.5)

        # Inner bright core
        if glow_r > 8:
            core = QColor(color)
            core.setAlpha(int(15 + glow_r * 0.8))
            grad2 = QRadialGradient(center, glow_r * 0.8)
            grad2.setColorAt(0, core)
            grad2.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(QBrush(grad2))
            p.drawEllipse(center, glow_r * 0.8, glow_r * 0.8)

    # ── Pulse ring (success) ─────────────────────────────────────

    def _draw_pulse_ring(self, p: QPainter):
        """Expanding ring on success."""
        if self._pulse_ring <= 0:
            return
        t = self._pulse_ring
        ring_r = (1.0 - t) * 60 + 30
        alpha = int(80 * t)
        center = QPointF(self.W / 2, self.H / 2)
        pen = QPen(QColor(166, 227, 161, alpha), 2)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(center, ring_r, ring_r)

    # ── Pill background ──────────────────────────────────────────

    def _draw_pill(self, p: QPainter):
        r = self.CORNER_R
        rect = QRectF(0, 0, self.W, self.H)
        path = QPainterPath()
        path.addRoundedRect(rect, r, r)

        bg = Pal.BG_REC if self._state == HudState.RECORDING else Pal.BG
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(bg))
        p.drawPath(path)

        # Thin border
        p.setPen(QPen(QColor(255, 255, 255, 12), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

    # ── Glassmorphism highlight ──────────────────────────────────

    def _draw_glass_highlight(self, p: QPainter):
        """Top highlight + inner glow for glass depth."""
        r = self.CORNER_R
        # Top highlight line
        highlight = QPainterPath()
        highlight.addRoundedRect(QRectF(8, 1, self.W - 16, 1), 1, 1)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(Pal.GLASS_TOP))
        p.drawPath(highlight)

        # Inner gradient overlay (top-to-transparent)
        inner = QPainterPath()
        inner.addRoundedRect(QRectF(2, 2, self.W - 4, self.H * 0.4), r - 2, r - 2)
        grad = QLinearGradient(QPointF(0, 2), QPointF(0, self.H * 0.4))
        grad.setColorAt(0, Pal.GLASS_INNER)
        grad.setColorAt(1, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(grad))
        p.drawPath(inner)

    # ── Fluid waves (recording) ──────────────────────────────────

    def _draw_fluid_waves(self, p: QPainter):
        """3 layered sine waves reacting to RMS with phase shift."""
        rms = self._display_rms
        margin = 24
        w = self.W - margin * 2
        mid_y = self.H / 2
        max_amp = 14 + rms * 8

        waves = [
            (0.7, 243, 139, 168, 0.7),   # pink, 70% opacity
            (0.4, 137, 180, 250, 0.4),   # blue, 40% opacity
            (0.2, 203, 166, 247, 0.2),   # violet, 20% opacity
        ]

        for layer, (phase_mult, cr, cg, cb, base_alpha) in enumerate(waves):
            path = QPainterPath()
            first = True
            phase_offset = layer * 0.9  # phase shift between layers

            for px in range(int(w) + 1):
                x = margin + px
                t = px / w

                # Composite sine for organic shape
                s = math.sin(self._phase * phase_mult + t * 6.0 + phase_offset)
                s2 = math.sin(self._phase * phase_mult * 1.7 + t * 4.0 + phase_offset + 1.0)
                s3 = math.sin(self._phase * phase_mult * 0.5 + t * 8.0 + phase_offset + 2.0)

                wave = s * 0.5 + s2 * 0.3 + s3 * 0.2

                # RMS-reactive amplitude
                amp = max_amp * (0.3 + rms * 0.7)
                y = mid_y + wave * amp

                if first:
                    path.moveTo(x, y)
                    first = False
                else:
                    path.lineTo(x, y)

            # Close path to fill area
            path.lineTo(margin + w, self.H)
            path.lineTo(margin, self.H)
            path.closeSubpath()

            alpha = int(255 * base_alpha * (0.5 + rms * 0.5))
            color = QColor(cr, cg, cb, alpha)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(color))
            p.drawPath(path)

    # ── Glow orb (thinking) ──────────────────────────────────────

    def _draw_glow_orb(self, p: QPainter):
        """Morphing glow orb with rotating conic gradient."""
        t = self._orb_phase
        morph = self._orb_morph

        cx = self.W / 2
        cy = self.H / 2

        # Orb size grows with morph
        orb_r = 12 + morph * 10

        # Rotating conic gradient (magenta / cyan / violet)
        grad = QConicalGradient(QPointF(cx, cy), t * 360)
        grad.setColorAt(0.0, QColor(243, 139, 168, int(180 * morph)))
        grad.setColorAt(0.33, QColor(137, 209, 250, int(160 * morph)))
        grad.setColorAt(0.66, QColor(203, 166, 247, int(180 * morph)))
        grad.setColorAt(1.0, QColor(243, 139, 168, int(180 * morph)))

        # Outer soft glow
        glow_grad = QRadialGradient(QPointF(cx, cy), orb_r * 2)
        glow_grad.setColorAt(0, QColor(203, 166, 247, int(50 * morph)))
        glow_grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(glow_grad))
        p.drawEllipse(QPointF(cx, cy), orb_r * 2, orb_r * 2)

        # Core orb
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawEllipse(QPointF(cx, cy), orb_r, orb_r)

        # Bright center dot
        dot_r = 3 + math.sin(t * 3) * 1.5
        p.setBrush(QBrush(QColor(255, 255, 255, int(120 * morph))))
        p.drawEllipse(QPointF(cx, cy), dot_r, dot_r)

    # ── Idle breathing ───────────────────────────────────────────

    def _draw_idle_breath(self, p: QPainter):
        """Subtle breathing glow in idle state."""
        breath = 0.5 + 0.5 * math.sin(self._phase * 0.8)
        alpha = int(8 + breath * 10)
        center = QPointF(self.W / 2, self.H / 2)
        grad = QRadialGradient(center, 40)
        grad.setColorAt(0, QColor(137, 180, 250, alpha))
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawEllipse(center, 40, 40)

    # ── Success ──────────────────────────────────────────────────

    def _draw_success(self, p: QPainter):
        if self._success_flash > 0:
            flash_alpha = int(50 * self._success_flash)
            r = self.CORNER_R
            path = QPainterPath()
            path.addRoundedRect(QRectF(2, 2, self.W - 4, self.H - 4), r - 2, r - 2)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(166, 227, 161, flash_alpha)))
            p.drawPath(path)

        # Checkmark
        cx, cy = self.W / 2, self.H / 2
        s = 12
        p.setPen(QPen(Pal.ACCENT_GREEN, 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        path = QPainterPath()
        path.moveTo(cx - s * 0.6, cy)
        path.lineTo(cx - s * 0.1, cy + s * 0.5)
        path.lineTo(cx + s * 0.7, cy - s * 0.4)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

    # ── Text ─────────────────────────────────────────────────────

    def _draw_text(self, p: QPainter):
        if not self._text:
            return
        font = QFont("Segoe UI", 14)
        p.setFont(font)
        color = {
            HudState.IDLE: Pal.TEXT_DIM,
            HudState.RECORDING: Pal.ACCENT_PINK,
            HudState.THINKING: Pal.SHIMMER_2,
            HudState.SUCCESS: Pal.ACCENT_GREEN,
        }.get(self._state, Pal.TEXT_NORM)
        p.setPen(color)
        p.drawText(QRectF(0, 0, self.W, self.H), Qt.AlignmentFlag.AlignCenter, self._text)

    def run(self):
        self.show()
        sys.exit(QApplication.instance().exec() if QApplication.instance() else QApplication(sys.argv).exec())

    def destroy(self):
        self.hide()


# ── Standalone demo ──────────────────────────────────────────────

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
            QTimer.singleShot(600, app.quit),
        ))

    QTimer.singleShot(200, demo)
    sys.exit(app.exec())


def _sim_vol(hud, dur=3000):
    import random
    t = [0]
    timer = QTimer()
    def tick():
        t[0] += 33
        if t[0] >= dur:
            timer.stop()
            return
        rms = random.uniform(0.1, 0.6) * (1 + 0.3 * math.sin(t[0] / 180))
        hud.set_rms(rms)
    timer.timeout.connect(tick)
    timer.start(33)


if __name__ == "__main__":
    launch_standalone()
