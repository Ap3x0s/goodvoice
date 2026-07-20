"""GoodVoice Settings — Neo-Glassmorphism + Neon Glow UI."""

import sys, math
from datetime import datetime, timedelta
from collections import defaultdict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QMessageBox, QApplication, QFrame,
    QStackedWidget, QScrollArea, QSizePolicy, QToolTip
)
from PyQt6.QtCore import Qt, QTimer, QPoint, QRectF, QPointF
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QLinearGradient, QPen, QBrush,
    QRadialGradient, QPainterPath, QConicalGradient
)

from settings import Settings
from stats import Stats
from history import History


# ── Tokens ───────────────────────────────────────────────────────

BG       = "#08080C"
BG_SB    = "#0C0C12"
C1       = "#FFFFFF"
C2       = "#94A3B8"
C3       = "#64748B"
AC       = "#6366F1"
AC_L     = "#818CF8"
AC_D     = "#4F46E5"
RED      = "#EF4444"
F        = "Segoe UI"
FM       = "Consolas"


# ── Glass card with glow ─────────────────────────────────────────

class GlassCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._glow = 0.0
        self._target_glow = 0.0
        self.setStyleSheet("background:transparent;border:none;")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumHeight(64)

    def enterEvent(self, e):
        self._target_glow = 1.0

    def leaveEvent(self, e):
        self._target_glow = 0.0

    def paintEvent(self, e):
        self._glow += (self._target_glow - self._glow) * 0.15
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        r = 16

        # Background glass
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), r, r)
        glass = QColor(255, 255, 255, int(3 + self._glow * 5))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(glass))
        p.drawPath(path)

        # Border
        border_alpha = int(20 + self._glow * 40)
        border_color = QColor(99, 102, 241, border_alpha) if self._glow > 0.01 else QColor(255, 255, 255, 20)
        p.setPen(QPen(border_color, 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

        # Glow effect
        if self._glow > 0.01:
            glow = QRadialGradient(QPointF(w / 2, 0), w * 0.6)
            glow.setColorAt(0, QColor(99, 102, 241, int(15 * self._glow)))
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(glow))
            p.drawEllipse(QPointF(w / 2, 0), w * 0.6, h * 0.8)

        p.end()
        if abs(self._glow - self._target_glow) > 0.001:
            self.update()


# ── Neon toggle switch ───────────────────────────────────────────

class NeonToggle(QWidget):
    toggled = lambda self: None

    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self._pos = 1.0 if checked else 0.0
        self.setFixedSize(52, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def isChecked(self):
        return self._checked

    def setChecked(self, v):
        self._checked = v
        self.update()

    def mousePressEvent(self, e):
        self._checked = not self._checked
        self.update()

    def paintEvent(self, e):
        target = 1.0 if self._checked else 0.0
        self._pos += (target - self._pos) * 0.2

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Track
        track_color = QColor(AC) if self._checked else QColor(42, 42, 56)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(track_color))
        p.drawRoundedRect(QRectF(0, 0, 52, 28), 14, 14)

        # Glow when on
        if self._checked:
            glow = QRadialGradient(QPointF(26, 14), 30)
            glow.setColorAt(0, QColor(99, 102, 241, 40))
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            p.setBrush(QBrush(glow))
            p.drawEllipse(QPointF(26, 14), 30, 30)

        # Thumb
        thumb_x = 4 + self._pos * 24
        thumb_color = QColor(255, 255, 255)
        p.setBrush(QBrush(thumb_color))
        p.drawEllipse(QPointF(thumb_x + 10, 14), 9, 9)

        p.end()
        if abs(self._pos - target) > 0.01:
            self.update()


# ── Combo ────────────────────────────────────────────────────────

def cmb(items, cur=None):
    c = QComboBox()
    c.addItems(items)
    if cur and cur in items:
        c.setCurrentText(cur)
    c.setFixedWidth(180)
    c.setFixedHeight(36)
    return c


# ── Sidebar button ───────────────────────────────────────────────

class Nav(QPushButton):
    def __init__(self, icon, text):
        super().__init__(f"  {icon}  {text}")
        self.setFixedHeight(40)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {C3};
                border: none;
                border-left: 3px solid transparent;
                border-radius: 0 10px 10px 0;
                padding: 0 16px;
                text-align: left;
                font-size: 13px;
                font-family: {F};
            }}
            QPushButton:hover {{
                background: rgba(99,102,241,0.06);
                color: {C2};
            }}
            QPushButton:checked {{
                background: rgba(99,102,241,0.12);
                color: {C1};
                font-weight: 600;
                border-left: 3px solid {AC};
            }}
        """)


# ── Chart ────────────────────────────────────────────────────────

class FluidChart(QWidget):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._hover = -1
        self.setMouseTracking(True)

    def mouseMoveEvent(self, e):
        idx = self._hit(e.pos())
        if idx != self._hover:
            self._hover = idx
            self.update()
            if 0 <= idx < len(self.data):
                lbl, val, date = self.data[idx]
                QToolTip.showText(e.globalPos(), f"{date}: {val} слов", self)
            else:
                QToolTip.hideText()

    def leaveEvent(self, e):
        self._hover = -1
        self.update()
        QToolTip.hideText()

    def _hit(self, pos):
        w, h = self.width(), self.height()
        ml, mr, mt, mb = 8, 8, 16, 32
        cw = w - ml - mr
        n = len(self.data)
        bw = max(14, min(22, (cw - (n - 1) * 5) // n))
        gap = 5
        total = n * bw + (n - 1) * gap
        sx = ml + (cw - total) // 2
        for i in range(n):
            x = sx + i * (bw + gap)
            if x <= pos.x() <= x + bw:
                return i
        return -1

    def paintEvent(self, e):
        if not self.data:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        ml, mr, mt, mb = 8, 8, 16, 32
        cw, ch = w - ml - mr, h - mt - mb
        mx = max(v for _, v, _ in self.data) or 1

        # Grid
        pen = QPen(QColor(255, 255, 255, 6), 1, Qt.PenStyle.DotLine)
        p.setPen(pen)
        for i in range(1, 5):
            gy = mt + int(ch * i / 5)
            p.drawLine(ml, gy, w - mr, gy)

        n = len(self.data)
        bw = max(14, min(22, (cw - (n - 1) * 5) // n))
        gap = 5
        total = n * bw + (n - 1) * gap
        sx = ml + (cw - total) // 2

        for i, (lbl, val, _) in enumerate(self.data):
            x = sx + i * (bw + gap)
            is_hv = (i == self._hover)

            if val == 0:
                bh = 4
                y = mt + ch - bh
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(QColor(255, 255, 255, 10)))
                p.drawRoundedRect(x, y, bw, bh, 2, 2)
            else:
                bh = max(8, int((val / mx) * ch))
                y = mt + ch - bh

                # Glow under bar
                if is_hv:
                    glow = QRadialGradient(QPointF(x + bw / 2, y + bh / 2), bh * 0.8)
                    glow.setColorAt(0, QColor(99, 102, 241, 50))
                    glow.setColorAt(1, QColor(0, 0, 0, 0))
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(QBrush(glow))
                    p.drawEllipse(QPointF(x + bw / 2, y + bh / 2), bh * 0.8, bh * 0.8)

                # Bar gradient
                g = QLinearGradient(x, y, x, y + bh)
                c_top = QColor(AC_L) if is_hv else QColor(AC)
                g.setColorAt(0, c_top)
                g.setColorAt(1, QColor(AC_D))
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(g))
                p.drawRoundedRect(x, y, bw, bh, 4, 4)

            # Label
            p.setPen(QColor(C3))
            p.setFont(QFont(F, 9))
            p.drawText(x, h - 22, bw, 18, Qt.AlignmentFlag.AlignCenter, lbl)

        p.end()


# ── History row ──────────────────────────────────────────────────

class HRow(QWidget):
    def __init__(self, entry):
        super().__init__()
        self._text = entry["text"]
        self._ts = entry["timestamp"]
        self._word_count = entry.get("word_count", len(self._text.split()))
        self._glow = 0.0
        self._target = 0.0
        self.setFixedHeight(56)
        self.setMouseTracking(True)

    def enterEvent(self, e):
        self._target = 1.0
        self.update()

    def leaveEvent(self, e):
        self._target = 0.0
        self.update()

    def paintEvent(self, e):
        self._glow += (self._target - self._glow) * 0.2
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        r = 12

        # Glass bg
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), r, r)
        a = int(3 + self._glow * 8)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(255, 255, 255, a)))
        p.drawPath(path)

        # Border
        ba = int(18 + self._glow * 30)
        bc = QColor(99, 102, 241, ba) if self._glow > 0.01 else QColor(255, 255, 255, 18)
        p.setPen(QPen(bc, 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

        # Glow
        if self._glow > 0.01:
            glow = QRadialGradient(QPointF(w / 2, h / 2), w * 0.5)
            glow.setColorAt(0, QColor(99, 102, 241, int(8 * self._glow)))
            glow.setColorAt(1, QColor(0, 0, 0, 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(glow))
            p.drawEllipse(QPointF(w / 2, h / 2), w * 0.5, h)

        # Time pill
        ts = datetime.fromtimestamp(self._entry_ts()).strftime("%H:%M") if hasattr(self, '_ts') else "00:00"
        p.setPen(QColor(C3))
        p.setFont(QFont(FM, 10))
        p.drawRoundedRect(QRectF(16, 14, 52, 28), 8, 8)
        p.setPen(QColor("#A0A0C0"))
        p.drawText(QRectF(16, 14, 52, 28), Qt.AlignmentFlag.AlignCenter, ts)

        # Text
        txt = self._text[:80] + ("..." if len(self._text) > 80 else "")
        p.setPen(QColor(C2))
        p.setFont(QFont(F, 13))
        p.drawText(QRectF(80, 10, w - 200, 36), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, txt)

        # Word chip
        chip = f"{len(self._text.split())} слов"
        p.setPen(QColor(AC))
        p.setFont(QFont(F, 10))
        cr = QRectF(w - 120, 15, 72, 26)
        p.setBrush(QBrush(QColor(99, 102, 241, 15)))
        p.setPen(QPen(QColor(99, 102, 241, 50), 1))
        p.drawRoundedRect(cr, 10, 10)
        p.drawText(cr, Qt.AlignmentFlag.AlignCenter, chip)

        p.end()

    def _entry_ts(self):
        return 0

    def set_entry(self, entry):
        self._ts = entry["timestamp"]
        self._text = entry["text"]
        self._word_count = entry.get("word_count", len(self._text.split()))


# ── KPI card with neon glow ──────────────────────────────────────

class NeonKPI(QFrame):
    def __init__(self, val, lbl):
        super().__init__()
        self._val = val
        self._lbl = lbl
        self.setMinimumHeight(96)
        self.setStyleSheet("background:transparent;border:none;")

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        r = 16

        # Glass bg
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), r, r)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(255, 255, 255, 3)))
        p.drawPath(path)

        # Border
        p.setPen(QPen(QColor(255, 255, 255, 18), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

        # Neon glow at top
        glow = QRadialGradient(QPointF(w / 2, 0), w * 0.5)
        glow.setColorAt(0, QColor(99, 102, 241, 12))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(glow))
        p.drawEllipse(QPointF(w / 2, 0), w * 0.5, h * 0.6)

        # Value — gradient text effect (white to light purple)
        p.setFont(QFont(FM, 28, QFont.Weight.Bold))
        p.setPen(QColor(C1))
        p.drawText(QRectF(20, 14, w - 40, 40), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self._val)

        # Label
        p.setFont(QFont(F, 12))
        p.setPen(QColor(C2))
        p.drawText(QRectF(20, 54, w - 40, 30), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, self._lbl)

        p.end()


# ── Main Window ──────────────────────────────────────────────────

class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = Settings().load()
        self.stats = Stats().load()
        self.history = History().load()
        self._build()

    def _build(self):
        self.setWindowTitle("GoodVoice")
        self.resize(920, 640)
        self.setMinimumSize(850, 580)
        self.setStyleSheet(f"""
            QWidget {{
                background: {BG};
                color: {C1};
                font-family: {F};
            }}
            QScrollArea {{ border:none; background:transparent; }}
            QScrollBar:vertical {{
                background: transparent;
                width: 5px;
                margin: 0 4px 0 0;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(99,102,241,0.2);
                border-radius: 2px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background:none; }}
            QComboBox {{
                background: rgba(255,255,255,0.04);
                color: {C1};
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 10px;
                padding: 7px 14px;
                font-size: 13px;
            }}
            QComboBox:hover {{
                border-color: rgba(99,102,241,0.4);
                background: rgba(255,255,255,0.06);
            }}
            QComboBox::drop-down {{ border:none; width:26px; }}
            QComboBox QAbstractItemView {{
                background: #12121A;
                color: {C1};
                border: 1px solid rgba(255,255,255,0.10);
                selection-background-color: rgba(99,102,241,0.2);
                border-radius: 10px;
                padding: 4px;
            }}
            QPushButton {{
                background: transparent;
                color: {C2};
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 10px;
                padding: 9px 22px;
                font-size: 13px;
                font-weight: 500;
                min-height: 38px;
            }}
            QPushButton:hover {{
                border-color: rgba(99,102,241,0.4);
                color: {C1};
                background: rgba(99,102,241,0.06);
            }}
            QPushButton#ok {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {AC}, stop:1 {AC_L});
                color: white;
                border: none;
                font-weight: 600;
                min-width: 130px;
            }}
            QPushButton#ok:hover {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {AC_L}, stop:1 #A78BFA);
            }}
            QPushButton#danger {{
                color: {RED};
                border-color: rgba(239,68,68,0.25);
            }}
            QPushButton#danger:hover {{
                background: rgba(239,68,68,0.08);
                border-color: rgba(239,68,68,0.5);
            }}
        """)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        sb = QFrame()
        sb.setFixedWidth(220)
        sb.setStyleSheet(f"background:{BG_SB};border-right:1px solid rgba(255,255,255,0.06);")
        sbl = QVBoxLayout(sb)
        sbl.setContentsMargins(18, 28, 18, 20)
        sbl.setSpacing(2)

        logo = QLabel("\U0001f399  GoodVoice")
        logo.setFont(QFont(F, 18, QFont.Weight.Bold))
        logo.setStyleSheet(f"color:{C1};padding:0 4px 18px 4px;border:none;")
        sbl.addWidget(logo)

        self._nav = []
        for icon, name in [("\u2699\ufe0f", "\u041e\u0441\u043d\u043e\u0432\u043d\u044b\u0435"), ("\U0001f4ca", "\u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430"), ("\U0001f4dc", "\u0418\u0441\u0442\u043e\u0440\u0438\u044f")]:
            b = Nav(icon, name)
            b.clicked.connect(lambda checked, n=name: self._goto(n))
            sbl.addWidget(b)
            self._nav.append((name, b))
        sbl.addStretch()

        root.addWidget(sb)

        # Content
        ct = QFrame()
        ct.setStyleSheet("background:transparent;border:none;")
        ctl = QVBoxLayout(ct)
        ctl.setContentsMargins(36, 28, 36, 20)
        ctl.setSpacing(0)

        self._title = QLabel("\u041e\u0441\u043d\u043e\u0432\u043d\u044b\u0435")
        self._title.setFont(QFont(F, 22, QFont.Weight.Bold))
        self._title.setStyleSheet(f"color:{C1};border:none;")
        ctl.addWidget(self._title)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._pg_gen())
        self._stack.addWidget(self._pg_stat())
        self._stack.addWidget(self._pg_hist())
        ctl.addWidget(self._stack, 1)

        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet("background:rgba(255,255,255,0.06);border:none;margin:12px 0;")
        ctl.addWidget(line)

        fl = QHBoxLayout()
        fl.setContentsMargins(0, 0, 0, 0)
        fl.addStretch()
        bc = QPushButton("\u0417\u0430\u043a\u0440\u044b\u0442\u044c")
        bc.clicked.connect(self.close)
        fl.addWidget(bc)
        bs = QPushButton("\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c")
        bs.setObjectName("ok")
        bs.clicked.connect(self._save)
        fl.addWidget(bs)
        ctl.addLayout(fl)

        root.addWidget(ct, 1)
        self._goto("\u041e\u0441\u043d\u043e\u0432\u043d\u044b\u0435")

    def _goto(self, name):
        self._title.setText(name)
        idx = {"\u041e\u0441\u043d\u043e\u0432\u043d\u044b\u0435": 0, "\u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430": 1, "\u0418\u0441\u0442\u043e\u0440\u0438\u044f": 2}[name]
        self._stack.setCurrentIndex(idx)
        for n, b in self._nav:
            b.setChecked(n == name)

    def _pg_gen(self):
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        c = QWidget()
        lay = QVBoxLayout(c)
        lay.setContentsMargins(0, 0, 12, 0)
        lay.setSpacing(10)

        lm = {"auto": "Auto", "ru": "Russian", "en": "English",
              "de": "German", "fr": "French", "es": "Spanish"}

        defs = [
            ("\u0413\u043e\u0440\u044f\u0447\u0430\u044f \u043a\u043b\u0430\u0432\u0438\u0448\u0430", "\u041a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f \u0434\u043b\u044f \u043d\u0430\u0447\u0430\u043b\u0430 \u0437\u0430\u043f\u0438\u0441\u0438 \u0433\u043e\u043b\u043e\u0441\u0430",
             ["Right Alt", "Right Ctrl", "Left Ctrl"],
             "Right Alt" if self.settings.hotkey == "alt_r" else
             ("Right Ctrl" if self.settings.hotkey == "ctrl_r" else "Left Ctrl")),
            ("\u0420\u0435\u0436\u0438\u043c \u0437\u0430\u043f\u0438\u0441\u0438", "Hold \u2014 \u0437\u0430\u0436\u0430\u043b/\u043e\u0442\u043f\u0443\u0441\u0442\u0438\u043b. Toggle \u2014 \u043d\u0430\u0436\u0430\u043b/\u043d\u0430\u0436\u0430\u043b",
             ["\u0417\u0430\u0436\u0430\u0442\u0438\u0435 (Hold)", "\u041f\u0435\u0440\u0435\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0435 (Toggle)"],
             "\u0417\u0430\u0436\u0430\u0442\u0438\u0435 (Hold)" if self.settings.trigger_mode == "hold" else "\u041f\u0435\u0440\u0435\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0435 (Toggle)"),
            ("\u042f\u0437\u044b\u043a", "\u042f\u0437\u044b\u043a \u0440\u0430\u0441\u043f\u043e\u0437\u043d\u0430\u0432\u0430\u043d\u0438\u044f \u0440\u0435\u0447\u0438",
             ["Auto", "Russian", "English", "German", "French", "Spanish"],
             lm.get(self.settings.language, "Auto")),
            ("\u0422\u0435\u043c\u0430 HUD", "\u0412\u0438\u0437\u0443\u0430\u043b\u044c\u043d\u044b\u0439 \u0441\u0442\u0438\u043b\u044c \u043f\u043b\u0430\u0432\u0430\u044e\u0449\u0435\u0433\u043e \u043e\u043a\u043d\u0430",
             ["hybrid_v2", "google", "google_v2", "hybrid", "vercel"],
             self.settings.hud_theme),
        ]

        self._combos = []
        for title, desc, items, cur in defs:
            f = GlassCard()
            fl = QHBoxLayout(f)
            fl.setContentsMargins(22, 0, 22, 0)
            fl.setSpacing(16)
            col = QVBoxLayout()
            col.setSpacing(2)
            t = QLabel(title)
            t.setFont(QFont(F, 14, QFont.Weight.Medium))
            t.setStyleSheet(f"color:{C1};background:transparent;border:none;")
            col.addWidget(t)
            d = QLabel(desc)
            d.setFont(QFont(F, 11))
            d.setStyleSheet(f"color:{C3};background:transparent;border:none;")
            col.addWidget(d)
            fl.addLayout(col, 1)
            cb = cmb(items, cur)
            fl.addWidget(cb)
            self._combos.append(cb)
            lay.addWidget(f)

        # Toggle
        f = GlassCard()
        fl = QHBoxLayout(f)
        fl.setContentsMargins(22, 0, 22, 0)
        fl.setSpacing(16)
        col = QVBoxLayout()
        col.setSpacing(2)
        t = QLabel("\u041f\u0443\u043d\u043a\u0442\u0443\u0430\u0446\u0438\u044f")
        t.setFont(QFont(F, 14, QFont.Weight.Medium))
        t.setStyleSheet(f"color:{C1};background:transparent;border:none;")
        col.addWidget(t)
        d = QLabel("\u0410\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u0440\u0430\u0441\u0441\u0442\u0430\u0432\u043b\u044f\u0435\u0442 \u0437\u0430\u043f\u044f\u0442\u044b\u0435 \u0438 \u0442\u043e\u0447\u043a\u0438")
        d.setFont(QFont(F, 11))
        d.setStyleSheet(f"color:{C3};background:transparent;border:none;")
        col.addWidget(d)
        fl.addLayout(col, 1)
        self.tog = NeonToggle(self.settings.punctuation)
        fl.addWidget(self.tog)
        lay.addWidget(f)

        lay.addStretch()
        sa.setWidget(c)
        return sa

    def _pg_stat(self):
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        c = QWidget()
        lay = QVBoxLayout(c)
        lay.setContentsMargins(0, 0, 12, 0)
        lay.setSpacing(16)

        st = self.stats
        row = QHBoxLayout()
        row.setSpacing(12)
        for val, lbl in [
            (str(st.total_sessions), "\u0421\u0435\u0441\u0441\u0438\u0439"),
            (f"{st.total_words:,}", "\u0421\u043b\u043e\u0432"),
            (f"{st.total_chars:,}", "\u0421\u0438\u043c\u0432\u043e\u043b\u043e\u0432"),
            (f"{st.avg_words:.0f}", "\u0421\u043b\u043e\u0432 / \u0441\u0435\u0441\u0441\u0438\u044f"),
        ]:
            row.addWidget(NeonKPI(val, lbl))
        lay.addLayout(row)

        if st.sessions:
            f = GlassCard()
            f.setMinimumHeight(280)
            fl = QVBoxLayout(f)
            fl.setContentsMargins(22, 18, 22, 14)
            fl.setSpacing(8)
            t = QLabel("\u0410\u043a\u0442\u0438\u0432\u043d\u043e\u0441\u0442\u044c \u043f\u043e \u0434\u043d\u044f\u043c")
            t.setFont(QFont(F, 13, QFont.Weight.Medium))
            t.setStyleSheet(f"color:{C2};background:transparent;border:none;")
            fl.addWidget(t)

            daily = defaultdict(int)
            for s in st.sessions:
                day = datetime.fromtimestamp(s["timestamp"]).strftime("%d.%m")
                daily[day] += s.get("word_count", 0)

            today = datetime.now()
            days = []
            for i in range(13, -1, -1):
                d = today - timedelta(days=i)
                key = d.strftime("%d.%m")
                label = ["\u041f\u043d", "\u0412\u0442", "\u0421\u0440", "\u0427\u0442", "\u041f\u0442", "\u0421\u0431", "\u0412\u0441"][d.weekday()]
                days.append((label, daily.get(key, 0), d.strftime("%d %B")))

            chart = FluidChart(days)
            chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            fl.addWidget(chart, 1)
            lay.addWidget(f, 1)
        else:
            lbl = QLabel("\u041f\u043e\u043a\u0430 \u043d\u0435\u0442 \u0434\u0430\u043d\u043d\u044b\u0445")
            lbl.setFont(QFont(F, 13))
            lbl.setStyleSheet(f"color:{C3};padding:40px;border:none;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(lbl)

        lay.addStretch()
        sa.setWidget(c)
        return sa

    def _pg_hist(self):
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        c = QWidget()
        lay = QVBoxLayout(c)
        lay.setContentsMargins(0, 0, 12, 0)
        lay.setSpacing(6)

        entries = self.history.get_recent(30)
        if not entries:
            lbl = QLabel("\u0418\u0441\u0442\u043e\u0440\u0438\u044f \u043f\u0443\u0441\u0442\u0430")
            lbl.setFont(QFont(F, 13))
            lbl.setStyleSheet(f"color:{C3};padding:40px;border:none;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(lbl)
        else:
            for e in entries:
                row = HRow(e)
                lay.addWidget(row)
            lay.addSpacing(8)
            btn = QPushButton("\u041e\u0447\u0438\u0441\u0442\u0438\u0442\u044c \u0438\u0441\u0442\u043e\u0440\u0438\u044e")
            btn.setObjectName("danger")
            btn.clicked.connect(self._clr)
            lay.addWidget(btn)

        lay.addStretch()
        sa.setWidget(c)
        return sa

    def _clr(self):
        if QMessageBox.question(self, "\u041e\u0447\u0438\u0441\u0442\u043a\u0430", "\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u0432\u0441\u044e \u0438\u0441\u0442\u043e\u0440\u0438\u044e?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.history.clear()
            self._stack.removeWidget(self._stack.widget(2))
            self._stack.insertWidget(2, self._pg_hist())
            self._stack.setCurrentIndex(2)

    def _save(self):
        hm = {"Right Alt": "alt_r", "Right Ctrl": "ctrl_r", "Left Ctrl": "ctrl_l"}
        lm = {"Auto": "auto", "Russian": "ru", "English": "en",
              "German": "de", "French": "fr", "Spanish": "es"}
        self.settings.hotkey = hm.get(self._combos[0].currentText(), "alt_r")
        self.settings.trigger_mode = "hold" if self._combos[1].currentIndex() == 0 else "toggle"
        self.settings.language = lm.get(self._combos[2].currentText(), "auto")
        self.settings.hud_theme = self._combos[3].currentText()
        self.settings.punctuation = self.tog.isChecked()
        self.settings.save()
        self.close()


def open_settings():
    w = SettingsWindow()
    w.show()
    return w
