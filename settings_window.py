"""GoodVoice Settings — premium dark UI with sidebar, cards, charts."""

import sys
import time
from datetime import datetime, timedelta
from collections import defaultdict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QCheckBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QApplication, QFrame,
    QStackedWidget, QScrollArea, QSizePolicy, QSpacerItem,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPainter, QLinearGradient, QPen, QBrush

from settings import Settings
from stats import Stats
from history import History

try:
    import matplotlib
    matplotlib.use("QtAgg")
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


# ── Design Tokens ────────────────────────────────────────────────

BG_MAIN     = "#0F0F12"
BG_SIDEBAR  = "#141418"
BG_CARD     = "#1A1A1E"
BG_CARD_H   = "#222228"
BORDER      = "rgba(255,255,255,0.06)"
BORDER_H    = "rgba(255,255,255,0.12)"
TEXT        = "#E8E8EC"
TEXT_DIM    = "#6B6B76"
TEXT_MUTED  = "#4A4A55"
ACCENT      = "#8B5CF6"
ACCENT2     = "#6366F1"
CYAN        = "#06B6D4"
GREEN       = "#22C55E"
RED         = "#EF4444"
YELLOW      = "#EAB308"
ORANGE      = "#F97316"
FONT        = "Segoe UI"
FONT_MONO   = "Consolas"
RADIUS      = 12
RADIUS_SM   = 8


# ── Helpers ──────────────────────────────────────────────────────

def card(widget=None):
    """Wrap widget in a card frame."""
    frame = QFrame()
    frame.setStyleSheet(f"""
        QFrame {{
            background: {BG_CARD};
            border: 1px solid {BORDER};
            border-radius: {RADIUS}px;
        }}
        QFrame:hover {{
            border-color: {BORDER_H};
        }}
    """)
    if widget:
        return widget, frame
    return frame


def section_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(QFont(FONT, 11, QFont.Weight.DemiBold))
    lbl.setStyleSheet(f"color: {TEXT_DIM}; background: transparent; border: none; padding: 4px 0;")
    return lbl


def card_row(label: str, description: str = "") -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(12)
    text_col = QVBoxLayout()
    text_col.setSpacing(2)
    lbl = QLabel(label)
    lbl.setFont(QFont(FONT, 13))
    lbl.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
    text_col.addWidget(lbl)
    if description:
        desc = QLabel(description)
        desc.setFont(QFont(FONT, 10))
        desc.setStyleSheet(f"color: {TEXT_DIM}; background: transparent; border: none;")
        desc.setWordWrap(True)
        text_col.addWidget(desc)
    row.addLayout(text_col)
    row.addStretch()
    return row


def styled_combo(items: list, current: str = None) -> QComboBox:
    combo = QComboBox()
    combo.addItems(items)
    if current and current in items:
        combo.setCurrentText(current)
    combo.setFixedHeight(36)
    return combo


def styled_checkbox(text: str, checked: bool = False) -> QCheckBox:
    cb = QCheckBox(text)
    cb.setChecked(checked)
    return cb


def kpi_card(value: str, label: str, color: str = TEXT) -> QFrame:
    frame = QFrame()
    frame.setStyleSheet(f"""
        QFrame {{
            background: {BG_CARD};
            border: 1px solid {BORDER};
            border-radius: {RADIUS}px;
            padding: 16px;
        }}
    """)
    layout = QVBoxLayout(frame)
    layout.setSpacing(4)
    val = QLabel(value)
    val.setFont(QFont(FONT_MONO, 28, QFont.Weight.Bold))
    val.setStyleSheet(f"color: {color}; background: transparent; border: none;")
    layout.addWidget(val)
    lbl = QLabel(label)
    lbl.setFont(QFont(FONT, 11))
    lbl.setStyleSheet(f"color: {TEXT_DIM}; background: transparent; border: none;")
    layout.addWidget(lbl)
    return frame


# ── Sidebar Button ───────────────────────────────────────────────

