"""GoodVoice settings — modern dark UI inspired by SuperDictate."""

import sys
import time
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QComboBox, QCheckBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QMessageBox, QApplication, QFrame,
    QGridLayout, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor, QIcon

from settings import Settings
from stats import Stats
from history import History


# ── Design tokens ────────────────────────────────────────────────

BG = "#0D0D11"
BG_CARD = "#16161E"
BG_HOVER = "#1E1E2E"
BORDER = "#2A2A3A"
TEXT = "#E0E0E0"
TEXT_DIM = "#7A7A8A"
ACCENT = "#8B5CF6"      # violet
ACCENT2 = "#06B6D4"     # cyan
GREEN = "#22C55E"
RED = "#EF4444"
YELLOW = "#EAB308"
FONT = "Segoe UI"
FONT_MONO = "Consolas"


def make_card(title: str = None) -> QVBoxLayout:
    """Create a styled card layout."""
    frame = QFrame()
    frame.setStyleSheet(f"""
        QFrame {{
            background-color: {BG_CARD};
            border: 1px solid {BORDER};
            border-radius: 12px;
            padding: 16px;
        }}
    """)
    layout = QVBoxLayout(frame)
    layout.setSpacing(10)
    if title:
        lbl = QLabel(title)
        lbl.setFont(QFont(FONT, 13, QFont.Weight.DemiBold))
        lbl.setStyleSheet(f"color: {TEXT}; background: transparent; border: none;")
        layout.addWidget(lbl)
    return layout, frame


def stat_label(value: str, color: str = TEXT) -> QLabel:
    lbl = QLabel(value)
    lbl.setFont(QFont(FONT_MONO, 18, QFont.Weight.Bold))
    lbl.setStyleSheet(f"color: {color}; background: transparent; border: none;")
    return lbl


def dim_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(QFont(FONT, 10))
    lbl.setStyleSheet(f"color: {TEXT_DIM}; background: transparent; border: none;")
    return lbl


