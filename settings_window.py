"""GoodVoice Settings — Minimalism clean UI."""

import sys
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QMessageBox, QApplication, QFrame,
    QStackedWidget, QScrollArea, QSizePolicy, QToolTip
)
from PyQt6.QtCore import Qt, QRectF, QPointF, QSize, QTimer
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QLinearGradient, QPen, QBrush,
    QRadialGradient, QPainterPath, QPixmap, QIcon
)

from settings import Settings
from stats import Stats
from history import History

# ── Tokens ───────────────────────────────────────────────────────

BG    = "#000000"
BG2   = "#0A0A0A"
CARD  = "#111111"
BDR   = "rgba(255,255,255,0.06)"
T1    = "#FFFFFF"
T2    = "#666666"
T3    = "#999999"
AC    = "#0066FF"
AC_H  = "#0052CC"
FN    = "Segoe UI"


# ── Card ─────────────────────────────────────────────────────────

class Card(QWidget):
    def __init__(self):
        super().__init__()
        self._g = 0.0
        self._t = 0.0
        self.setMouseTracking(True)
        self.setMinimumHeight(72)

    def enterEvent(self, e): self._t = 1.0
    def leaveEvent(self, e): self._t = 0.0

    def paintEvent(self, e):
        self._g += (self._t - self._g) * 0.15
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(CARD)))
        p.drawRect(0, 0, w, h)
        if self._g > 0.01:
            c = QColor(AC); c.setAlpha(int(15 + self._g * 30))
            p.setPen(QPen(c, 1))
        else:
            p.setPen(QPen(QColor(BDR), 1))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRect(0, 0, w, h)
        p.end()
        if abs(self._g - self._t) > 0.005: self.update()


# ── Switch ───────────────────────────────────────────────────────

class Switch(QWidget):
    def __init__(self, on=False):
        super().__init__()
        self._on = on
        self._p = 1.0 if on else 0.0
        self.setFixedSize(60, 32)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def isChecked(self): return self._on
    def mousePressEvent(self, e): self._on = not self._on; self._start()
    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Space):
            self._on = not self._on; self._start()

    def _start(self):
        self._anim = QTimer()
        self._anim.timeout.connect(self._tick)
        self._anim.setInterval(16)
        self._anim.start()

    def _tick(self):
        tgt = 1.0 if self._on else 0.0
        self._p += (tgt - self._p) * 0.15
        self.update()
        if abs(self._p - tgt) < 0.01:
            self._p = tgt
            if hasattr(self, '_anim') and self._anim: self._anim.stop()
            self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self._on:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(AC)))
            p.drawRect(0, 0, 60, 32)
        else:
            p.setPen(QPen(QColor(T2), 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(0, 0, 60, 32)
        x = 4 + self._p * 28
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(T1)))
        p.drawRect(int(x), 4, 24, 24)
        p.end()


# ── Combo ────────────────────────────────────────────────────────

def combo(items, cur=None):
    c = QComboBox()
    c.addItems(items)
    if cur and cur in items: c.setCurrentText(cur)
    c.setFixedWidth(180)
    c.setFixedHeight(36)
    c.setCursor(Qt.CursorShape.PointingHandCursor)
    fn = QFont(FN, 11)
    c.setFont(fn)
    c.view().setFont(fn)
    c.setStyleSheet(f"""
        QComboBox {{
            background: {CARD}; color: {T1};
            border: 1px solid {BDR}; border-radius: 0px;
            padding: 6px 12px; font-size: 13px; font-family: {FN};
        }}
        QComboBox:hover {{ border-color: rgba(0,102,255,0.3); }}
        QComboBox:focus {{ border-color: {AC}; }}
        QComboBox::drop-down {{ border: none; width: 24px; }}
        QComboBox QAbstractItemView {{
            background: #0D0D0D; color: {T1};
            border: 1px solid rgba(0,102,255,0.2);
            selection-background-color: rgba(0,102,255,0.12);
            outline: none; padding: 2px; font-size: 13px; font-family: {FN};
        }}
        QComboBox QAbstractItemView::item {{
            padding: 8px 14px; min-height: 32px;
            border-bottom: 1px solid rgba(255,255,255,0.04);
        }}
        QComboBox QAbstractItemView::item:last {{ border-bottom: none; }}
        QComboBox QAbstractItemView::item:hover {{ background: rgba(0,102,255,0.08); }}
        QComboBox QAbstractItemView::item:selected {{ background: rgba(0,102,255,0.12); color: {T1}; }}
    """)
    return c


