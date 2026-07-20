"""GoodVoice Settings — strict Vercel/Anthropic Dark palette."""

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

try:
    import matplotlib
    matplotlib.use("QtAgg")
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


# ── Strict Design Tokens (Vercel / Anthropic Dark) ───────────────

BG          = "#0B0B0E"
BG_SIDEBAR  = "#0F0F14"
BG_CARD     = "#16161E"
BG_CARD_H   = "#1C1C26"
BG_ACTIVE   = "#1E1E2D"
BORDER      = "rgba(255, 255, 255, 0.08)"
BORDER_H    = "rgba(255, 255, 255, 0.14)"

# Text hierarchy
TEXT        = "#FFFFFF"      # headings, primary
TEXT_MID    = "#94A3B8"      # descriptions, secondary
TEXT_DIM    = "#64748B"      # muted, labels

# Accent — single accent color throughout
ACCENT      = "#6366F1"      # Indigo-500
ACCENT_H    = "#818CF8"      # Indigo-400 (hover/lighter)
ACCENT_D    = "#4F46E5"      # Indigo-600 (darker)

FONT        = "Segoe UI"
FONT_MONO   = "Consolas"
RADIUS      = 12
RADIUS_SM   = 8


# ── Helpers ──────────────────────────────────────────────────────

def card_frame() -> QFrame:
    f = QFrame()
    f.setStyleSheet(f"""
        QFrame {{
            background: {BG_CARD};
            border: 1px solid {BORDER};
            border-radius: {RADIUS}px;
        }}
        QFrame:hover {{
            border-color: {BORDER_H};
        }}
    """)
    return f


def kpi_card(value: str, label: str) -> QFrame:
    """Single-color KPI card — all values white."""
    f = card_frame()
    layout = QVBoxLayout(f)
    layout.setContentsMargins(20, 18, 20, 18)
    layout.setSpacing(6)
    val = QLabel(value)
    val.setFont(QFont(FONT_MONO, 30, QFont.Weight.Bold))
    val.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
    layout.addWidget(val)
    lbl = QLabel(label)
    lbl.setFont(QFont(FONT, 12))
    lbl.setStyleSheet(f"color: {TEXT_MID}; background: transparent; border: none;")
    layout.addWidget(lbl)
    return f


def card_row_text(title: str, desc: str = "") -> QVBoxLayout:
    col = QVBoxLayout()
    col.setSpacing(2)
    t = QLabel(title)
    t.setFont(QFont(FONT, 14, QFont.Weight.Medium))
    t.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
    col.addWidget(t)
    if desc:
        d = QLabel(desc)
        d.setFont(QFont(FONT, 11))
        d.setStyleSheet(f"color: {TEXT_DIM}; background: transparent; border: none;")
        d.setWordWrap(True)
        col.addWidget(d)
    return col


def styled_combo(items: list, current: str = None) -> QComboBox:
    c = QComboBox()
    c.addItems(items)
    if current and current in items:
        c.setCurrentText(current)
    c.setFixedHeight(38)
    return c


# ── Sidebar Button ───────────────────────────────────────────────

