"""GoodVoice Settings — polished Vercel/Anthropic Dark with full visual detail."""

import sys
from datetime import datetime, timedelta
from collections import defaultdict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QCheckBox, QPushButton, QMessageBox, QApplication, QFrame,
    QStackedWidget, QScrollArea, QSizePolicy, QToolTip
)
from PyQt6.QtCore import Qt, QRect, QPoint
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QLinearGradient, QPen, QBrush,
    QRadialGradient, QPainterPath, QCursor
)

from settings import Settings
from stats import Stats
from history import History


# ── Tokens ───────────────────────────────────────────────────────

BG       = "#0B0B0E"
BG_SB    = "#0F0F14"
BG_CARD  = "#13131A"
BG_CARD2 = "#16161E"
BD       = "rgba(255,255,255,0.07)"
BD_TOP   = "rgba(255,255,255,0.10)"
BD_HV    = "rgba(99,102,241,0.30)"
BG_HV    = "#1A1A24"
C1       = "#FFFFFF"
C2       = "#94A3B8"
C3       = "#64748B"
C4       = "#808099"
AC       = "#6366F1"
AC_L     = "#818CF8"
AC_D     = "#4F46E5"
RED      = "#EF4444"
F        = "Segoe UI"
FM       = "Consolas"
R        = 10
RS       = 6
CH_W     = 18   # chart bar width


# ── Card frame ───────────────────────────────────────────────────

def card():
    f = QFrame()
    f.setStyleSheet(f"""
        QFrame {{
            background: {BG_CARD};
            border: 1px solid {BD};
            border-top: 1px solid {BD_TOP};
            border-radius: {R}px;
        }}
        QFrame:hover {{
            border-color: {BD_HV};
        }}
    """)
    f.setCursor(Qt.CursorShape.ArrowCursor)
    return f


def kpi(val, lbl):
    f = card()
    f.setMinimumHeight(92)
    l = QVBoxLayout(f)
    l.setContentsMargins(20, 14, 20, 14)
    l.setSpacing(4)
    v = QLabel(val)
    v.setFont(QFont(FM, 28, QFont.Weight.Bold))
    v.setStyleSheet(f"color:{C1};background:transparent;border:none;")
    l.addWidget(v)
    t = QLabel(lbl)
    t.setFont(QFont(F, 12))
    t.setStyleSheet(f"color:{C2};background:transparent;border:none;")
    l.addWidget(t)
    return f


# ── Toggle Switch ────────────────────────────────────────────────

class ToggleSwitch(QCheckBox):
    def __init__(self, checked=False):
        super().__init__()
        self.setChecked(checked)
        self.setFixedSize(44, 24)
        self.setStyleSheet(f"""
            QCheckBox {{
                background: transparent;
                spacing: 0;
            }}
            QCheckBox::indicator {{
                width: 44px;
                height: 24px;
                border-radius: 12px;
                background: #2A2A38;
                border: 1px solid rgba(255,255,255,0.08);
            }}
            QCheckBox::indicator:checked {{
                background: {AC};
                border-color: {AC};
            }}
        """)


# ── Combo ────────────────────────────────────────────────────────

def cmb(items, cur=None):
    c = QComboBox()
    c.addItems(items)
    if cur and cur in items:
        c.setCurrentText(cur)
    c.setFixedWidth(180)
    c.setFixedHeight(34)
    return c