# ── Nav ──────────────────────────────────────────────────────────

class Nav(QPushButton):
    def __init__(self, icon_name, text):
        super().__init__()
        self.setFixedHeight(44)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # Load icon
        icon_path = Path(__file__).parent / "assets" / "icons" / f"{icon_name}.svg"
        if icon_path.exists():
            pixmap = QPixmap(str(icon_path))
            tinted = QPixmap(pixmap.size())
            tinted.fill(QColor(0, 0, 0, 0))
            painter = QPainter(tinted)
            painter.drawPixmap(0, 0, pixmap)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(tinted.rect(), QColor(255, 255, 255))
            painter.end()
            self.setIcon(QIcon(tinted))
            self.setIconSize(QSize(18, 18))
        self.setText(f"  {text}")
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {T3};
                border: none; border-left: 2px solid transparent;
                padding: 0 16px; text-align: left;
                font-size: 13px; font-family: {FN}; letter-spacing: 0.5px;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.03); color: {T2}; }}
            QPushButton:checked {{
                background: rgba(0,102,255,0.08); color: {T1};
                font-weight: 500; border-left: 2px solid {AC};
            }}
        """)


# ── Chart ────────────────────────────────────────────────────────

class Chart(QWidget):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._h = -1
        self.setMouseTracking(True)

    def mouseMoveEvent(self, e):
        i = self._hit(e.pos())
        if i != self._h:
            self._h = i
            self.update()
            if 0 <= i < len(self.data):
                l, v, d = self.data[i]
                QToolTip.showText(e.globalPosition().toPoint(), f"{d}: {v} \u0441\u043b\u043e\u0432", self)
            else: QToolTip.hideText()

    def leaveEvent(self, e): self._h = -1; self.update(); QToolTip.hideText()

    def _hit(self, pos):
        w = self.width()
        n = len(self.data)
        bw = max(12, min(20, (w - 32 - (n - 1) * 8) // n))
        total = n * bw + (n - 1) * 8
        sx = 16 + (w - 32 - total) // 2
        for i in range(n):
            x = sx + i * (bw + 8)
            if x <= pos.x() <= x + bw: return i
        return -1

    def paintEvent(self, e):
        if not self.data: return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        mt, mb = 16, 32
        ch = h - mt - mb
        mx = max(v for _, v, _ in self.data) or 1
        p.setPen(QPen(QColor(255, 255, 255, 4), 1, Qt.PenStyle.DotLine))
        for i in range(1, 4):
            p.drawLine(16, mt + int(ch * i / 4), w - 16, mt + int(ch * i / 4))
        n = len(self.data)
        bw = max(12, min(20, (w - 32 - (n - 1) * 8) // n))
        total = n * bw + (n - 1) * 8
        sx = 16 + (w - 32 - total) // 2
        for i, (lbl, val, _) in enumerate(self.data):
            x = sx + i * (bw + 8)
            if val == 0:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(QColor(255, 255, 255, 6)))
                p.drawRect(x, mt + ch - 3, bw, 3)
            else:
                bh = max(4, int((val / mx) * ch))
                y = mt + ch - bh
                c = QColor(AC) if i == self._h else QColor(T1)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(c))
                p.drawRect(x, y, bw, bh)
            p.setPen(QColor(T3))
            p.setFont(QFont("Consolas", 9))
            p.drawText(x, h - 20, bw, 16, Qt.AlignmentFlag.AlignCenter, lbl)
        p.end()


# ── History row ──────────────────────────────────────────────────

class Row(QFrame):
    def __init__(self, entry):
        super().__init__()
        self._text = entry["text"]
        self.setFixedHeight(56)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"QFrame {{ background: {CARD}; border: 1px solid {BDR}; }} QFrame:hover {{ border-color: rgba(0,102,255,0.3); }}")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)
        ts = datetime.fromtimestamp(entry["timestamp"]).strftime("%H:%M")
        tl = QLabel(ts)
        tl.setFont(QFont("Consolas", 10))
        tl.setStyleSheet(f"color:{T3};background:transparent;border:none;")
        tl.setFixedWidth(52)
        layout.addWidget(tl)
        txt = self._text[:80] + ("..." if len(self._text) > 80 else "")
        ml = QLabel(txt)
        ml.setFont(QFont(FN, 13))
        ml.setStyleSheet(f"color:{T2};background:transparent;border:none;")
        ml.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(ml, 1)
        wc = entry.get("word_count", len(self._text.split()))
        chip = QLabel(f"{wc} \u0441\u043b\u043e\u0432")
        chip.setFont(QFont("Consolas", 10))
        chip.setStyleSheet(f"color:{AC};background:rgba(0,102,255,8);border:1px solid rgba(0,102,255,40);padding:4px 10px;")
        chip.setFixedWidth(76)
        chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(chip)
    def mousePressEvent(self, e): QApplication.clipboard().setText(self._text)


# ── KPI ──────────────────────────────────────────────────────────

class KPI(QWidget):
    def __init__(self, val, lbl):
        super().__init__()
        self._val = val; self._lbl = lbl; self.setFixedHeight(104)
    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.setPen(Qt.PenStyle.NoPen); p.setBrush(QBrush(QColor(CARD))); p.drawRect(0,0,w,h)
        p.setPen(QPen(QColor(BDR),1)); p.setBrush(Qt.BrushStyle.NoBrush); p.drawRect(0,0,w,h)
        p.setPen(QColor(T1)); p.setFont(QFont("Consolas",28,QFont.Weight.Bold))
        p.drawText(QRectF(20,14,w-40,44), Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter, self._val)
        p.setPen(QColor(T3)); p.setFont(QFont("Consolas",10))
        p.drawText(QRectF(20,60,w-40,28), Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop, self._lbl)
        p.end()


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
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet(f"""
            QWidget {{ background: {BG}; color: {T1}; font-family: {FN}; }}
            QScrollArea {{ border:none; background:transparent; }}
            QScrollBar:vertical {{ background:transparent; width:4px; margin:0 8px 0 0; }}
            QScrollBar::handle:vertical {{ background:rgba(255,255,255,0.06); min-height:24px; }}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical {{ height:0; }}
            QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical {{ background:none; }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Custom Title Bar ──────────────────────────────────────
        tb = QFrame()
        tb.setFixedHeight(36)
        tb.setStyleSheet(f"background:{BG2};border-bottom:1px solid {BDR};")
        tb_lay = QHBoxLayout(tb)
        tb_lay.setContentsMargins(0, 0, 0, 0)
        tb_lay.setSpacing(0)

        # Spacer (draggable area)
        spacer = QLabel()
        spacer.setStyleSheet("background:transparent;")
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb_lay.addWidget(spacer)

        # Window buttons
        def _load_tb_icon(name):
            p = Path(__file__).parent / "assets" / "icons" / f"{name}.svg"
            if not p.exists(): return QIcon()
            px = QPixmap(str(p))
            tinted = QPixmap(px.size())
            tinted.fill(QColor(0, 0, 0, 0))
            painter = QPainter(tinted)
            painter.drawPixmap(0, 0, px)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(tinted.rect(), QColor(T3))
            painter.end()
            return QIcon(tinted)

        self._tb_icons = {}
        for icon_name, slot in [("minimize", self.showMinimized), ("maximize", self._toggle_max), ("close", self.close)]:
            b = QPushButton()
            b.setIcon(_load_tb_icon(icon_name))
            b.setIconSize(QSize(16, 16))
            b.setFixedSize(46, 36)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            if icon_name == "close":
                b.setStyleSheet(f"QPushButton{{background:transparent;border:none;}} QPushButton:hover{{background:rgba(220,38,38,0.8);}}")
            else:
                b.setStyleSheet(f"QPushButton{{background:transparent;border:none;}} QPushButton:hover{{background:rgba(255,255,255,0.06);}}")
            b.clicked.connect(slot)
            if icon_name in ("maximize", "restore"):
                self._tb_max_btn = b
                self._tb_icons["maximize"] = _load_tb_icon("maximize")
                self._tb_icons["restore"] = _load_tb_icon("restore")
            tb_lay.addWidget(b)

        root.addWidget(tb)

        # ── Main content row ──────────────────────────────────────
        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(0)

        # Sidebar
        sb = QFrame()
        sb.setFixedWidth(224)
        sb.setStyleSheet(f"background:{BG2};border-right:1px solid {BDR};")
        sbl = QVBoxLayout(sb)
        sbl.setContentsMargins(0, 24, 0, 24)
        sbl.setSpacing(4)

        # Logo
        lr = QHBoxLayout()
        lr.setContentsMargins(0,0,0,16); lr.setSpacing(0)
        lr.addStretch()
        li = QLabel()
        li.setFixedSize(90, 90)
        li.setStyleSheet("background:transparent;border:none;")
        ip = Path(__file__).parent / "assets" / "Applogo.png"
        if ip.exists():
            px = QPixmap(str(ip)).scaled(QSize(90,90), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            li.setPixmap(px)
            li.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lr.addWidget(li)
        spacer2 = QLabel()
        spacer2.setFixedWidth(4)
        spacer2.setStyleSheet("background:transparent;border:none;")
        lr.addWidget(spacer2)
        lt = QLabel("GoodVoice")
        lt.setFont(QFont(FN, 15, QFont.Weight.DemiBold))
        lt.setStyleSheet(f"color:{T1};background:transparent;border:none;")
        lr.addWidget(lt)
        lr.addStretch()
        sbl.addLayout(lr)

        self._nav = []
        for ic, nm in [("settings","\u041e\u0441\u043d\u043e\u0432\u043d\u044b\u0435"),("chart-bar","\u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430"),("history","\u0418\u0441\u0442\u043e\u0440\u0438\u044f")]:
            b = Nav(ic, nm)
            b.clicked.connect(lambda checked, n=nm: self._goto(n))
            sbl.addWidget(b); self._nav.append((nm, b))
        sbl.addStretch()
        content_row.addWidget(sb)

        # Content
        ct = QFrame(); ct.setStyleSheet("background:transparent;border:none;")
        ctl = QVBoxLayout(ct)
        ctl.setContentsMargins(32, 24, 32, 16); ctl.setSpacing(0)

        self._title = QLabel("\u041e\u0441\u043d\u043e\u0432\u043d\u044b\u0435")
        self._title.setFont(QFont(FN, 24, QFont.Weight.Bold))
        self._title.setStyleSheet(f"color:{T1};border:none;")
        ctl.addWidget(self._title)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._pg_gen())
        self._stack.addWidget(self._pg_stat())
        self._stack.addWidget(self._pg_hist())
        ctl.addWidget(self._stack, 1)

        QFrame().setFixedHeight(1)
        line = QFrame(); line.setFixedHeight(1)
        line.setStyleSheet(f"background:{BDR};border:none;margin:12px 0;")
        ctl.addWidget(line)

        # Footer
        fl = QHBoxLayout()
        fl.setContentsMargins(0, 8, 0, 0)
        fl.addStretch()
        bc = QPushButton("\u0417\u0430\u043a\u0440\u044b\u0442\u044c")
        bc.setFixedHeight(40); bc.setFixedWidth(120)
        bc.setStyleSheet(f"QPushButton{{background:transparent;color:{T2};border:1px solid {BDR};border-radius:0px;padding:10px;font-size:14px;font-weight:500;letter-spacing:1px;}} QPushButton:hover{{border-color:rgba(0,102,255,0.3);color:{T1};}}")
        bc.clicked.connect(self.close)
        fl.addWidget(bc)
        fl.addSpacing(12)
        bs = QPushButton("\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c")
        bs.setFixedHeight(40); bs.setFixedWidth(140)
        bs.setStyleSheet(f"QPushButton{{background:{AC};color:#FFFFFF;border:2px solid {AC};border-radius:0px;font-weight:600;font-size:14px;letter-spacing:1px;padding:10px;}} QPushButton:hover{{background:{AC_H};border-color:{AC_H};}}")
        bs.clicked.connect(self._save)
        fl.addWidget(bs)
        ctl.addLayout(fl)

        content_row.addWidget(ct, 1)
        root.addLayout(content_row, 1)
        self._goto("\u041e\u0441\u043d\u043e\u0432\u043d\u044b\u0435")

    def _toggle_max(self):
        if self.isMaximized():
            self.showNormal()
            if hasattr(self, '_tb_max_btn') and hasattr(self, '_tb_icons'):
                self._tb_max_btn.setIcon(self._tb_icons["maximize"])
        else:
            self.showMaximized()
            if hasattr(self, '_tb_max_btn') and hasattr(self, '_tb_icons'):
                self._tb_max_btn.setIcon(self._tb_icons["restore"])

    def _goto(self, name):
        self._title.setText(name)
        self._stack.setCurrentIndex({"\u041e\u0441\u043d\u043e\u0432\u043d\u044b\u0435":0,"\u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430":1,"\u0418\u0441\u0442\u043e\u0440\u0438\u044f":2}[name])
        for n,b in self._nav: b.setChecked(n==name)

    def _pg_gen(self):
        sa = QScrollArea(); sa.setWidgetResizable(True)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        c = QWidget(); lay = QVBoxLayout(c)
        lay.setContentsMargins(0,0,8,0); lay.setSpacing(8)
        lm = {"auto":"Auto","ru":"Russian","en":"English","de":"German","fr":"French","es":"Spanish"}
        mm = {"tiny":"tiny","base":"base","small":"small","medium":"medium","large-v2":"large-v2","large-v3":"large-v3","turbo":"turbo"}
        defs = [
            ("\u0413\u043e\u0440\u044f\u0447\u0430\u044f \u043a\u043b\u0430\u0432\u0438\u0448\u0430","\u041a\u043e\u043c\u0431\u0438\u043d\u0430\u0446\u0438\u044f \u0434\u043b\u044f \u0437\u0430\u043f\u0438\u0441\u0438 \u0433\u043e\u043b\u043e\u0441\u0430",["Right Alt","Right Ctrl","Left Ctrl"],"Right Alt" if self.settings.hotkey=="alt_r" else ("Right Ctrl" if self.settings.hotkey=="ctrl_r" else "Left Ctrl")),
            ("\u0420\u0435\u0436\u0438\u043c \u0437\u0430\u043f\u0438\u0441\u0438","Hold \u2014 \u0437\u0430\u0436\u0430\u043b/\u043e\u0442\u043f\u0443\u0441\u0442\u0438\u043b. Toggle \u2014 \u043d\u0430\u0436\u0430\u043b/\u043d\u0430\u0436\u0430\u043b",["\u0417\u0430\u0436\u0430\u0442\u0438\u0435 (Hold)","\u041f\u0435\u0440\u0435\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0435 (Toggle)"],"\u0417\u0430\u0436\u0430\u0442\u0438\u0435 (Hold)" if self.settings.trigger_mode=="hold" else "\u041f\u0435\u0440\u0435\u043a\u043b\u044e\u0447\u0435\u043d\u0438\u0435 (Toggle)"),
            ("\u042f\u0437\u044b\u043a","\u042f\u0437\u044b\u043a \u0440\u0430\u0441\u043f\u043e\u0437\u043d\u0430\u0432\u0430\u043d\u0438\u044f \u0440\u0435\u0447\u0438",["Auto","Russian","English","German","French","Spanish"],lm.get(self.settings.language,"Auto")),
            ("\u0422\u0435\u043c\u0430 HUD","\u0412\u0438\u0437\u0443\u0430\u043b\u044c\u043d\u044b\u0439 \u0441\u0442\u0438\u043b\u044c \u043f\u043b\u0430\u0432\u0430\u044e\u0449\u0435\u0433\u043e \u043e\u043a\u043d\u0430",["hybrid_v2","google","google_v2","hybrid","vercel"],self.settings.hud_theme),
            ("\u041c\u043e\u0434\u0435\u043b\u044c Whisper","\u0420\u0430\u0437\u043c\u0435\u0440 \u043c\u043e\u0434\u0435\u043b\u0438 \u0434\u043b\u044f \u0440\u0430\u0441\u043f\u043e\u0437\u043d\u0430\u0432\u0430\u043d\u0438\u044f \u0440\u0435\u0447\u0438 (\u0442\u043e\u0447\u043d\u0435\u0435 \u2014 \u043c\u0435\u0434\u043b\u0435\u0435)",["tiny","base","small","medium","large-v2","large-v3","turbo"],mm.get(self.settings.model_size,"medium")),
        ]
        self._c = []
        for title,desc,items,cur in defs:
            f = Card(); fl = QHBoxLayout(f)
            fl.setContentsMargins(20,0,20,0); fl.setSpacing(16)
            col = QVBoxLayout(); col.setSpacing(2); col.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            t = QLabel(title); t.setFont(QFont(FN,14,QFont.Weight.Normal))
            t.setStyleSheet(f"color:{T1};background:transparent;border:none;"); col.addWidget(t)
            d = QLabel(desc); d.setFont(QFont(FN,12))
            d.setStyleSheet(f"color:{T3};background:transparent;border:none;"); col.addWidget(d)
            fl.addLayout(col, 1)
            cb = combo(items, cur); fl.addWidget(cb)
            self._c.append(cb); lay.addWidget(f)
        # Punctuation
        f = Card(); fl = QHBoxLayout(f)
        fl.setContentsMargins(20,0,20,0); fl.setSpacing(16)
        col = QVBoxLayout(); col.setSpacing(2); col.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        t = QLabel("\u041f\u0443\u043d\u043a\u0442\u0443\u0430\u0446\u0438\u044f"); t.setFont(QFont(FN,14,QFont.Weight.Normal))
        t.setStyleSheet(f"color:{T1};background:transparent;border:none;"); col.addWidget(t)
        d = QLabel("\u0410\u0432\u0442\u043e\u043c\u0430\u0442\u0438\u0447\u0435\u0441\u043a\u0438 \u0440\u0430\u0441\u0441\u0442\u0430\u0432\u043b\u044f\u0435\u0442 \u0437\u0430\u043f\u044f\u0442\u044b\u0435 \u0438 \u0442\u043e\u0447\u043a\u0438"); d.setFont(QFont(FN,12))
        d.setStyleSheet(f"color:{T3};background:transparent;border:none;"); col.addWidget(d)
        fl.addLayout(col, 1)
        self.tog = Switch(self.settings.punctuation); fl.addWidget(self.tog)
        lay.addWidget(f)
        lay.addStretch(); sa.setWidget(c); return sa

    def _pg_stat(self):
        sa = QScrollArea(); sa.setWidgetResizable(True)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        c = QWidget(); lay = QVBoxLayout(c)
        lay.setContentsMargins(0,0,8,0); lay.setSpacing(12)
        st = self.stats
        fr = QHBoxLayout()
        fl = QLabel("\u041f\u0435\u0440\u0438\u043e\u0434:")
        fl.setFont(QFont("Consolas",11)); fl.setStyleSheet(f"color:{T3};background:transparent;border:none;letter-spacing:1px;")
        fr.addWidget(fl); fr.addStretch()
        self._filter = combo(["1 \u043d\u0435\u0434\u0435\u043b\u044f","2 \u043d\u0435\u0434\u0435\u043b\u0438","3 \u043d\u0435\u0434\u0435\u043b\u0438","4 \u043d\u0435\u0434\u0435\u043b\u0438","5 \u043d\u0435\u0434\u0435\u043b\u044c","6 \u043d\u0435\u0434\u0435\u043b\u044c","\u0417\u0430 \u0432\u0441\u0451 \u0432\u0440\u0435\u043c\u044f"],"1 \u043d\u0435\u0434\u0435\u043b\u044f")
        self._filter.setFixedWidth(160); self._filter.currentIndexChanged.connect(self._update_stat)
        fr.addWidget(self._filter); lay.addLayout(fr)
        self._kpi_row = QHBoxLayout(); self._kpi_row.setSpacing(12); lay.addLayout(self._kpi_row)
        if st.sessions:
            f = Card(); f.setMinimumHeight(240)
            fl = QVBoxLayout(f); fl.setContentsMargins(20,16,20,12); fl.setSpacing(4)
            t = QLabel("\u0410\u043a\u0442\u0438\u0432\u043d\u043e\u0441\u0442\u044c \u043f\u043e \u0434\u043d\u044f\u043c")
            t.setFont(QFont("Consolas",11)); t.setStyleSheet(f"color:{T3};background:transparent;border:none;letter-spacing:1px;")
            fl.addWidget(t)
            self._chart = Chart([]); self._chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            fl.addWidget(self._chart, 1); lay.addWidget(f, 1)
        else:
            lbl = QLabel("\u041f\u043e\u043a\u0430 \u043d\u0435\u0442 \u0434\u0430\u043d\u043d\u044b\u0445")
            lbl.setFont(QFont(FN,13)); lbl.setStyleSheet(f"color:{T3};padding:40px;border:none;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(lbl)
        lay.addStretch(); sa.setWidget(c)
        self._update_stat(); return sa

    def _update_stat(self):
        ft = self._filter.currentText() if hasattr(self,'_filter') else "1 \u043d\u0435\u0434\u0435\u043b\u044f"
        dm = {"\u0417\u0430 \u0432\u0441\u0451 \u0432\u0440\u0435\u043c\u044f":0,"1 \u043d\u0435\u0434\u0435\u043b\u044f":7,"2 \u043d\u0435\u0434\u0435\u043b\u0438":14,"3 \u043d\u0435\u0434\u0435\u043b\u0438":21,"4 \u043d\u0435\u0434\u0435\u043b\u0438":28,"5 \u043d\u0435\u0434\u0435\u043b\u044c":35,"6 \u043d\u0435\u0434\u0435\u043b\u044c":42}
        days = dm.get(ft,0); st = self.stats
        filtered = st.sessions if days==0 else [s for s in st.sessions if datetime.fromtimestamp(s["timestamp"])>=datetime.now()-timedelta(days=days)]
        ts = len(filtered); tw = sum(s.get("word_count",0) for s in filtered)
        tc = sum(s.get("char_count",0) for s in filtered); aw = tw/max(1,ts)
        while self._kpi_row.count():
            it = self._kpi_row.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        for v,l in [(str(ts),"\u0421\u0435\u0441\u0441\u0438\u0439"),(f"{tw:,}","\u0421\u043b\u043e\u0432"),(f"{tc:,}","\u0421\u0438\u043c\u0432\u043e\u043b\u043e\u0432"),(f"{aw:.0f}","\u0421\u043b\u043e\u0432/\u0441\u0435\u0441\u0441\u0438\u044f")]:
            self._kpi_row.addWidget(KPI(v,l))
        if hasattr(self,'_chart') and self._chart:
            daily = defaultdict(int)
            for s in filtered: daily[datetime.fromtimestamp(s["timestamp"]).strftime("%d.%m")] += s.get("word_count",0)
            if days==0:
                chart_data = [(k,daily[k],k) for k in sorted(daily.keys())]
            else:
                today = datetime.now()
                chart_data = [(["\u041f\u043d","\u0412\u0442","\u0421\u0440","\u0427\u0442","\u041f\u0442","\u0421\u0431","\u0412\u0441"][(today-timedelta(days=i)).weekday()],daily.get((today-timedelta(days=i)).strftime("%d.%m"),0),(today-timedelta(days=i)).strftime("%d %B")) for i in range(days-1,-1,-1)]
            self._chart.data = chart_data; self._chart.update()

    def _pg_hist(self):
        sa = QScrollArea(); sa.setWidgetResizable(True)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        c = QWidget(); lay = QVBoxLayout(c)
        lay.setContentsMargins(0,0,8,0); lay.setSpacing(8)
        entries = self.history.get_recent(30)
        if not entries:
            lbl = QLabel("\u0418\u0441\u0442\u043e\u0440\u0438\u044f \u043f\u0443\u0441\u0442\u0430")
            lbl.setFont(QFont(FN,13)); lbl.setStyleSheet(f"color:{T3};padding:40px;border:none;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(lbl)
        else:
            for e in entries: lay.addWidget(Row(e))
            lay.addSpacing(8)
            btn = QPushButton("\u041e\u0447\u0438\u0441\u0442\u0438\u0442\u044c \u0438\u0441\u0442\u043e\u0440\u0438\u044e")
            btn.setObjectName("danger"); btn.clicked.connect(self._clr)
            btn.setFixedHeight(40)
            btn.setStyleSheet(f"QPushButton{{background:transparent;color:#DC2626;border:1px solid rgba(220,38,38,0.3);border-radius:0px;padding:10px;font-size:13px;font-family:{FN};letter-spacing:0.5px;}} QPushButton:hover{{background:rgba(220,38,38,0.08);border-color:rgba(220,38,38,0.5);}}")
            lay.addWidget(btn)
        lay.addStretch(); sa.setWidget(c); return sa

    def _clr(self):
        if QMessageBox.question(self,"\u041e\u0447\u0438\u0441\u0442\u043a\u0430","\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u0432\u0441\u044e \u0438\u0441\u0442\u043e\u0440\u0438\u044e?",QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)==QMessageBox.StandardButton.Yes:
            self.history.clear()
            self._stack.removeWidget(self._stack.widget(2))
            self._stack.insertWidget(2,self._pg_hist())
            self._stack.setCurrentIndex(2)

    def _save(self):
        hm = {"Right Alt":"alt_r","Right Ctrl":"ctrl_r","Left Ctrl":"ctrl_l"}
        lm = {"Auto":"auto","Russian":"ru","English":"en","German":"de","French":"fr","Spanish":"es"}
        self.settings.hotkey = hm.get(self._c[0].currentText(),"alt_r")
        self.settings.trigger_mode = "hold" if self._c[1].currentIndex()==0 else "toggle"
        self.settings.language = lm.get(self._c[2].currentText(),"auto")
        self.settings.hud_theme = self._c[3].currentText()
        self.settings.model_size = self._c[4].currentText()
        self.settings.punctuation = self.tog.isChecked()
        self.settings.save(); self.close()


def open_settings():
    w = SettingsWindow(); w.show(); return w