class SidebarBtn(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(40)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_DIM};
                border: none;
                border-radius: {RADIUS_SM}px;
                padding: 0 16px;
                text-align: left;
                font-size: 13px;
                font-family: {FONT};
            }}
            QPushButton:hover {{
                background: #181824;
                color: {TEXT_MID};
            }}
            QPushButton:checked {{
                background: {BG_ACTIVE};
                color: {TEXT};
                font-weight: 600;
                border-left: 3px solid {ACCENT};
                padding-left: 13px;
            }}
        """)


# ── Bar Chart ────────────────────────────────────────────────────

class BarChart(QWidget):
    def __init__(self, data: list, parent=None):
        super().__init__(parent)
        self.data = data
        self.setMinimumHeight(200)

    def paintEvent(self, event):
        if not self.data:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        ml, mr, mt, mb = 8, 8, 16, 36
        cw, ch = w - ml - mr, h - mt - mb
        max_val = max(v for _, v in self.data) if self.data else 1
        if max_val == 0:
            max_val = 1

        # Grid lines
        p.setPen(QPen(QColor(255, 255, 255, 8), 1, Qt.PenStyle.DotLine))
        for i in range(1, 5):
            gy = mt + int(ch * i / 5)
            p.drawLine(ml, gy, w - mr, gy)

        n = len(self.data)
        bar_w = max(10, min(20, (cw - (n - 1) * 6) // n))
        gap = 6
        total = n * bar_w + (n - 1) * gap
        sx = ml + (cw - total) // 2

        for i, (label, value) in enumerate(self.data):
            x = sx + i * (bar_w + gap)
            bar_h = max(4, int((value / max_val) * ch))
            y = mt + ch - bar_h

            # Gradient bar
            grad = QLinearGradient(x, y, x, y + bar_h)
            grad.setColorAt(0, QColor(ACCENT))
            grad.setColorAt(1, QColor(ACCENT_D))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(x, y, bar_w, bar_h, 3, 3)

            # Day label
            p.setPen(QColor(TEXT_DIM))
            p.setFont(QFont(FONT, 8))
            p.drawText(x, h - 14, bar_w, 16, Qt.AlignmentFlag.AlignCenter, label)

        p.end()


# ── History Item ─────────────────────────────────────────────────

class HistoryItem(QFrame):
    def __init__(self, entry: dict, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: {RADIUS_SM}px;
                padding: 14px 16px;
            }}
            QFrame:hover {{
                background: {BG_CARD_H};
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setSpacing(14)

        # Time
        ts = datetime.fromtimestamp(entry["timestamp"]).strftime("%H:%M")
        time_lbl = QLabel(ts)
        time_lbl.setFont(QFont(FONT_MONO, 11))
        time_lbl.setStyleSheet(f"color: {TEXT_DIM}; background: transparent; border: none;")
        time_lbl.setFixedWidth(48)
        layout.addWidget(time_lbl)

        # Text
        text = entry["text"][:100] + ("..." if len(entry["text"]) > 100 else "")
        text_lbl = QLabel(text)
        text_lbl.setFont(QFont(FONT, 13))
        text_lbl.setStyleSheet(f"color: {TEXT_MID}; background: transparent; border: none;")
        text_lbl.setWordWrap(True)
        layout.addWidget(text_lbl, 1)

        # Word count chip
        chip = QLabel(f"{entry['word_count']} слов")
        chip.setFont(QFont(FONT, 10))
        chip.setStyleSheet(f"""
            color: {ACCENT};
            background: rgba(99, 102, 241, 0.1);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 12px;
            padding: 4px 10px;
        """)
        chip.setFixedHeight(26)
        layout.addWidget(chip)


# ── Main Window ──────────────────────────────────────────────────

class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = Settings().load()
        self.stats = Stats().load()
        self.history = History().load()
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("GoodVoice")
        self.setFixedSize(720, 560)
        self.setStyleSheet(f"""
            QWidget {{
                background: {BG};
                color: {TEXT};
                font-family: {FONT};
            }}
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 6px;
            }}
            QScrollBar::handle:vertical {{
                background: {TEXT_DIM};
                border-radius: 3px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QComboBox {{
                background: {BG_CARD};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: {RADIUS_SM}px;
                padding: 8px 14px;
                font-size: 13px;
                min-width: 180px;
                min-height: 38px;
            }}
            QComboBox:hover {{
                border-color: {ACCENT};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 28px;
            }}
            QComboBox QAbstractItemView {{
                background: {BG_CARD};
                color: {TEXT};
                border: 1px solid {BORDER};
                selection-background-color: {ACCENT}33;
                border-radius: {RADIUS_SM}px;
                padding: 4px;
            }}
            QCheckBox {{
                color: {TEXT};
                font-size: 13px;
                spacing: 10px;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                border: 2px solid {BORDER_H};
                border-radius: 6px;
                background: {BG_CARD};
            }}
            QCheckBox::indicator:checked {{
                background: {ACCENT};
                border-color: {ACCENT};
            }}
            QPushButton {{
                background: transparent;
                color: {TEXT_MID};
                border: 1px solid {BORDER};
                border-radius: {RADIUS_SM}px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 500;
                min-height: 38px;
            }}
            QPushButton:hover {{
                border-color: {ACCENT};
                color: {TEXT};
            }}
            QPushButton#primary {{
                background: {ACCENT};
                color: {TEXT};
                border: none;
                font-weight: 600;
            }}
            QPushButton#primary:hover {{
                background: {ACCENT_H};
            }}
            QPushButton#danger {{
                color: #EF4444;
                border-color: rgba(239, 68, 68, 0.3);
            }}
            QPushButton#danger:hover {{
                background: rgba(239, 68, 68, 0.1);
                border-color: rgba(239, 68, 68, 0.5);
            }}
        """)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background: {BG_SIDEBAR};
                border-right: 1px solid {BORDER};
            }}
        """)
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(16, 24, 16, 24)
        sb.setSpacing(4)

        logo = QLabel("GoodVoice")
        logo.setFont(QFont(FONT, 18, QFont.Weight.Bold))
        logo.setStyleSheet(f"color: {TEXT}; padding: 0 4px 16px 4px; border: none;")
        sb.addWidget(logo)

        self._nav = []
        for name in ["Основные", "Статистика", "История"]:
            btn = SidebarBtn(name)
            btn.clicked.connect(lambda checked, n=name: self._goto(n))
            sb.addWidget(btn)
            self._nav.append((name, btn))

        sb.addStretch()
        ver = QLabel("v1.0.0")
        ver.setFont(QFont(FONT, 9))
        ver.setStyleSheet(f"color: {TEXT_DIM}; padding: 0 4px; border: none;")
        sb.addWidget(ver)

        root.addWidget(sidebar)

        # ── Content ──────────────────────────────────────────────
        content = QFrame()
        content.setStyleSheet(f"background: {BG}; border: none;")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(36, 28, 36, 20)
        cl.setSpacing(0)

        self._title = QLabel("Основные")
        self._title.setFont(QFont(FONT, 24, QFont.Weight.Bold))
        self._title.setStyleSheet(f"color: {TEXT}; border: none;")
        cl.addWidget(self._title)

        sub = QLabel("Настройки голосового ввода")
        sub.setFont(QFont(FONT, 13))
        sub.setStyleSheet(f"color: {TEXT_DIM}; border: none; margin-bottom: 24px;")
        cl.addWidget(sub)

        self._stack = QStackedWidget()
        self._stack.addWidget(self._page_general())
        self._stack.addWidget(self._page_stats())
        self._stack.addWidget(self._page_history())
        cl.addWidget(self._stack, 1)

        # Footer
        footer_line = QFrame()
        footer_line.setFixedHeight(1)
        footer_line.setStyleSheet(f"background: {BORDER}; border: none; margin: 8px 0;")
        cl.addWidget(footer_line)

        footer = QHBoxLayout()
        footer.setContentsMargins(0, 12, 0, 0)
        footer.addStretch()
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.close)
        footer.addWidget(btn_close)
        btn_save = QPushButton("Сохранить")
        btn_save.setObjectName("primary")
        btn_save.setFixedWidth(130)
        btn_save.clicked.connect(self._save)
        footer.addWidget(btn_save)
        cl.addLayout(footer)

        root.addWidget(content, 1)
        self._goto("Основные")

    def _goto(self, name: str):
        self._title.setText(name)
        idx = {"Основные": 0, "Статистика": 1, "История": 2}[name]
        self._stack.setCurrentIndex(idx)
        for n, btn in self._nav:
            btn.setChecked(n == name)

    # ── Pages ────────────────────────────────────────────────────

    def _page_general(self):
        s = QScrollArea()
        s.setWidgetResizable(True)
        s.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        c = QWidget()
        lay = QVBoxLayout(c)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(14)

        # Hotkey
        f = card_frame()
        fl = QVBoxLayout(f)
        fl.setContentsMargins(20, 16, 20, 16)
        fl.setSpacing(10)
        fl.addLayout(card_row_text("Горячая клавиша", "Комбинация для начала записи голоса"))
        self.combo_hotkey = styled_combo(
            ["Right Alt", "Right Ctrl", "Left Ctrl"],
            "Right Alt" if self.settings.hotkey == "alt_r" else (
                "Right Ctrl" if self.settings.hotkey == "ctrl_r" else "Left Ctrl"))
        fl.addWidget(self.combo_hotkey)
        lay.addWidget(f)

        # Trigger
        f = card_frame()
        fl = QVBoxLayout(f)
        fl.setContentsMargins(20, 16, 20, 16)
        fl.setSpacing(10)
        fl.addLayout(card_row_text("Режим записи", "Hold — зажал/говоришь/отпустил. Toggle — нажал/говоришь/нажал"))
        self.combo_mode = styled_combo(
            ["Зажатие (Hold)", "Переключение (Toggle)"],
            "Зажатие (Hold)" if self.settings.trigger_mode == "hold" else "Переключение (Toggle)")
        fl.addWidget(self.combo_mode)
        lay.addWidget(f)

        # Language
        f = card_frame()
        fl = QVBoxLayout(f)
        fl.setContentsMargins(20, 16, 20, 16)
        fl.setSpacing(10)
        fl.addLayout(card_row_text("Язык", "Язык распознавания речи"))
        lang_map = {"auto": "Auto", "ru": "Russian", "en": "English", "de": "German", "fr": "French", "es": "Spanish"}
        self.combo_lang = styled_combo(
            ["Auto", "Russian", "English", "German", "French", "Spanish"],
            lang_map.get(self.settings.language, "Auto"))
        fl.addWidget(self.combo_lang)
        lay.addWidget(f)

        # Punctuation
        f = card_frame()
        fl = QVBoxLayout(f)
        fl.setContentsMargins(20, 16, 20, 16)
        row = QHBoxLayout()
        row.addLayout(card_row_text("Пунктуация", "Автоматически расставляет запятые и точки"))
        row.addStretch()
        self.check_punct = QCheckBox()
        self.check_punct.setChecked(self.settings.punctuation)
        row.addWidget(self.check_punct)
        fl.addLayout(row)
        lay.addWidget(f)

        # Theme
        f = card_frame()
        fl = QVBoxLayout(f)
        fl.setContentsMargins(20, 16, 20, 16)
        fl.setSpacing(10)
        fl.addLayout(card_row_text("Тема HUD", "Визуальный стиль плавающего окна"))
        self.combo_theme = styled_combo(
            ["hybrid_v2", "google", "google_v2", "hybrid", "vercel"],
            self.settings.hud_theme)
        fl.addWidget(self.combo_theme)
        lay.addWidget(f)

        lay.addStretch()
        s.setWidget(c)
        return s

    def _page_stats(self):
        s = QScrollArea()
        s.setWidgetResizable(True)
        s.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        c = QWidget()
        lay = QVBoxLayout(c)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(20)

        st = self.stats

        # KPI row — all white values
        row = QHBoxLayout()
        row.setSpacing(14)
        row.addWidget(kpi_card(str(st.total_sessions), "Сессий"))
        row.addWidget(kpi_card(f"{st.total_words:,}", "Слов"))
        row.addWidget(kpi_card(f"{st.total_chars:,}", "Символов"))
        row.addWidget(kpi_card(f"{st.avg_words:.0f}", "Слов / сессия"))
        lay.addLayout(row)

        # Chart
        if st.sessions:
            f = card_frame()
            fl = QVBoxLayout(f)
            fl.setContentsMargins(20, 16, 20, 16)
            fl.setSpacing(8)
            t = QLabel("Активность по дням")
            t.setFont(QFont(FONT, 13, QFont.Weight.Medium))
            t.setStyleSheet(f"color: {TEXT_MID}; background: transparent; border: none;")
            fl.addWidget(t)

            daily = defaultdict(int)
            for sess in st.sessions:
                day = datetime.fromtimestamp(sess["timestamp"]).strftime("%d.%m")
                daily[day] += sess.get("word_count", 0)
            days = sorted(daily.keys())[-14:]
            data = [(d, daily[d]) for d in days]

            chart = BarChart(data)
            fl.addWidget(chart)
            lay.addWidget(f)
        else:
            empty = QLabel("Пока нет данных")
            empty.setFont(QFont(FONT, 13))
            empty.setStyleSheet(f"color: {TEXT_DIM}; padding: 40px; border: none;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(empty)

        lay.addStretch()
        s.setWidget(c)
        return s

    def _page_history(self):
        s = QScrollArea()
        s.setWidgetResizable(True)
        s.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        c = QWidget()
        lay = QVBoxLayout(c)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        entries = self.history.get_recent(30)
        if not entries:
            empty = QLabel("История пуста")
            empty.setFont(QFont(FONT, 13))
            empty.setStyleSheet(f"color: {TEXT_DIM}; padding: 40px; border: none;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(empty)
        else:
            for entry in entries:
                lay.addWidget(HistoryItem(entry))
            lay.addSpacing(8)
            btn = QPushButton("Очистить историю")
            btn.setObjectName("danger")
            btn.clicked.connect(self._clear_history)
            lay.addWidget(btn)

        lay.addStretch()
        s.setWidget(c)
        return s

    def _clear_history(self):
        reply = QMessageBox.question(
            self, "Очистка", "Удалить всю историю?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.history.clear()
            self._stack.removeWidget(self._stack.widget(2))
            self._stack.insertWidget(2, self._page_history())
            self._stack.setCurrentIndex(2)

    def _save(self):
        hotkey_map = {"Right Alt": "alt_r", "Right Ctrl": "ctrl_r", "Left Ctrl": "ctrl_l"}
        self.settings.hotkey = hotkey_map.get(self.combo_hotkey.currentText(), "alt_r")
        self.settings.trigger_mode = "hold" if self.combo_mode.currentIndex() == 0 else "toggle"
        lang_rev = {"Auto": "auto", "Russian": "ru", "English": "en", "German": "de", "French": "fr", "Spanish": "es"}
        self.settings.language = lang_rev.get(self.combo_lang.currentText(), "auto")
        self.settings.punctuation = self.check_punct.isChecked()
        self.settings.hud_theme = self.combo_theme.currentText()
        self.settings.save()
        self.close()


def open_settings():
    win = SettingsWindow()
    win.show()
    return win