class SidebarButton(QPushButton):
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
                background: {BG_CARD};
                color: {TEXT};
            }}
            QPushButton:checked {{
                background: {ACCENT}22;
                color: {ACCENT};
                font-weight: 600;
            }}
        """)


# ── Chart Widget ─────────────────────────────────────────────────

class BarChart(QWidget):
    def __init__(self, data: list, parent=None):
        super().__init__(parent)
        self.data = data  # list of (label, value)
        self.setMinimumHeight(180)

    def paintEvent(self, event):
        if not self.data:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        margin_l, margin_r, margin_t, margin_b = 10, 10, 20, 30
        chart_w = w - margin_l - margin_r
        chart_h = h - margin_t - margin_b

        max_val = max(v for _, v in self.data) if self.data else 1
        if max_val == 0:
            max_val = 1

        n = len(self.data)
        bar_w = max(8, min(40, (chart_w - (n - 1) * 6) // n))
        gap = 6
        total_w = n * bar_w + (n - 1) * gap
        start_x = margin_l + (chart_w - total_w) // 2

        # Draw bars
        for i, (label, value) in enumerate(self.data):
            x = start_x + i * (bar_w + gap)
            bar_h = int((value / max_val) * chart_h)
            y = margin_t + chart_h - bar_h

            # Gradient bar
            grad = QLinearGradient(x, y, x, y + bar_h)
            grad.setColorAt(0, QColor(ACCENT))
            grad.setColorAt(1, QColor(ACCENT2))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(grad))
            p.drawRoundedRect(x, y, bar_w, bar_h, 4, 4)

            # Label
            if n <= 14:
                p.setPen(QColor(TEXT_DIM))
                p.setFont(QFont(FONT, 8))
                p.drawText(x, h - 10, bar_w, 16, Qt.AlignmentFlag.AlignCenter, label)

        p.end()


# ── History Item Widget ──────────────────────────────────────────

class HistoryItem(QFrame):
    def __init__(self, entry: dict, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: {RADIUS_SM}px;
                padding: 12px;
            }}
            QFrame:hover {{
                background: {BG_CARD_H};
                border-color: {BORDER_H};
            }}
        """)
        layout = QHBoxLayout(self)
        layout.setSpacing(12)

        # Time
        ts = datetime.fromtimestamp(entry["timestamp"]).strftime("%H:%M")
        time_lbl = QLabel(ts)
        time_lbl.setFont(QFont(FONT_MONO, 11))
        time_lbl.setStyleSheet(f"color: {TEXT_DIM}; background: transparent; border: none;")
        time_lbl.setFixedWidth(50)
        layout.addWidget(time_lbl)

        # Text
        text = entry["text"][:100] + ("..." if len(entry["text"]) > 100 else "")
        text_lbl = QLabel(text)
        text_lbl.setFont(QFont(FONT, 12))
        text_lbl.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
        text_lbl.setWordWrap(True)
        layout.addWidget(text_lbl, 1)

        # Word count chip
        words = entry["word_count"]
        chip = QLabel(f"{words} слов")
        chip.setFont(QFont(FONT, 10))
        chip.setStyleSheet(f"""
            color: {ACCENT};
            background: {ACCENT}15;
            border: 1px solid {ACCENT}30;
            border-radius: 12px;
            padding: 4px 10px;
        """)
        chip.setFixedHeight(24)
        layout.addWidget(chip)


# ── Main Settings Window ─────────────────────────────────────────

