"""GoodVoice Settings — clean, professional, accessible UI."""

import sys
from datetime import datetime, timedelta
from collections import defaultdict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QMessageBox, QApplication, QFrame,
    QStackedWidget, QScrollArea, QSizePolicy, QToolTip
)
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QLinearGradient, QPen, QBrush,
    QRadialGradient, QPainterPath
)

from settings import Settings
from stats import Stats
from history import History


# ── Design Tokens ────────────────────────────────────────────────

BG       = "#0A0A0F"
BG_SB    = "#0E0E14"
BG_CARD  = "rgba(255,255,255,0.03)"
BD       = "rgba(255,255,255,0.07)"
BD_H     = "rgba(99,102,241,0.35)"
C1       = "#FFFFFF"
C2       = "#A0AEC0"
C3       = "#5A6577"
AC       = "#6366F1"
AC_L     = "#818CF8"
RED      = "#EF4444"
F        = "Segoe UI"
FM       = "Consolas"
R        = 12


# ── Helpers ──────────────────────────────────────────────────────

def card():
    f = QFrame()
    f.setStyleSheet(f"""
        QFrame {{
            background: {BG_CARD};
            border: 1px solid {BD};
            border-radius: {R}px;
        }}
    """)
    return f


def kpi(val, lbl):
    f = card()
    f.setFixedHeight(96)
    l = QVBoxLayout(f)
    l.setContentsMargins(20, 12, 20, 12)
    l.setSpacing(2)
    v = QLabel(val)
    v.setFont(QFont(FM, 26, QFont.Weight.Bold))
    v.setStyleSheet(f"color:{C1};background:transparent;border:none;")
    l.addWidget(v)
    t = QLabel(lbl)
    t.setFont(QFont(F, 12))
    t.setStyleSheet(f"color:{C2};background:transparent;border:none;")
    l.addWidget(t)
    return f


def combo(items, cur=None):
    c = QComboBox()
    c.addItems(items)
    if cur and cur in items:
        c.setCurrentText(cur)
    c.setFixedWidth(180)
    c.setFixedHeight(36)
    return c


# ── Neon Toggle ──────────────────────────────────────────────────

class Toggle(QWidget):
    def __init__(self, checked=False):
        super().__init__()
        self._on = checked
        self._pos = 1.0 if checked else 0.0
        self.setFixedSize(48, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def isChecked(self):
        return self._on

    def mousePressEvent(self, e):
        self._on = not self._on
        self.update()

    def paintEvent(self, e):
        target = 1.0 if self._on else 0.0
        self._pos += (target - self._pos) * 0.25
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Track
        track = QColor(AC) if self._on else QColor(35, 35, 48)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(track))
        p.drawRoundedRect(QRectF(0, 0, 48, 26), 13, 13)

        # Thumb
        x = 4 + self._pos * 20
        p.setBrush(QBrush(QColor(255, 255, 255)))
        p.drawEllipse(QPointF(x + 9, 13), 8, 8)

        p.end()
        if abs(self._pos - target) > 0.01:
            self.update()


# ── Sidebar Nav ──────────────────────────────────────────────────