# ── Nav button with icon ─────────────────────────────────────────

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
                border-radius: {RS}px;
                padding: 0 14px;
                text-align: left;
                font-size: 13px;
                font-family: {F};
            }}
            QPushButton:hover {{
                background: #181824;
                color: {C2};
            }}
            QPushButton:checked {{
                background: #1E1E2D;
                color: {C1};
                font-weight: 600;
                border-left: 3px solid {AC};
                padding-left: 11px;
            }}
        """)


# ── Chart with tooltip ───────────────────────────────────────────

class BarChart(QWidget):
    def __init__(self, data):
        super().__init__()
        self.data = data  # [(label, value, date_str)]
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._hover_idx = -1
        self.setMouseTracking(True)

    def mouseMoveEvent(self, e):
        idx = self._hit_test(e.pos())
        if idx != self._hover_idx:
            self._hover_idx = idx
            self.update()
            if idx >= 0 and idx < len(self.data):
                lbl, val, date_str = self.data[idx]
                QToolTip.showText(
                    e.globalPos(),
                    f"{date_str}: {val} слов",
                    self
                )
            else:
                QToolTip.hideText()

    def leaveEvent(self, e):
        self._hover_idx = -1
        self.update()
        QToolTip.hideText()

    def _hit_test(self, pos):
        if not self.data:
            return -1
        w, h = self.width(), self.height()
        ml, mr, mt, mb = 6, 6, 12, 30
        cw = w - ml - mr
        n = len(self.data)
        bw = max(CH_W, min(24, (cw - (n - 1) * 6) // n))
        gap = 6
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
        ml, mr, mt, mb = 6, 6, 12, 30
        cw, ch = w - ml - mr, h - mt - mb
        mx = max(v for _, v, _ in self.data) or 1

        # Grid lines
        pen = QPen(QColor(255, 255, 255, 8), 1, Qt.PenStyle.DotLine)
        p.setPen(pen)
        for i in range(1, 5):
            gy = mt + int(ch * i / 5)
            p.drawLine(ml, gy, w - mr, gy)

        n = len(self.data)
        bw = max(CH_W, min(24, (cw - (n - 1) * 6) // n))
        gap = 6
        total = n * bw + (n - 1) * gap
        sx = ml + (cw - total) // 2

        for i, (lbl, val, _) in enumerate(self.data):
            x = sx + i * (bw + gap)
            if val == 0:
                # Empty day — minimal bar
                bh = 4
                y = mt + ch - bh
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(QColor(255, 255, 255, 12)))
                p.drawRoundedRect(x, y, bw, bh, 2, 2)
            else:
                bh = max(6, int((val / mx) * ch))
                y = mt + ch - bh
                is_hover = (i == self._hover_idx)
                c1 = QColor(AC_L if is_hover else AC)
                c2 = QColor(AC_D)
                g = QLinearGradient(x, y, x, y + bh)
                g.setColorAt(0, c1)
                g.setColorAt(1, c2)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(g))
                p.drawRoundedRect(x, y, bw, bh, 3, 3)

            # Day label
            p.setPen(QColor(C3))
            p.setFont(QFont(F, 9))
            p.drawText(x, h - 20, bw, 18, Qt.AlignmentFlag.AlignCenter, lbl)

        p.end()


# ── History row with copy button ─────────────────────────────────

class HRow(QFrame):
    def __init__(self, entry):
        super().__init__()
        self._text = entry["text"]
        self.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BD};
                border-top: 1px solid {BD_TOP};
                border-radius: {RS}px;
            }}
            QFrame:hover {{
                background: {BG_HV};
                border-color: {BD_HV};
            }}
        """)
        self.setFixedHeight(54)
        l = QHBoxLayout(self)
        l.setContentsMargins(16, 0, 16, 0)
        l.setSpacing(14)

        # Time pill
        ts = datetime.fromtimestamp(entry["timestamp"]).strftime("%H:%M")
        time_frame = QFrame()
        time_frame.setFixedWidth(56)
        time_frame.setFixedHeight(26)
        time_frame.setStyleSheet(f"""
            background: #1C1C28;
            border: 1px solid rgba(160,160,192,0.15);
            border-radius: 8px;
        """)
        tl = QLabel(ts)
        tl.setFont(QFont(FM, 10))
        tl.setStyleSheet(f"color: #A0A0C0; background: transparent; border: none;")
        tl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        fl = QHBoxLayout(time_frame)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.addWidget(tl)
        l.addWidget(time_frame)

        # Text
        txt = self._text[:90] + ("..." if len(self._text) > 90 else "")
        text_lbl = QLabel(txt)
        text_lbl.setFont(QFont(F, 13))
        text_lbl.setStyleSheet(f"color: {C2}; background: transparent; border: none;")
        text_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        l.addWidget(text_lbl, 1)

        # Word count chip
        chip = QLabel(f"{entry['word_count']} слов")
        chip.setFont(QFont(F, 10))
        chip.setStyleSheet(f"""
            color: {AC};
            background: rgba(99,102,241,0.1);
            border: 1px solid rgba(99,102,241,0.2);
            border-radius: 10px;
            padding: 4px 10px;
        """)
        chip.setFixedWidth(72)
        chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        l.addWidget(chip)

        # Copy button (hidden, shows on hover via style)
        self._copy_btn = QPushButton("📋")
        self._copy_btn.setFixedSize(28, 28)
        self._copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(99,102,241,0.15);
                border: 1px solid rgba(99,102,241,0.3);
                border-radius: 6px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background: rgba(99,102,241,0.3);
            }}
        """)
        self._copy_btn.clicked.connect(self._copy)
        self._copy_btn.setVisible(False)
        l.addWidget(self._copy_btn)

    def enterEvent(self, e):
        self._copy_btn.setVisible(True)

    def leaveEvent(self, e):
        self._copy_btn.setVisible(False)

    def _copy(self):
        QApplication.clipboard().setText(self._text)
        self._copy_btn.setText("✓")
        QTimer.singleShot(800, lambda: self._copy_btn.setText("📋"))


from PyQt6.QtCore import QTimer


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
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 6px;
                margin: 0 4px 0 0;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255,255,255,0.10);
                border-radius: 3px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {{
                background: none;
            }}
            QComboBox {{
                background: #1E1E2A;
                color: {C1};
                border: 1px solid {BD};
                border-radius: {RS}px;
                padding: 6px 12px;
                font-size: 13px;
            }}
            QComboBox:hover {{
                border-color: {AC};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 26px;
            }}
            QComboBox QAbstractItemView {{
                background: #1E1E2A;
                color: {C1};
                border: 1px solid {BD};
                selection-background-color: {AC}33;
                border-radius: {RS}px;
                padding: 2px;
            }}
            QPushButton {{
                background: transparent;
                color: {C2};
                border: 1px solid {BD};
                border-radius: {RS}px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: 500;
                min-height: 36px;
            }}
            QPushButton:hover {{
                border-color: {AC};
                color: {C1};
            }}
            QPushButton#ok {{
                background: {AC};
                color: {C1};
                border: none;
                font-weight: 600;
                min-width: 120px;
            }}
            QPushButton#ok:hover {{
                background: {AC_L};
            }}
            QPushButton#danger {{
                color: {RED};
                border-color: rgba(239,68,68,0.3);
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
        sb.setStyleSheet(f"background:{BG_SB};border-right:1px solid {BD};")
        sbl = QVBoxLayout(sb)
        sbl.setContentsMargins(18, 24, 18, 20)
        sbl.setSpacing(2)

        logo = QLabel("🎙  GoodVoice")
        logo.setFont(QFont(F, 18, QFont.Weight.Bold))
        logo.setStyleSheet(f"color:{C1};padding:0 4px 16px 4px;border:none;")
        sbl.addWidget(logo)

        self._nav = []
        for icon, name in [("⚙", "Основные"), ("📊", "Статистика"), ("📜", "История")]:
            b = Nav(icon, name)
            b.clicked.connect(lambda checked, n=name: self._goto(n))
            sbl.addWidget(b)
            self._nav.append((name, b))
        sbl.addStretch()
        ver = QLabel("v1.0.0")
        ver.setFont(QFont(F, 9))
        ver.setStyleSheet(f"color:{C3};padding:0 4px;border:none;")
        sbl.addWidget(ver)

        root.addWidget(sb)

        # Content
        ct = QFrame()
        ct.setStyleSheet(f"background:{BG};border:none;")
        ctl = QVBoxLayout(ct)
        ctl.setContentsMargins(36, 28, 36, 20)
        ctl.setSpacing(0)

        self._title = QLabel("Основные")
        self._title.setFont(QFont(F, 22, QFont.Weight.Bold))
        self._title.setStyleSheet(f"color:{C1};border:none;")
        ctl.addWidget(self._title)

        sub = QLabel("Настройки голосового ввода")
        sub.setFont(QFont(F, 13))
        sub.setStyleSheet(f"color:{C3};border:none;margin-bottom:20px;")
        ctl.addWidget(sub)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._pg_gen())
        self._stack.addWidget(self._pg_stat())
        self._stack.addWidget(self._pg_hist())
        ctl.addWidget(self._stack, 1)

        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background:{BD};border:none;margin:12px 0;")
        ctl.addWidget(line)

        fl = QHBoxLayout()
        fl.setContentsMargins(0, 0, 0, 0)
        fl.addStretch()
        bc = QPushButton("Закрыть")
        bc.clicked.connect(self.close)
        fl.addWidget(bc)
        bs = QPushButton("Сохранить")
        bs.setObjectName("ok")
        bs.clicked.connect(self._save)
        fl.addWidget(bs)
        ctl.addLayout(fl)

        root.addWidget(ct, 1)
        self._goto("Основные")

    def _goto(self, name):
        self._title.setText(name)
        idx = {"Основные": 0, "Статистика": 1, "История": 2}[name]
        self._stack.setCurrentIndex(idx)
        for n, b in self._nav:
            b.setChecked(n == name)

    # ── General page ─────────────────────────────────────────────

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
            ("Горячая клавиша", "Комбинация для начала записи",
             ["Right Alt", "Right Ctrl", "Left Ctrl"],
             "Right Alt" if self.settings.hotkey == "alt_r" else
             ("Right Ctrl" if self.settings.hotkey == "ctrl_r" else "Left Ctrl")),
            ("Режим записи", "Hold — зажал/отпустил. Toggle — нажал/нажал",
             ["Зажатие (Hold)", "Переключение (Toggle)"],
             "Зажатие (Hold)" if self.settings.trigger_mode == "hold" else "Переключение (Toggle)"),
            ("Язык", "Язык распознавания речи",
             ["Auto", "Russian", "English", "German", "French", "Spanish"],
             lm.get(self.settings.language, "Auto")),
            ("Тема HUD", "Визуальный стиль плавающего окна",
             ["hybrid_v2", "google", "google_v2", "hybrid", "vercel"],
             self.settings.hud_theme),
        ]

        self._combos = []
        for title, desc, items, cur in defs:
            f = card()
            fl = QHBoxLayout(f)
            fl.setContentsMargins(20, 0, 20, 0)
            fl.setSpacing(16)
            col = QVBoxLayout()
            col.setSpacing(2)
            t = QLabel(title)
            t.setFont(QFont(F, 14, QFont.Weight.Medium))
            t.setStyleSheet(f"color:{C1};background:transparent;border:none;")
            col.addWidget(t)
            d = QLabel(desc)
            d.setFont(QFont(F, 11))
            d.setStyleSheet(f"color:{C4};background:transparent;border:none;")
            col.addWidget(d)
            fl.addLayout(col, 1)
            cb = cmb(items, cur)
            fl.addWidget(cb)
            self._combos.append(cb)
            lay.addWidget(f)

        # Punctuation toggle
        f = card()
        fl = QHBoxLayout(f)
        fl.setContentsMargins(20, 0, 20, 0)
        fl.setSpacing(16)
        col = QVBoxLayout()
        col.setSpacing(2)
        t = QLabel("Пунктуация")
        t.setFont(QFont(F, 14, QFont.Weight.Medium))
        t.setStyleSheet(f"color:{C1};background:transparent;border:none;")
        col.addWidget(t)
        d = QLabel("Автоматически расставляет запятые и точки")
        d.setFont(QFont(F, 11))
        d.setStyleSheet(f"color:{C4};background:transparent;border:none;")
        col.addWidget(d)
        fl.addLayout(col, 1)
        self.chk = ToggleSwitch(self.settings.punctuation)
        fl.addWidget(self.chk)
        lay.addWidget(f)

        lay.addStretch()
        sa.setWidget(c)
        return sa

    # ── Stats page ───────────────────────────────────────────────

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
        row.addWidget(kpi(str(st.total_sessions), "Сессий"))
        row.addWidget(kpi(f"{st.total_words:,}", "Слов"))
        row.addWidget(kpi(f"{st.total_chars:,}", "Символов"))
        row.addWidget(kpi(f"{st.avg_words:.0f}", "Слов / сессия"))
        lay.addLayout(row)

        if st.sessions:
            f = card()
            f.setMinimumHeight(260)
            fl = QVBoxLayout(f)
            fl.setContentsMargins(20, 16, 20, 12)
            fl.setSpacing(6)
            t = QLabel("Активность по дням")
            t.setFont(QFont(F, 13, QFont.Weight.Medium))
            t.setStyleSheet(f"color:{C2};background:transparent;border:none;")
            fl.addWidget(t)

            daily = defaultdict(int)
            for sess in st.sessions:
                day = datetime.fromtimestamp(sess["timestamp"]).strftime("%d.%m")
                daily[day] += sess.get("word_count", 0)

            # Last 14 days with zero-fill
            today = datetime.now()
            days = []
            for i in range(13, -1, -1):
                d = today - timedelta(days=i)
                key = d.strftime("%d.%m")
                label = ["Пн","Вт","Ср","Чт","Пт","Сб","Вс"][d.weekday()]
                days.append((label, daily.get(key, 0), d.strftime("%d %B")))

            chart = BarChart(days)
            chart.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            fl.addWidget(chart, 1)
            lay.addWidget(f, 1)
        else:
            lbl = QLabel("Пока нет данных")
            lbl.setFont(QFont(F, 13))
            lbl.setStyleSheet(f"color:{C3};padding:40px;border:none;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(lbl)

        lay.addStretch()
        sa.setWidget(c)
        return sa

    # ── History page ─────────────────────────────────────────────

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
            lbl = QLabel("История пуста")
            lbl.setFont(QFont(F, 13))
            lbl.setStyleSheet(f"color:{C3};padding:40px;border:none;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(lbl)
        else:
            for e in entries:
                lay.addWidget(HRow(e))
            lay.addSpacing(8)
            btn = QPushButton("Очистить историю")
            btn.setObjectName("danger")
            btn.clicked.connect(self._clr)
            lay.addWidget(btn)

        lay.addStretch()
        sa.setWidget(c)
        return sa

    def _clr(self):
        if QMessageBox.question(self, "Очистка", "Удалить всю историю?",
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
        self.settings.punctuation = self.chk.isChecked()
        self.settings.save()
        self.close()


def open_settings():
    w = SettingsWindow()
    w.show()
    return w