class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = Settings().load()
        self.stats = Stats().load()
        self.history = History().load()
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("GoodVoice")
        self.setFixedSize(720, 540)
        self.setStyleSheet(f"""
            QWidget {{
                background: {BG_MAIN};
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
                background: {TEXT_MUTED};
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
                padding: 8px 12px;
                font-size: 13px;
                min-width: 160px;
                min-height: 36px;
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
                selection-background-color: {ACCENT}44;
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
                background: {BG_CARD};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: {RADIUS_SM}px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 500;
                min-height: 36px;
            }}
            QPushButton:hover {{
                border-color: {ACCENT};
                background: {BG_CARD_H};
            }}
            QPushButton#primary {{
                background: {ACCENT};
                color: white;
                border: none;
                font-weight: 600;
            }}
            QPushButton#primary:hover {{
                background: {ACCENT2};
            }}
        """)

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setFixedWidth(180)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background: {BG_SIDEBAR};
                border-right: 1px solid {BORDER};
            }}
        """)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(12, 20, 12, 20)
        sb_layout.setSpacing(4)

        # App name
        app_name = QLabel("GoodVoice")
        app_name.setFont(QFont(FONT, 16, QFont.Weight.Bold))
        app_name.setStyleSheet(f"color: {TEXT}; padding: 0 4px 12px 4px; border: none;")
        sb_layout.addWidget(app_name)

        # Nav buttons
        self._nav_buttons = []
        pages = ["Основные", "Статистика", "История"]
        for i, name in enumerate(pages):
            btn = SidebarButton(name)
            btn.clicked.connect(lambda checked, idx=i: self._switch_page(idx))
            sb_layout.addWidget(btn)
            self._nav_buttons.append(btn)

        sb_layout.addStretch()

        # Version
        ver = QLabel("v1.0.0")
        ver.setFont(QFont(FONT, 9))
        ver.setStyleSheet(f"color: {TEXT_MUTED}; padding: 0 4px; border: none;")
        sb_layout.addWidget(ver)

        root.addWidget(sidebar)

        # ── Content area ─────────────────────────────────────────
        content = QFrame()
        content.setStyleSheet(f"background: {BG_MAIN}; border: none;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(32, 28, 32, 20)
        content_layout.setSpacing(0)

        # Page title
        self._title = QLabel("Основные")
        self._title.setFont(QFont(FONT, 22, QFont.Weight.Bold))
        self._title.setStyleSheet(f"color: {TEXT}; border: none; margin-bottom: 4px;")
        content_layout.addWidget(self._title)

        subtitle = QLabel("Настройки голосового ввода")
        subtitle.setFont(QFont(FONT, 12))
        subtitle.setStyleSheet(f"color: {TEXT_DIM}; border: none; margin-bottom: 20px;")
        content_layout.addWidget(subtitle)

        # Stacked pages
        self._stack = QStackedWidget()
        self._stack.addWidget(self._create_general_page())
        self._stack.addWidget(self._create_stats_page())
        self._stack.addWidget(self._create_history_page())
        content_layout.addWidget(self._stack, 1)

        # Footer buttons
        footer = QHBoxLayout()
        footer.addStretch()
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.close)
        footer.addWidget(btn_close)
        btn_save = QPushButton("Сохранить")
        btn_save.setObjectName("primary")
        btn_save.setFixedWidth(120)
        btn_save.clicked.connect(self._save)
        footer.addWidget(btn_save)
        content_layout.addLayout(footer)

        root.addWidget(content, 1)

        # Select first page
        self._nav_buttons[0].setChecked(True)

    def _switch_page(self, index: int):
        titles = ["Основные", "Статистика", "История"]
        self._title.setText(titles[index])
        self._stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_buttons):
            btn.setChecked(i == index)

    # ── Pages ────────────────────────────────────────────────────

    def _create_general_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Hotkey card
        frame = card()
        card_layout = QVBoxLayout(frame)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(12)
        card_layout.addLayout(card_row(
            "Горячая клавиша",
            "Комбинация для начала записи голоса"
        ))
        self.combo_hotkey = styled_combo(
            ["Right Alt", "Right Ctrl", "Left Ctrl"],
            "Right Alt" if self.settings.hotkey == "alt_r" else (
                "Right Ctrl" if self.settings.hotkey == "ctrl_r" else "Left Ctrl")
        )
        card_layout.addWidget(self.combo_hotkey)
        layout.addWidget(frame)

        # Trigger mode card
        frame = card()
        card_layout = QVBoxLayout(frame)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(12)
        card_layout.addLayout(card_row(
            "Режим записи",
            "Hold — зажал/говоришь/отпустил. Toggle — нажал/говоришь/нажал"
        ))
        self.combo_mode = styled_combo(
            ["Зажатие (Hold)", "Переключение (Toggle)"],
            "Зажатие (Hold)" if self.settings.trigger_mode == "hold" else "Переключение (Toggle)"
        )
        card_layout.addWidget(self.combo_mode)
        layout.addWidget(frame)

        # Language card
        frame = card()
        card_layout = QVBoxLayout(frame)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(12)
        card_layout.addLayout(card_row(
            "Язык",
            "Язык распознавания речи"
        ))
        lang_map = {"auto": "Auto", "ru": "Russian", "en": "English", "de": "German", "fr": "French", "es": "Spanish"}
        self.combo_lang = styled_combo(
            ["Auto", "Russian", "English", "German", "French", "Spanish"],
            lang_map.get(self.settings.language, "Auto")
        )
        card_layout.addWidget(self.combo_lang)
        layout.addWidget(frame)

        # Punctuation card
        frame = card()
        card_layout = QVBoxLayout(frame)
        card_layout.setContentsMargins(20, 16, 20, 16)
        row = card_row(
            "Пунктуация",
            "Автоматически расставляет запятые и точки"
        )
        self.check_punct = styled_checkbox("", self.settings.punctuation)
        row.addWidget(self.check_punct)
        card_layout.addLayout(row)
        layout.addWidget(frame)

        # Theme card
        frame = card()
        card_layout = QVBoxLayout(frame)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(12)
        card_layout.addLayout(card_row(
            "Тема HUD",
            "Визуальный стиль плавающего окна"
        ))
        self.combo_theme = styled_combo(
            ["hybrid_v2", "google", "google_v2", "hybrid", "vercel"],
            self.settings.hud_theme
        )
        card_layout.addWidget(self.combo_theme)
        layout.addWidget(frame)

        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def _create_stats_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        s = self.stats

        # KPI cards
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)
        kpi_row.addWidget(kpi_card(str(s.total_sessions), "Сессий", ACCENT))
        kpi_row.addWidget(kpi_card(f"{s.total_words:,}", "Слов", GREEN))
        kpi_row.addWidget(kpi_card(f"{s.total_chars:,}", "Символов", CYAN))
        kpi_row.addWidget(kpi_card(f"{s.avg_words:.0f}", "Слов / сессия", YELLOW))
        layout.addLayout(kpi_row)

        # Bar chart
        if HAS_MATPLOTLIB and s.sessions:
            chart_frame = card()
            chart_layout = QVBoxLayout(chart_frame)
            chart_layout.setContentsMargins(20, 16, 20, 16)
            chart_layout.setSpacing(8)
            chart_title = section_title("Активность по дням")
            chart_layout.addWidget(chart_title)

            # Aggregate by day
            daily = defaultdict(int)
            for sess in s.sessions:
                day = datetime.fromtimestamp(sess["timestamp"]).strftime("%d.%m")
                daily[day] += sess.get("word_count", 0)

            days = sorted(daily.keys())[-14:]  # last 14 days
            data = [(d, daily[d]) for d in days]

            chart = BarChart(data)
            chart_layout.addWidget(chart)
            layout.addWidget(chart_frame)
        elif not s.sessions:
            empty = QLabel("Пока нет данных. Начните диктовать!")
            empty.setFont(QFont(FONT, 13))
            empty.setStyleSheet(f"color: {TEXT_DIM}; padding: 40px; border: none;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(empty)

        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def _create_history_page(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        entries = self.history.get_recent(30)

        if not entries:
            empty = QLabel("История пуста")
            empty.setFont(QFont(FONT, 13))
            empty.setStyleSheet(f"color: {TEXT_DIM}; padding: 40px; border: none;")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(empty)
        else:
            for entry in entries:
                item = HistoryItem(entry)
                layout.addWidget(item)

            layout.addSpacing(12)
            btn_clear = QPushButton("Очистить историю")
            btn_clear.clicked.connect(self._clear_history)
            layout.addWidget(btn_clear)

        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def _clear_history(self):
        reply = QMessageBox.question(
            self, "Очистка", "Удалить всю историю?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.history.clear()
            self._stack.removeWidget(self._stack.widget(2))
            self._stack.insertWidget(2, self._create_history_page())
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
