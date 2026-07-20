"""GoodVoice Settings — compact Vercel/Anthropic Dark layout."""

import sys
import time
from datetime import datetime
from collections import defaultdict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QCheckBox, QPushButton, QMessageBox, QApplication, QFrame,
    QStackedWidget, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPainter, QLinearGradient, QPen, QBrush

from settings import Settings
from stats import Stats
from history import History


# ── Tokens ───────────────────────────────────────────────────────

BG         = "#0B0B0E"
BG_SB      = "#0F0F14"
BG_CARD    = "#16161E"
BG_ACTIVE  = "#1E1E2D"
BORDER     = "rgba(255,255,255,0.08)"
BORDER_H   = "rgba(255,255,255,0.14)"
TEXT       = "#FFFFFF"
TEXT2      = "#94A3B8"
TEXT3      = "#64748B"
ACCENT     = "#6366F1"
ACCENT_H   = "#818CF8"
RED        = "#EF4444"
FONT       = "Segoe UI"
FM         = "Consolas"
R          = 10
RS         = 6


# ── Widgets ──────────────────────────────────────────────────────

def card(h: int = None) -> QFrame:
    f = QFrame()
    style = f"background:{BG_CARD};border:1px solid {BORDER};border-radius:{R}px;"
    if h:
        style += f"min-height:{h}px;max-height:{h}px;"
    f.setStyleSheet(style)
    return f


def kpi(value: str, label: str) -> QFrame:
    f = card(88)
    l = QVBoxLayout(f)
    l.setContentsMargins(16, 12, 16, 12)
    l.setSpacing(2)
    v = QLabel(value)
    v.setFont(QFont(FM, 26, QFont.Weight.Bold))
    v.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
    l.addWidget(v)
    lb = QLabel(label)
    lb.setFont(QFont(FONT, 11))
    lb.setStyleSheet(f"color:{TEXT2};background:transparent;border:none;")
    l.addWidget(lb)
    return f


def combo(items, cur=None) -> QComboBox:
    c = QComboBox()
    c.addItems(items)
    if cur and cur in items:
        c.setCurrentText(cur)
    c.setFixedHeight(34)
    return c