class Nav(QPushButton):
    def __init__(self, icon, text):
        super().__init__(f"  {icon}  {text}")
        self.setFixedHeight(38)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {C3};
                border: none;
                border-left: 3px solid transparent;
                border-radius: 0 8px 8px 0;
                padding: 0 14px;
                text-align: left;
                font-size: 13px;
                font-family: {F};
            }}
            QPushButton:hover {{
                background: rgba(99,102,241,0.06);
                color: {C2};
            }}
            QPushButton:checked {{
                background: rgba(99,102,241,0.10);
                color: {C1};
                font-weight: 600;
                border-left: 3px solid {AC};
            }}
        """)


# ── Chart ────────────────────────────────────────────────────────

class Chart(QWidget):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._hover = -1
        self.setMouseTracking(True)

    def mouseMoveEvent(self, e):
        idx = self._hit(e.pos())
        if idx != self._hover:
            self._hover = idx
            self.update()
            if 0 <= idx < len(self.data):
                lbl, val, dt = self.data[idx]
                QToolTip.showText(e.globalPos(), f"{dt}: {val} слов", self)
            else:
                QToolTip.hideText()

    def leaveEvent(self, e):
        self._hover = -1
        self.update()
        QToolTip.hideText()

    def _hit(self, pos):
        w = self.width()
        n = len(self.data)
        bw = max(14, min(20, (w - 40 - (n - 1) * 5) // n))
        gap = 5
        total = n * bw + (n - 1) * gap
        sx = 20 + (w - 40 - total) // 2
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
        mt, mb = 12, 28
        ch = h - mt - mb
        mx = max(v for _, v, _ in self.data) or 1

        # Grid
        p.setPen(QPen(QColor(255, 255, 255, 6), 1, Qt.PenStyle.DotLine))
        for i in range(1, 4):
            gy = mt + int(ch * i / 4)
            p.drawLine(20, gy, w - 20, gy)

        n = len(self.data)
        bw = max(14, min(20, (w - 40 - (n - 1) * 5) // n))
        gap = 5
        total = n * bw + (n - 1) * gap
        sx = 20 + (w - 40 - total) // 2

        for i, (lbl, val, _) in enumerate(self.data):
            x = sx + i * (bw + gap)
            hv = (i == self._hover)

            if val == 0:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(QColor(255, 255, 255, 8)))
                p.drawRoundedRect(x, mt + ch - 3, bw, 3, 1, 1)
            else:
                bh = max(6, int((val / mx) * ch))
                y = mt + ch - bh
                g = QLinearGradient(x, y, x, y + bh)
                g.setColorAt(0, QColor(AC_L if hv else AC))
                g.setColorAt(1, QColor("#4F46E5"))
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(g))
                p.drawRoundedRect(x, y, bw, bh, 3, 3)

            p.setPen(QColor(C3))
            p.setFont(QFont(F, 9))
            p.drawText(x, h - 18, bw, 16, Qt.AlignmentFlag.AlignCenter, lbl)

        p.end()


# ── History Row ──────────────────────────────────────────────────

class Row(QWidget):
    def __init__(self, entry):
        super().__init__()
        self._text = entry["text"]
        self._ts = entry["timestamp"]
        self._words = entry.get("word_count", len(self._text.split()))
        self._glow = 0.0
        self._tgt = 0.0
        self.setFixedHeight(52)
        self.setMouseTracking(True)

    def enterEvent(self, e):
        self._tgt = 1.0
        self.update()

    def leaveEvent(self, e):
        self._tgt = 0.0
        self.update()

    def mousePressEvent(self, e):
        QApplication.clipboard().setText(self._text)

    def paintEvent(self, e):
        self._glow += (self._tgt - self._glow) * 0.2
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # BG
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), 10, 10)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(255, 255, 255, int(2 + self._glow * 6))))
        p.drawPath(path)

        # Border
        ba = int(16 + self._glow * 25)
        bc = QColor(99, 102, 241, ba) if self._glow > 0.01 else QColor(255, 255, 255, 14)
        p.setPen(QPen(bc, 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

        # Time
        ts = datetime.fromtimestamp(self._ts).strftime("%H:%M")
        p.setPen(QColor(C3))
        p.setFont(QFont(FM, 10))
        p.drawRoundedRect(QRectF(14, 13, 50, 26), 7, 7)
        p.setPen(QColor("#A0A0C0"))
        p.drawText(QRectF(14, 13, 50, 26), Qt.AlignmentFlag.AlignCenter, ts)

        # Text
        txt = self._text[:80] + ("..." if len(self._text) > 80 else "")
        p.setPen(QColor(C2))
        p.setFont(QFont(F, 13))
        p.drawText(QRectF(74, 10, w - 180, 32),
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, txt)

        # Chip
        chip = f"{self._words} слов"
        cr = QRectF(w - 110, 14, 72, 24)
        p.setPen(QPen(QColor(99, 102, 241, 50), 1))
        p.setBrush(QBrush(QColor(99, 102, 241, 12)))
        p.drawRoundedRect(cr, 10, 10)
        p.setPen(QColor(AC))
        p.setFont(QFont(F, 9))
        p.drawText(cr, Qt.AlignmentFlag.AlignCenter, chip)

        p.end()
        if abs(self._glow - self._tgt) > 0.005:
            self.update()


# ── Window ───────────────────────────────────────────────────────

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
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background:none; }}
            QComboBox {{
                background: rgba(255,255,255,0.04);
                color: {C1};
                border: 1px solid {BD};
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 13px;
            }}
            QComboBox:hover {{ border-color: {BD_H}; }}
            QComboBox::drop-down {{ border:none; width:24px; }}
            QComboBox QAbstractItemView {{
                background: #12121A;
                color: {C1};
                border: 1px solid {BD};
                selection-background-color: rgba(99,102,241,0.2);
                border-radius: 8px;
                padding: 2px;
            }}
            QPushButton {{
                background: transparent;
                color: {C2};
                border: 1px solid {BD};
                border-radius: 8px;
                padding: 8px 18px;
                font-size: 13px;
                font-weight: 500;
                min-height: 36px;
            }}
            QPushButton:hover {{ border-color: {BD_H}; color: {C1}; }}
            QPushButton#ok {{
                background: {AC};
                color: white;
                border: none;
                font-weight: 600;
                min-width: 120px;
            }}
            QPushButton#ok:hover {{ background: {AC_L}; }}
            QPushButton#danger {{ color:{RED}; border-color:rgba(239,68,68,0.25); }}
            QPushButton#danger:hover {{ background:rgba(239,68,68,0.08); border-color:rgba(239,68,68,0.5); }}
        """)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        sb = QFrame()
        sb.setFixedWidth(220)
        sb.setStyleSheet(f"background:{BG_SB};border-right:1px solid rgba(255,255,255,0.05);")
        sbl = QVBoxLayout(sb)
        sbl.setContentsMargins(16, 24, 16, 20)
        sbl.setSpacing(2)

        logo = QLabel("GoodVoice")
        logo.setFont(QFont(F, 18, QFont.Weight.Bold))
        logo.setStyleSheet(f"color:{C1};padding:0 4px 16px 4px;border:none;")
        sbl.addWidget(logo)

        self._nav = []
        for icon, name in [("\u2699", "\u041e\u0441\u043d\u043e\u0432\u043d\u044b\u0435"), ("\u25c6", "\u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430"), ("\u25a0", "\u0418\u0441\u0442\u043e\u0440\u0438\u044f")]:
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
        ctl.setContentsMargins(32, 24, 32, 16)
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
        line.setStyleSheet("background:rgba(255,255,255,0.05);border:none;margin:10px 0;")
        ctl.addWidget(line)

        fl = QHBoxLayout()
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
        self._stack.setCurrentIndex(
            {"\u041e\u0441\u043d\u043e\u0432\u043d\u044b\u0435": 0,
             "\u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430": 1,
             "\u0418\u0441\u0442\u043e\u0440\u0438\u044f": 2}[name])
        for n, b in self._nav:
            b.setChecked(n == name)

    def _pg_gen(self):
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        c = QWidget()
        lay = QVBoxLayout(c)
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(10)

        lm = {"auto": "Auto", "ru": "Russian", "en": "English",
              "de": "German", "fr": "French", "es": "Spanish"}

        defs = [
            ("\u0413\u043e\u0440\u044f\u0447\u0430\u044f \u043a\u043b\u0430\u0432\u0438\u0448\u0430",
             "\u041a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f \u0434\u043b\u044f \u0437\u0430\u043f\u0438\u0441\u0438 \u0433\u043e\u043b\u043e\u0441\u0430",
             ["Right Alt", "Right Ctrl", "Left Ctrl"],
             "Right Alt" if self.settings.hotkey == "alt_r" else
             ("Right Ctrl" if self.settings.hotkey == "ctrl_r" else "Left Ctrl")),
            ("\u0420\u0435\u0436\u0438\u043c \u0437\u0430\u043f\u0438\u0441\u0438",
             "Hold \u2014 \u0437\u0430\u0436\u0430\u043b/\u043e\u0442\u043f\u0443\u0441\u0442\u0438\u043b. Toggle \u2014 \u043d\u0430\u0436\u0430\u043b/\u043d\u0430\u0436\u0430\u043b",
             ["\u0417\u0430\u0436\u0430\u0442\u0438\u0435 (Hold)", "\u041f\u0435\u0440\u0435\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0435 (Toggle)"],
             "\u0417\u0430\u0436\u0430\u0442\u0438\u0435 (Hold)" if self.settings.trigger_mode == "hold" else "\u041f\u0435\u0440\u0435\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0435 (Toggle)"),
            ("\u042f\u0437\u044b\u043a", "\u042f\u0437\u044b\u043a \u0440\u0430\u0441\u043f\u043e\u0437\u043d\u0430\u0432\u0430\u043d\u0438\u044f \u0440\u0435\u0447\u0438",
             ["Auto", "Russian", "English", "German", "French", "Spanish"],
             lm.get(self.settings.language, "Auto")),
            ("\u0422\u0435\u043c\u0430 HUD",
             "\u0412\u0438\u0437\u0443\u0430\u043b\u044c\u043d\u044b\u0439 \u0441\u0442\u0438\u043b\u044c \u043f\u043b\u0430\u0432\u0430\u044e\u0449\u0435\u0433\u043e \u043e\u043a\u043d\u0430",
             ["hybrid_v2", "google", "google_v2", "hybrid", "vercel"],
             self.settings.hud_theme),
        ]

        self._c = []
        for title, desc, items, cur in defs:
            f = card()
            fl = QHBoxLayout(f)
            fl.setContentsMargins(20, 0, 20, 0)
            fl.setSpacing(12)
            col = QVBoxLayout()
            col.setSpacing(1)
            t = QLabel(title)
            t.setFont(QFont(F, 14, QFont.Weight.Medium))
            t.setStyleSheet(f"color:{C1};background:transparent;border:none;")
            col.addWidget(t)
            d = QLabel(desc)
            d.setFont(QFont(F, 11))
            d.setStyleSheet(f"color:{C3};background:transparent;border:none;")
            col.addWidget(d)
            fl.addLayout(col, 1)
            cb = combo(items, cur)
            fl.addWidget(cb)
            self._c.append(cb)
            lay.addWidget(f)

        # Toggle
        f = card()
        fl = QHBoxLayout(f)
        fl.setContentsMargins(20, 0, 20, 0)
        fl.setSpacing(12)
        col = QVBoxLayout()
        col.setSpacing(1)
        t = QLabel("\u041f\u0443\u043d\u043a\u0442\u0443\u0430\u0446\u0438\u044f")
        t.setFont(QFont(F, 14, QFont.Weight.Medium))
        t.setStyleSheet(f"color:{C1};background:transparent;border:none;")
        col.addWidget(t)
        d = QLabel("\u0410\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u0440\u0430\u0441\u0441\u0442\u0430\u0432\u043b\u044f\u0435\u0442 \u0437\u0430\u043f\u044f\u0442\u044b\u0435 \u0438 \u0442\u043e\u0447\u043a\u0438")
        d.setFont(QFont(F, 11))
        d.setStyleSheet(f"color:{C3};background:transparent;border:none;")
        col.addWidget(d)
        fl.addLayout(col, 1)
        self.tog = Toggle(self.settings.punctuation)
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
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(12)

        st = self.stats
        row = QHBoxLayout()
        row.setSpacing(10)
        for val, lbl in [
            (str(st.total_sessions), "\u0421\u0435\u0441\u0441\u0438\u0439"),
            (f"{st.total_words:,}", "\u0421\u043b\u043e\u0432"),
            (f"{st.total_chars:,}", "\u0421\u0438\u043c\u0432\u043e\u043b\u043e\u0432"),
            (f"{st.avg_words:.0f}", "\u0421\u043b\u043e\u0432/\u0441\u0435\u0441\u0441\u0438\u044f"),
        ]:
            row.addWidget(kpi(val, lbl))
        lay.addLayout(row)

        if st.sessions:
            f = card()
            f.setMinimumHeight(240)
            fl = QVBoxLayout(f)
            fl.setContentsMargins(20, 14, 20, 10)
            fl.setSpacing(4)
            t = QLabel("\u0410\u043a\u0442\u0438\u0432\u043d\u043e\u0441\u0442\u044c \u043f\u043e \u0434\u043d\u044f\u043c")
            t.setFont(QFont(F, 12, QFont.Weight.Medium))
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
                lbl = ["\u041f\u043d", "\u0412\u0442", "\u0421\u0440", "\u0427\u0442", "\u041f\u0442", "\u0421\u0431", "\u0412\u0441"][d.weekday()]
                days.append((lbl, daily.get(key, 0), d.strftime("%d %B")))

            chart = Chart(days)
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
        lay.setContentsMargins(0, 0, 8, 0)
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
                lay.addWidget(Row(e))
            lay.addSpacing(8)
            btn = QPushButton("\u041e\u0447\u0438\u0441\u0442\u0438\u0442\u044c \u0438\u0441\u0442\u043e\u0440\u0438\u044e")
            btn.setObjectName("danger")
            btn.clicked.connect(self._clr)
            lay.addWidget(btn)

        lay.addStretch()
        sa.setWidget(c)
        return sa

    def _clr(self):
        if QMessageBox.question(self, "\u041e\u0447\u0438\u0441\u0442\u043a\u0430",
                "\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u0432\u0441\u044e \u0438\u0441\u0442\u043e\u0440\u0438\u044e?",
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
        self.settings.hotkey = hm.get(self._c[0].currentText(), "alt_r")
        self.settings.trigger_mode = "hold" if self._c[1].currentIndex() == 0 else "toggle"
        self.settings.language = lm.get(self._c[2].currentText(), "auto")
        self.settings.hud_theme = self._c[3].currentText()
        self.settings.punctuation = self.tog.isChecked()
        self.settings.save()
        self.close()


def open_settings():
    w = SettingsWindow()
    w.show()
    return w
