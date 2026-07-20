"""Google Hybrid HUD — v1 soft bars + v2 spring physics, fluid waves, glow orb, glassmorphism."""

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
    ACCENT_PINK  = QColor(243, 139, 168)
    ACCENT_PEACH = QColor(250, 179, 135)
    ACCENT_GREEN = QColor(166, 227, 161)
    SHIMMER_1    = QColor(137, 180, 250)
    SHIMMER_2    = QColor(203, 166, 247)
    GLASS_TOP    = QColor(255, 255, 255, 22)
    GLASS_INNER  = QColor(255, 255, 255, 6)


class HudState:
    HIDDEN    = "hidden"
    IDLE      = "idle"
    RECORDING = "recording"
    THINKING  = "thinking"
    SUCCESS   = "success"


class Spring:
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

    def set(self, v):
        self.value = v
        self.velocity = 0


class HudWidget(QWidget):
    """Hybrid: soft bars (v1) layered over fluid waves (v2), spring physics, glassmorphism."""

    W = 360
    H = 68
    CORNER_R = 34

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

        # Springs
        self._spr_sc = Spring(0.12, 0.65)
        self._spr_sc.set(0.85); self._spr_sc.target = 0.85
        self._spr_glow = Spring(0.06, 0.75)
        self._spr_glow.set(0); self._spr_glow.target = 0

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

        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    def _reposition(self):
        s = QApplication.primaryScreen().geometry()
        self.move((s.width() - self.W) // 2, s.height() - 130)

    # ── API ──────────────────────────────────────────────────────

    def set_state(self, state):
        if state == self._state:
            return
        self._state = state
        if state == HudState.IDLE:
            self._text = "Right Ctrl"
            self._spr_sc.target = 1.0
            self._spr_glow.target = 10.0
            self._orb_morph = 0.0
            self.show(); self.raise_()
        elif state == HudState.RECORDING:
            self._text = ""
            self._spr_sc.target = 1.03
            self._spr_glow.target = 25.0
            self._orb_morph = 0.0
            self.show(); self.raise_()
        elif state == HudState.THINKING:
            self._text = ""
            self._spr_sc.target = 1.0
            self._spr_glow.target = 18.0
            self._orb_morph = 0.0
        elif state == HudState.SUCCESS:
            self._spr_sc.target = 1.06
            self._spr_glow.target = 30.0
            self._success_flash = 1.0
            self._pulse_ring = 1.0
        elif state == HudState.HIDDEN:
            self._spr_sc.target = 0.85
            self._spr_glow.target = 0.0

    def set_rms(self, rms):
        self._rms = min(1.0, rms * 4.0)

    def set_text(self, text):
        self._text = text

    # ── Tick ─────────────────────────────────────────────────────

    def _tick(self):
        self._spr_sc.update()
        self._spr_glow.update()

        tgt = self._rms if self._state == HudState.RECORDING else 0.0
        self._display_rms += (tgt - self._display_rms) * 0.18

        if self._state == HudState.RECORDING:
            self._phase += 0.06 + self._display_rms * 0.15
        elif self._state == HudState.THINKING:
            self._phase += 0.03
            self._orb_phase += 0.04
            self._orb_morph += (1.0 - self._orb_morph) * 0.04
        elif self._state == HudState.IDLE:
            self._phase += 0.015

        if self._success_flash > 0:
            self._success_flash -= 0.035
        if self._pulse_ring > 0:
            self._pulse_ring -= 0.025

        if (self._state == HudState.HIDDEN
                and abs(self._spr_sc.value - 0.85) < 0.01
                and abs(self._spr_glow.value) < 0.5):
            self.hide(); return

        self.update()

    # ── Paint ────────────────────────────────────────────────────

    def paintEvent(self, event):
        sc = self._spr_sc.value
        if sc < 0.01:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.translate(self.W / 2, self.H / 2)
        p.scale(sc, sc)
        p.translate(-self.W / 2, -self.H / 2)
        p.setOpacity(min(1.0, max(0.0, (sc - 0.7) / 0.3)))

        self._draw_glow(p)
        self._draw_pulse_ring(p)
        self._draw_pill(p)
        self._draw_glass(p)

        if self._state == HudState.RECORDING:
            self._draw_fluid_waves(p)
            self._draw_soft_bars(p)
        elif self._state == HudState.THINKING:
            self._draw_glow_orb(p)
        elif self._state == HudState.SUCCESS:
            self._draw_success(p)
        elif self._state == HudState.IDLE:
            self._draw_idle_breath(p)

        self._draw_text(p)
        p.end()

    # ── Glow ─────────────────────────────────────────────────────

    def _draw_glow(self, p):
        gr = self._spr_glow.value
        if gr < 1:
            return
        c = {HudState.RECORDING: Pal.ACCENT_PINK,
             HudState.THINKING: Pal.SHIMMER_2,
             HudState.SUCCESS: Pal.ACCENT_GREEN}.get(self._state, Pal.SHIMMER_1)
        g = QColor(c); g.setAlpha(int(25 + gr * 1.2))
        ctr = QPointF(self.W / 2, self.H / 2)
        grad = QRadialGradient(ctr, gr * 2.5)
        grad.setColorAt(0, g)
        grad.setColorAt(0.5, QColor(c.red(), c.green(), c.blue(), int(g.alpha() * 0.3)))
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(grad))
        p.drawEllipse(ctr, gr * 2.5, gr * 2.5)
        if gr > 8:
            core = QColor(c); core.setAlpha(int(15 + gr * 0.8))
            g2 = QRadialGradient(ctr, gr * 0.8)
            g2.setColorAt(0, core); g2.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(QBrush(g2))
            p.drawEllipse(ctr, gr * 0.8, gr * 0.8)

    # ── Pulse ring ───────────────────────────────────────────────

    def _draw_pulse_ring(self, p):
        if self._pulse_ring <= 0:
            return
        t = self._pulse_ring
        r = (1.0 - t) * 60 + 30
        a = int(80 * t)
        p.setPen(QPen(QColor(166, 227, 161, a), 2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(self.W / 2, self.H / 2), r, r)

    # ── Pill ─────────────────────────────────────────────────────

    def _draw_pill(self, p):
        r = self.CORNER_R
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, self.W, self.H), r, r)
        bg = Pal.BG_REC if self._state == HudState.RECORDING else Pal.BG
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(bg)); p.drawPath(path)
        p.setPen(QPen(QColor(255, 255, 255, 12), 1))
        p.setBrush(Qt.BrushStyle.NoBrush); p.drawPath(path)

    # ── Glassmorphism ────────────────────────────────────────────

    def _draw_glass(self, p):
        r = self.CORNER_R
        hl = QPainterPath()
        hl.addRoundedRect(QRectF(10, 1, self.W - 20, 1), 1, 1)
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(Pal.GLASS_TOP)); p.drawPath(hl)
        inner = QPainterPath()
        inner.addRoundedRect(QRectF(2, 2, self.W - 4, self.H * 0.38), r - 2, r - 2)
        grad = QLinearGradient(QPointF(0, 2), QPointF(0, self.H * 0.38))
        grad.setColorAt(0, Pal.GLASS_INNER)
        grad.setColorAt(1, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(grad)); p.drawPath(inner)

    # ── Fluid waves (v2 base layer) ──────────────────────────────

    def _draw_fluid_waves(self, p):
        rms = self._display_rms
        margin = 24
        w = self.W - margin * 2
        mid_y = self.H / 2 + 2
        max_amp = 12 + rms * 6

        layers = [
            (0.7, 243, 139, 168, 0.50),
            (0.4, 137, 180, 250, 0.30),
            (0.2, 203, 166, 247, 0.18),
        ]
        for li, (pm, cr, cg, cb, ba) in enumerate(layers):
            path = QPainterPath()
            first = True
            po = li * 0.9
            for px in range(int(w) + 1):
                x = margin + px
                t = px / w
                s = math.sin(self._phase * pm + t * 6.0 + po)
                s2 = math.sin(self._phase * pm * 1.7 + t * 4.0 + po + 1.0)
                s3 = math.sin(self._phase * pm * 0.5 + t * 8.0 + po + 2.0)
                wave = s * 0.5 + s2 * 0.3 + s3 * 0.2
                amp = max_amp * (0.3 + rms * 0.7)
                y = mid_y + wave * amp
                if first:
                    path.moveTo(x, y); first = False
                else:
                    path.lineTo(x, y)
            path.lineTo(margin + w, self.H)
            path.lineTo(margin, self.H)
            path.closeSubpath()
            a = int(255 * ba * (0.5 + rms * 0.5))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(cr, cg, cb, a)))
            p.drawPath(path)

    # ── Soft bars (v1 overlay) ───────────────────────────────────

    def _draw_soft_bars(self, p):
        """V1-style rounded equalizer bars on top of fluid waves."""
        rms = self._display_rms
        n = 7
        bw, gap = 4, 5
        sx = 24
        by = self.H / 2 + 2
        mh = 18

        for i in range(n):
            ph = self._phase + i * 0.6
            wave = (
                abs(math.sin(ph)) * 0.5
                + abs(math.sin(ph * 2.1 + 0.3)) * 0.3
                + abs(math.sin(ph * 0.7 + 1.2)) * 0.2
            )
            h = wave * 0.3 + rms * wave * 0.7
            h = max(0.08, min(1.0, h))
            bh = h * mh

            x1 = sx + i * (bw + gap)
            y1 = by - bh
            x2 = x1 + bw
            y2 = by

            intensity = h
            r = int(243 * intensity + 166 * (1 - intensity))
            g = int(139 * intensity + 139 * (1 - intensity))
            b = int(248 * intensity + 229 * (1 - intensity))
            a = int(180 + 75 * intensity)

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(r, g, b, a)))
            bar = QPainterPath()
            bar.addRoundedRect(QRectF(x1, y1, bw, bh), 2, 2)
            p.drawPath(bar)

    # ── Glow orb (thinking) ──────────────────────────────────────

    def _draw_glow_orb(self, p):
        t = self._orb_phase
        m = self._orb_morph
        cx, cy = self.W / 2, self.H / 2
        orr = 12 + m * 10

        grad = QConicalGradient(QPointF(cx, cy), t * 360)
        grad.setColorAt(0.0, QColor(243, 139, 168, int(180 * m)))
        grad.setColorAt(0.33, QColor(137, 209, 250, int(160 * m)))
        grad.setColorAt(0.66, QColor(203, 166, 247, int(180 * m)))
        grad.setColorAt(1.0, QColor(243, 139, 168, int(180 * m)))

        gg = QRadialGradient(QPointF(cx, cy), orr * 2)
        gg.setColorAt(0, QColor(203, 166, 247, int(50 * m)))
        gg.setColorAt(1, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(gg))
        p.drawEllipse(QPointF(cx, cy), orr * 2, orr * 2)

        p.setBrush(QBrush(grad))
        p.drawEllipse(QPointF(cx, cy), orr, orr)

        dr = 3 + math.sin(t * 3) * 1.5
        p.setBrush(QBrush(QColor(255, 255, 255, int(120 * m))))
        p.drawEllipse(QPointF(cx, cy), dr, dr)

    # ── Idle breath ──────────────────────────────────────────────

    def _draw_idle_breath(self, p):
        b = 0.5 + 0.5 * math.sin(self._phase * 0.8)
        a = int(8 + b * 10)
        ctr = QPointF(self.W / 2, self.H / 2)
        grad = QRadialGradient(ctr, 40)
        grad.setColorAt(0, QColor(137, 180, 250, a))
        grad.setColorAt(1, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(grad))
        p.drawEllipse(ctr, 40, 40)

    # ── Success ──────────────────────────────────────────────────

    def _draw_success(self, p):
        if self._success_flash > 0:
            a = int(50 * self._success_flash)
            r = self.CORNER_R
            path = QPainterPath()
            path.addRoundedRect(QRectF(2, 2, self.W - 4, self.H - 4), r - 2, r - 2)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(166, 227, 161, a)))
            p.drawPath(path)
        cx, cy = self.W / 2, self.H / 2
        s = 12
        p.setPen(QPen(Pal.ACCENT_GREEN, 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        path = QPainterPath()
        path.moveTo(cx - s * 0.6, cy)
        path.lineTo(cx - s * 0.1, cy + s * 0.5)
        path.lineTo(cx + s * 0.7, cy - s * 0.4)
        p.setBrush(Qt.BrushStyle.NoBrush); p.drawPath(path)

    # ── Text ─────────────────────────────────────────────────────

    def _draw_text(self, p):
        if not self._text:
            return
        p.setFont(QFont("Segoe UI", 14))
        c = {HudState.IDLE: Pal.TEXT_DIM,
             HudState.RECORDING: Pal.ACCENT_PINK,
             HudState.THINKING: Pal.SHIMMER_2,
             HudState.SUCCESS: Pal.ACCENT_GREEN}.get(self._state, Pal.TEXT_NORM)
        p.setPen(c)
        p.drawText(QRectF(0, 0, self.W, self.H), Qt.AlignmentFlag.AlignCenter, self._text)

    def run(self):
        self.show()
        sys.exit(QApplication.instance().exec() if QApplication.instance() else QApplication(sys.argv).exec())

    def destroy(self):
        self.hide()


# ── Demo ─────────────────────────────────────────────────────────

def launch_standalone():
    app = QApplication(sys.argv)
    hud = HudWidget()
    hud.show()

    def demo():
        hud.set_state(HudState.IDLE)
        QTimer.singleShot(1500, lambda: (hud.set_state(HudState.RECORDING), _sim(hud, 3000)))
        QTimer.singleShot(4500, lambda: (hud.set_state(HudState.THINKING), hud.set_text("")))
        QTimer.singleShot(6500, lambda: (hud.set_state(HudState.SUCCESS), hud.set_text("1, 2, 3, 4, 5")))
        QTimer.singleShot(8000, lambda: (hud.set_state(HudState.HIDDEN), QTimer.singleShot(600, app.quit)))

    QTimer.singleShot(200, demo)
    sys.exit(app.exec())


def _sim(hud, dur=3000):
    import random
    t = [0]
    tm = QTimer()
    def tick():
        t[0] += 33
        if t[0] >= dur: tm.stop(); return
        hud.set_rms(random.uniform(0.1, 0.6) * (1 + 0.3 * math.sin(t[0] / 180)))
    tm.timeout.connect(tick); tm.start(33)


if __name__ == "__main__":
    launch_standalone()