class NavBtn(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setFixedHeight(36)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton{{background:transparent;color:{TEXT3};border:none;
                border-radius:{RS}px;padding:0 14px;text-align:left;
                font-size:13px;font-family:{FONT};}}
            QPushButton:hover{{background:#181824;color:{TEXT2};}}
            QPushButton:checked{{background:{BG_ACTIVE};color:{TEXT};
                font-weight:600;border-left:3px solid {ACCENT};padding-left:11px;}}
        """)


class BarChart(QWidget):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.setFixedHeight(160)

    def paintEvent(self, e):
        if not self.data:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        ml, mr, mt, mb = 4, 4, 10, 28
        cw, ch = w - ml - mr, h - mt - mb
        mx = max(v for _, v in self.data) or 1

        # Grid
        pen = QPen(QColor(255, 255, 255, 8), 1, Qt.PenStyle.DotLine)
        p.setPen(pen)
        for i in range(1, 5):
            gy = mt + int(ch * i / 5)
            p.drawLine(ml, gy, w - mr, gy)

        n = len(self.data)
        bw = max(12, min(18, (cw - (n - 1) * 5) // n))
        gap = 5
        total = n * bw + (n - 1) * gap
        sx = ml + (cw - total) // 2

        for i, (lbl, val) in enumerate(self.data):
            x = sx + i * (bw + gap)
            bh = max(4, int((val / mx) * ch))
            y = mt + ch - bh
            g = QLinearGradient(x, y, x, y + bh)
            g.setColorAt(0, QColor(ACCENT))
            g.setColorAt(1, QColor("#4F46E5"))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(g))
            p.drawRoundedRect(x, y, bw, bh, 3, 3)
            p.setPen(QColor(TEXT3))
            p.setFont(QFont(FONT, 8))
            p.drawText(x, h - 18, bw, 16, Qt.AlignmentFlag.AlignCenter, lbl)

        p.end()


class HistoryRow(QFrame):
    def __init__(self, entry):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame{{background:{BG_CARD};border:1px solid {BORDER};
                border-radius:{RS}px;padding:10px 14px;}}
            QFrame:hover{{background:{BG_CARD}{{}}.replace('{BG_CARD}','#1C1C26');}}
        """)
        self.setFixedHeight(52)
        l = QHBoxLayout(self)
        l.setSpacing(12)
        l.setContentsMargins(14, 0, 14, 0)

        ts = datetime.fromtimestamp(entry["timestamp"]).strftime("%H:%M")
        t = QLabel(ts)
        t.setFont(QFont(FM, 11))
        t.setStyleSheet(f"color:{TEXT3};background:transparent;border:none;")
        t.setFixedWidth(44)
        l.addWidget(t)

        txt = entry["text"][:80] + ("..." if len(entry["text"]) > 80 else "")
        tl = QLabel(txt)
        tl.setFont(QFont(FONT, 12))
        tl.setStyleSheet(f"color:{TEXT2};background:transparent;border:none;")
        l.addWidget(tl, 1)

        chip = QLabel(f"{entry['word_count']} слов")
        chip.setFont(QFont(FONT, 9))
        chip.setStyleSheet(f"""
            color:{ACCENT};background:rgba(99,102,241,0.1);
            border:1px solid rgba(99,102,241,0.2);
            border-radius:10px;padding:3px 8px;
        """)
        chip.setFixedHeight(22)
        l.addWidget(chip)


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
        self.setFixedSize(680, 500)
        self.setStyleSheet(f"""
            QWidget{{background:{BG};color:{TEXT};font-family:{FONT};}}
            QScrollArea{{border:none;background:transparent;}}
            QScrollBar:vertical{{background:transparent;width:4px;}}
            QScrollBar::handle:vertical{{background:rgba(255,255,255,0.15);
                border-radius:2px;min-height:20px;}}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{height:0;}}
            QComboBox{{background:{BG_CARD};color:{TEXT};border:1px solid {BORDER};
                border-radius:{RS}px;padding:6px 10px;font-size:12px;
                min-width:150px;max-height:34px;}}
            QComboBox:hover{{border-color:{ACCENT};}}
            QComboBox::drop-down{{border:none;width:24px;}}
            QComboBox QAbstractItemView{{background:{BG_CARD};color:{TEXT};
                border:1px solid {BORDER};selection-background-color:{ACCENT}33;
                border-radius:{RS}px;padding:2px;}}
            QCheckBox{{color:{TEXT};font-size:12px;spacing:8px;}}
            QCheckBox::indicator{{width:18px;height:18px;border:2px solid {BORDER_H};
                border-radius:5px;background:{BG_CARD};}}
            QCheckBox::indicator:checked{{background:{ACCENT};border-color:{ACCENT};}}
            QPushButton{{background:transparent;color:{TEXT2};border:1px solid {BORDER};
                border-radius:{RS}px;padding:8px 16px;font-size:12px;
                font-weight:500;max-height:34px;}}
            QPushButton:hover{{border-color:{ACCENT};color:{TEXT};}}
            QPushButton#ok{{background:{ACCENT};color:{TEXT};border:none;font-weight:600;
                min-width:110px;}}
            QPushButton#ok:hover{{background:{ACCENT_H};}}
            QPushButton#danger{{color:{RED};border-color:rgba(239,68,68,0.3);}}
            QPushButton#danger:hover{{background:rgba(239,68,68,0.08);}}
        """)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        sb = QFrame()
        sb.setFixedWidth(180)
        sb.setStyleSheet(f"background:{BG_SB};border-right:1px solid {BORDER};")
        sbl = QVBoxLayout(sb)
        sbl.setContentsMargins(14, 20, 14, 16)
        sbl.setSpacing(2)

        logo = QLabel("GoodVoice")
        logo.setFont(QFont(FONT, 16, QFont.Weight.Bold))
        logo.setStyleSheet(f"color:{TEXT};padding:0 4px 12px 4px;border:none;")
        sbl.addWidget(logo)

        self._nav = []
        for name in ["Основные", "Статистика", "История"]:
            b = NavBtn(name)
            b.clicked.connect(lambda checked, n=name: self._goto(n))
            sbl.addWidget(b)
            self._nav.append((name, b))
        sbl.addStretch()

        # Content
        ct = QFrame()
        ct.setStyleSheet(f"background:{BG};border:none;")
        ctl = QVBoxLayout(ct)
        ctl.setContentsMargins(28, 22, 28, 16)
        ctl.setSpacing(0)

        self._title = QLabel("Основные")
        self._title.setFont(QFont(FONT, 20, QFont.Weight.Bold))
        self._title.setStyleSheet(f"color:{TEXT};border:none;")
        ctl.addWidget(self._title)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._pg_general())
        self._stack.addWidget(self._pg_stats())
        self._stack.addWidget(self._pg_history())
        ctl.addWidget(self._stack, 1)

        # Footer — fixed, no scroll
        line = QFrame()
        line.setFixedHeight(1)
        line.setStyleSheet(f"background:{BORDER};border:none;margin:8px 0;")
        ctl.addWidget(line)
        fl = QHBoxLayout()
        fl.setContentsMargins(0, 8, 0, 0)
        fl.addStretch()
        bc = QPushButton("Закрыть")
        bc.clicked.connect(self.close)
        fl.addWidget(bc)
        bs = QPushButton("Сохранить")
        bs.setObjectName("ok")
        bs.clicked.connect(self._save)
        fl.addWidget(bs)
        ctl.addLayout(fl)

        root.addWidget(sb)
        root.addWidget(ct, 1)
        self._goto("Основные")

    def _goto(self, name):
        self._title.setText(name)
        self._stack.setCurrentIndex({"Основные": 0, "Статистика": 1, "История": 2}[name])
        for n, b in self._nav:
            b.setChecked(n == name)

    # ── Pages ────────────────────────────────────────────────────

    def _pg_general(self):
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        c = QWidget()
        lay = QVBoxLayout(c)
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(10)

        lang_map = {"auto": "Auto", "ru": "Russian", "en": "English",
                     "de": "German", "fr": "French", "es": "Spanish"}

        rows = [
            ("Горячая клавиша", "Комбинация для начала записи",
             combo(["Right Alt", "Right Ctrl", "Left Ctrl"],
                   "Right Alt" if self.settings.hotkey == "alt_r" else
                   ("Right Ctrl" if self.settings.hotkey == "ctrl_r" else "Left Ctrl"))),
            ("Режим записи", "Hold — зажал/отпустил. Toggle — нажал/нажал",
             combo(["Зажатие (Hold)", "Переключение (Toggle)"],
                   "Зажатие (Hold)" if self.settings.trigger_mode == "hold" else "Переключение (Toggle)")),
            ("Язык", "Язык распознавания речи",
             combo(["Auto", "Russian", "English", "German", "French", "Spanish"],
                   lang_map.get(self.settings.language, "Auto"))),
            ("Тема HUD", "Визуальный стиль плавающего окна",
             combo(["hybrid_v2", "google", "google_v2", "hybrid", "vercel"],
                   self.settings.hud_theme)),
        ]

        for title, desc, widget in rows:
            f = card(64)
            fl = QHBoxLayout(f)
            fl.setContentsMargins(16, 0, 16, 0)
            fl.setSpacing(12)
            col = QVBoxLayout()
            col.setSpacing(1)
            t = QLabel(title)
            t.setFont(QFont(FONT, 13, QFont.Weight.Medium))
            t.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
            col.addWidget(t)
            d = QLabel(desc)
            d.setFont(QFont(FONT, 10))
            d.setStyleSheet(f"color:{TEXT3};background:transparent;border:none;")
            col.addWidget(d)
            fl.addLayout(col, 1)
            fl.addWidget(widget)
            lay.addWidget(f)

        # Punctuation
        f = card(56)
        fl = QHBoxLayout(f)
        fl.setContentsMargins(16, 0, 16, 0)
        t = QLabel("Пунктуация")
        t.setFont(QFont(FONT, 13, QFont.Weight.Medium))
        t.setStyleSheet(f"color:{TEXT};background:transparent;border:none;")
        fl.addWidget(t, 1)
        self.chk_p = QCheckBox()
        self.chk_p.setChecked(self.settings.punctuation)
        fl.addWidget(self.chk_p)
        lay.addWidget(f)

        lay.addStretch()
        sa.setWidget(c)
        return sa

    def _pg_stats(self):
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        c = QWidget()
        lay = QVBoxLayout(c)
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(16)

        st = self.stats
        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(kpi(str(st.total_sessions), "Сессий"))
        row.addWidget(kpi(f"{st.total_words:,}", "Слов"))
        row.addWidget(kpi(f"{st.total_chars:,}", "Символов"))
        row.addWidget(kpi(f"{st.avg_words:.0f}", "Слов/сессия"))
        lay.addLayout(row)

        if st.sessions:
            f = card(220)
            fl = QVBoxLayout(f)
            fl.setContentsMargins(16, 12, 16, 8)
            fl.setSpacing(4)
            t = QLabel("Активность по дням")
            t.setFont(QFont(FONT, 12, QFont.Weight.Medium))
            t.setStyleSheet(f"color:{TEXT2};background:transparent;border:none;")
            fl.addWidget(t)
            daily = defaultdict(int)
            for s in st.sessions:
                day = datetime.fromtimestamp(s["timestamp"]).strftime("%d.%m")
                daily[day] += s.get("word_count", 0)
            days = sorted(daily.keys())[-14:]
            fl.addWidget(BarChart([(d, daily[d]) for d in days]))
            lay.addWidget(f)

        lay.addStretch()
        sa.setWidget(c)
        return sa

    def _pg_history(self):
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        c = QWidget()
        lay = QVBoxLayout(c)
        lay.setContentsMargins(0, 0, 8, 0)
        lay.setSpacing(6)

        entries = self.history.get_recent(30)
        if not entries:
            empty = QLabel("История пуста")
            empty.setFont(QFont(FONT, 12))
            empty.setStyleSheet(f"color:{TEXT3};padding:32px;border:none;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(empty)
        else:
            for entry in entries:
                lay.addWidget(HistoryRow(entry))
            lay.addSpacing(6)
            btn = QPushButton("Очистить историю")
            btn.setObjectName("danger")
            btn.clicked.connect(self._clear_hist)
            lay.addWidget(btn)

        lay.addStretch()
        sa.setWidget(c)
        return sa

    def _clear_hist(self):
        if QMessageBox.question(self, "Очистка", "Удалить всю историю?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) == QMessageBox.StandardButton.Yes:
            self.history.clear()
            self._stack.removeWidget(self._stack.widget(2))
            self._stack.insertWidget(2, self._pg_history())
            self._stack.setCurrentIndex(2)

    def _save(self):
        hm = {"Right Alt": "alt_r", "Right Ctrl": "ctrl_r", "Left Ctrl": "ctrl_l"}
        self.settings.hotkey = hm.get(self.combo_hotkey.currentText() if hasattr(self, 'combo_hotkey') else "Right Alt", "alt_r")
        # Find the actual combo widgets from the general page
        page = self._stack.widget(0)
        if page:
            sa = page if isinstance(page, QScrollArea) else None
            if sa:
                container = sa.widget()
                if container:
                    layout = container.layout()
                    # Get combos from layout children
                    combos = []
                    for i in range(layout.count()):
                        item = layout.itemAt(i)
                        if item and item.widget():
                            fw = item.widget()
                            for j in range(fw.layout().count()):
                                sub = fw.layout().itemAt(j)
                                if sub and hasattr(sub, 'widget') and sub.widget() and isinstance(sub.widget(), QComboBox):
                                    combos.append(sub.widget())
                    if len(combos) >= 4:
                        self.settings.hotkey = hm.get(combos[0].currentText(), "alt_r")
                        self.settings.trigger_mode = "hold" if combos[1].currentIndex() == 0 else "toggle"
                        lr = {"Auto": "auto", "Russian": "ru", "English": "en",
                              "German": "de", "French": "fr", "Spanish": "es"}
                        self.settings.language = lr.get(combos[2].currentText(), "auto")
                        self.settings.hud_theme = combos[3].currentText()
        self.settings.punctuation = self.chk_p.isChecked()
        self.settings.save()
        self.close()


def open_settings():
    w = SettingsWindow()
    w.show()
    return w