class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = Settings().load()
        self.stats = Stats().load()
        self.history = History().load()
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("GoodVoice — Настройки")
        self.setFixedSize(540, 520)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {BG};
                color: {TEXT};
                font-family: {FONT};
            }}
            QTabWidget::pane {{
                border: 1px solid {BORDER};
                border-radius: 8px;
                background: {BG};
            }}
            QTabBar::tab {{
                background: {BG_CARD};
                color: {TEXT_DIM};
                padding: 10px 20px;
                border: 1px solid {BORDER};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 12px;
                font-weight: 500;
            }}
            QTabBar::tab:selected {{
                background: {BG};
                color: {ACCENT};
                border-bottom: 2px solid {ACCENT};
            }}
            QComboBox {{
                background: {BG_CARD};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 12px;
                min-width: 160px;
            }}
            QComboBox:hover {{
                border-color: {ACCENT};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox QAbstractItemView {{
                background: {BG_CARD};
                color: {TEXT};
                border: 1px solid {BORDER};
                selection-background-color: {ACCENT};
                border-radius: 8px;
            }}
            QCheckBox {{
                color: {TEXT};
                font-size: 12px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {BORDER};
                border-radius: 4px;
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
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                border-color: {ACCENT};
                background: {BG_HOVER};
            }}
            QPushButton:pressed {{
                background: {ACCENT};
                color: white;
            }}
            QTableWidget {{
                background: {BG_CARD};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 8px;
                gridline-color: {BORDER};
                font-size: 11px;
            }}
            QTableWidget::item {{
                padding: 6px 8px;
                border: none;
            }}
            QTableWidget::item:selected {{
                background: {ACCENT}33;
            }}
            QHeaderView::section {{
                background: {BG_CARD};
                color: {TEXT_DIM};
                border: none;
                border-bottom: 1px solid {BORDER};
                padding: 8px;
                font-size: 11px;
                font-weight: 600;
            }}
            QGroupBox {{
                border: 1px solid {BORDER};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 16px;
                font-size: 12px;
                font-weight: 600;
                color: {TEXT_DIM};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Title
        title = QLabel("GoodVoice")
        title.setFont(QFont(FONT, 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {TEXT}; background: transparent;")
        layout.addWidget(title)

        subtitle = dim_label("Настройки голосового ввода")
        layout.addWidget(subtitle)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._create_general_tab(), "Основные")
        tabs.addTab(self._create_stats_tab(), "Статистика")
        tabs.addTab(self._create_history_tab(), "История")
        layout.addWidget(tabs)

        # Footer
        footer = QHBoxLayout()
        footer.addStretch()
        btn_save = QPushButton("Сохранить")
        btn_save.setFixedWidth(100)
        btn_save.clicked.connect(self._save)
        footer.addWidget(btn_save)
        layout.addLayout(footer)

        self.setLayout(layout)

    def _create_general_tab(self):
        w = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)

        # Hotkey card
        card, frame = make_card("Горячая клавиша")
        row = QHBoxLayout()
        row.addWidget(dim_label("Клавиша"))
        row.addStretch()
        self.combo_hotkey = QComboBox()
        self.combo_hotkey.addItems(["Right Alt", "Right Ctrl", "Left Ctrl"])
        current = "Right Alt" if self.settings.hotkey == "alt_r" else (
            "Right Ctrl" if self.settings.hotkey == "ctrl_r" else "Left Ctrl")
        self.combo_hotkey.setCurrentText(current)
        row.addWidget(self.combo_hotkey)
        card.addLayout(row)
        layout.addWidget(frame)

        # Trigger mode card
        card, frame = make_card("Режим записи")
        row = QHBoxLayout()
        row.addWidget(dim_label("Режим"))
        row.addStretch()
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Зажатие (Hold)", "Переключение (Toggle)"])
        self.combo_mode.setCurrentIndex(0 if self.settings.trigger_mode == "hold" else 1)
        row.addWidget(self.combo_mode)
        card.addLayout(row)
        layout.addWidget(frame)

        # Language card
        card, frame = make_card("Язык")
        row = QHBoxLayout()
        row.addWidget(dim_label("Язык распознавания"))
        row.addStretch()
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["Auto", "Russian", "English", "German", "French", "Spanish"])
        lang_map = {"auto": "Auto", "ru": "Russian", "en": "English", "de": "German", "fr": "French", "es": "Spanish"}
        self.combo_lang.setCurrentText(lang_map.get(self.settings.language, "Auto"))
        row.addWidget(self.combo_lang)
        card.addLayout(row)
        layout.addWidget(frame)

        # Punctuation
        self.check_punct = QCheckBox("Автоматическая пунктуация")
        self.check_punct.setChecked(self.settings.punctuation)
        layout.addWidget(self.check_punct)

        # Theme card
        card, frame = make_card("Тема HUD")
        row = QHBoxLayout()
        row.addWidget(dim_label("Тема интерфейса"))
        row.addStretch()
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["hybrid_v2", "google", "google_v2", "hybrid", "vercel"])
        self.combo_theme.setCurrentText(self.settings.hud_theme)
        row.addWidget(self.combo_theme)
        card.addLayout(row)
        layout.addWidget(frame)

        layout.addStretch()
        w.setLayout(layout)
        return w

    def _create_stats_tab(self):
        w = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)

        s = self.stats

        # Stats cards grid
        grid = QGridLayout()
        grid.setSpacing(10)

        # Sessions
        card, frame = make_card()
        card.addWidget(stat_label(str(s.total_sessions), ACCENT))
        card.addWidget(dim_label("Сессий"))
        grid.addWidget(frame, 0, 0)

        # Words
        card, frame = make_card()
        card.addWidget(stat_label(f"{s.total_words:,}", GREEN))
        card.addWidget(dim_label("Слов"))
        grid.addWidget(frame, 0, 1)

        # Chars
        card, frame = make_card()
        card.addWidget(stat_label(f"{s.total_chars:,}", ACCENT2))
        card.addWidget(dim_label("Символов"))
        grid.addWidget(frame, 1, 0)

        # Avg
        card, frame = make_card()
        card.addWidget(stat_label(f"{s.avg_words:.0f}", YELLOW))
        card.addWidget(dim_label("Слов / сессия"))
        grid.addWidget(frame, 1, 1)

        layout.addLayout(grid)
        layout.addStretch()
        w.setLayout(layout)
        return w

    def _create_history_tab(self):
        w = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)

        entries = self.history.get_recent(20)

        self.table = QTableWidget(len(entries), 3)
        self.table.setHorizontalHeaderLabels(["Время", "Текст", "Слов"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)

        for i, entry in enumerate(entries):
            ts = datetime.fromtimestamp(entry["timestamp"]).strftime("%H:%M")
            text = entry["text"][:80] + ("..." if len(entry["text"]) > 80 else "")
            words = str(entry["word_count"])

            time_item = QTableWidgetItem(ts)
            time_item.setForeground(QColor(TEXT_DIM))
            text_item = QTableWidgetItem(text)
            words_item = QTableWidgetItem(words)
            words_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.table.setItem(i, 0, time_item)
            self.table.setItem(i, 1, text_item)
            self.table.setItem(i, 2, words_item)

        layout.addWidget(self.table)

        btn_clear = QPushButton("Очистить историю")
        btn_clear.clicked.connect(self._clear_history)
        layout.addWidget(btn_clear)

        w.setLayout(layout)
        return w

    def _clear_history(self):
        reply = QMessageBox.question(
            self, "Очистка", "Удалить всю историю?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.history.clear()
            self.table.setRowCount(0)

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
