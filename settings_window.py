"""GoodVoice settings GUI panel."""

import sys
import time
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QLabel, QComboBox, QCheckBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from settings import Settings
from stats import Stats
from history import History


class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = Settings().load()
        self.stats = Stats().load()
        self.history = History().load()
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("GoodVoice — Настройки")
        self.setFixedSize(520, 480)

        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(12, 12, 12, 12)

        # Tabs
        tabs = QTabWidget()
        tabs.addTab(self._create_general_tab(), "Основные")
        tabs.addTab(self._create_hud_tab(), "HUD")
        tabs.addTab(self._create_stats_tab(), "Статистика")
        tabs.addTab(self._create_history_tab(), "История")
        layout.addWidget(tabs)

        # Buttons
        btn_row = QHBoxLayout()
        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self._save)
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.close)
        btn_row.addStretch()
        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def _create_general_tab(self):
        w = QWidget()
        layout = QVBoxLayout()

        # Hotkey
        g1 = QGroupBox("Горячая клавиша")
        l1 = QHBoxLayout()
        l1.addWidget(QLabel("Клавиша:"))
        self.combo_hotkey = QComboBox()
        self.combo_hotkey.addItems(["Right Ctrl", "Left Ctrl"])
        self.combo_hotkey.setCurrentText(
            "Right Ctrl" if self.settings.hotkey == "ctrl_r" else "Left Ctrl"
        )
        l1.addWidget(self.combo_hotkey)
        g1.setLayout(l1)
        layout.addWidget(g1)

        # Trigger mode
        g2 = QGroupBox("Режим записи")
        l2 = QHBoxLayout()
        l2.addWidget(QLabel("Режим:"))
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Зажатие (Hold)", "Переключение (Toggle)"])
        self.combo_mode.setCurrentIndex(0 if self.settings.trigger_mode == "hold" else 1)
        l2.addWidget(self.combo_mode)
        g2.setLayout(l2)
        layout.addWidget(g2)

        # Language
        g3 = QGroupBox("Язык")
        l3 = QHBoxLayout()
        l3.addWidget(QLabel("Язык:"))
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["Auto", "Russian", "English", "German", "French", "Spanish"])
        lang_map = {"auto": "Auto", "ru": "Russian", "en": "English", "de": "German", "fr": "French", "es": "Spanish"}
        self.combo_lang.setCurrentText(lang_map.get(self.settings.language, "Auto"))
        l3.addWidget(self.combo_lang)
        g3.setLayout(l3)
        layout.addWidget(g3)

        # Punctuation
        self.check_punct = QCheckBox("Автоматическая пунктуация")
        self.check_punct.setChecked(self.settings.punctuation)
        layout.addWidget(self.check_punct)

        layout.addStretch()
        w.setLayout(layout)
        return w

    def _create_hud_tab(self):
        w = QWidget()
        layout = QVBoxLayout()

        # Theme
        g1 = QGroupBox("Тема интерфейса")
        l1 = QHBoxLayout()
        l1.addWidget(QLabel("Тема:"))
        self.combo_theme = QComboBox()
        self.combo_theme.addItems(["hybrid_v2", "google", "google_v2", "hybrid", "vercel"])
        self.combo_theme.setCurrentText(self.settings.hud_theme)
        l1.addWidget(self.combo_theme)
        g1.setLayout(l1)
        layout.addWidget(g1)

        layout.addStretch()
        w.setLayout(layout)
        return w

    def _create_stats_tab(self):
        w = QWidget()
        layout = QVBoxLayout()

        g = QGroupBox("Статистика")
        gl = QVBoxLayout()

        s = self.stats
        gl.addWidget(QLabel(f"Всего сессий: {s.total_sessions}"))
        gl.addWidget(QLabel(f"Всего слов: {s.total_words:,}"))
        gl.addWidget(QLabel(f"Всего символов: {s.total_chars:,}"))
        gl.addWidget(QLabel(f"Средняя длина: {s.avg_words:.1f} слов"))

        g.setLayout(gl)
        layout.addWidget(g)
        layout.addStretch()
        w.setLayout(layout)
        return w

    def _create_history_tab(self):
        w = QWidget()
        layout = QVBoxLayout()

        entries = self.history.get_recent(20)

        self.table = QTableWidget(len(entries), 3)
        self.table.setHorizontalHeaderLabels(["Время", "Текст", "Слов"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        for i, entry in enumerate(entries):
            ts = datetime.fromtimestamp(entry["timestamp"]).strftime("%H:%M")
            text = entry["text"][:60] + ("..." if len(entry["text"]) > 60 else "")
            words = str(entry["word_count"])
            self.table.setItem(i, 0, QTableWidgetItem(ts))
            self.table.setItem(i, 1, QTableWidgetItem(text))
            self.table.setItem(i, 2, QTableWidgetItem(words))

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
        # Save settings
        self.settings.hotkey = "ctrl_r" if self.combo_hotkey.currentText() == "Right Ctrl" else "ctrl_l"
        self.settings.trigger_mode = "hold" if self.combo_mode.currentIndex() == 0 else "toggle"
        lang_rev = {"Auto": "auto", "Russian": "ru", "English": "en", "German": "de", "French": "fr", "Spanish": "es"}
        self.settings.language = lang_rev.get(self.combo_lang.currentText(), "auto")
        self.settings.punctuation = self.check_punct.isChecked()
        self.settings.hud_theme = self.combo_theme.currentText()
        self.settings.save()
        self.close()


def open_settings():
    """Open settings window (non-blocking)."""
    win = SettingsWindow()
    win.show()
    return win
