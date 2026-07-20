# GoodVoice

Быстрый голосовой ввод для Windows с использованием Whisper.

## Установка

```powershell
cd "C:\Users\Евгений\Desktop\Projects\goodvoice"
pip install -r requirements.txt
```

## Запуск

```powershell
python main.py
```

## Использование

- **Left Ctrl (зажать)** — начать запись, отпустить — текст вводится
- **Left Ctrl (нажать)** — toggle режим (если включён в настройках)
- **Escape** — отмена текущей записи
- **ПКМ по иконке в трее** — настройки, выход

## Настройки

Файл: `~/Documents/goodvoice/settings.json`

| Параметр | По умолчанию | Описание |
|----------|-------------|----------|
| model_size | medium | Размер модели Whisper (tiny/base/small/medium/large-v3) |
| language | auto | Язык (auto/ru/en/de/...) |
| trigger_mode | hold | Режим триггера (hold/toggle) |
| punctuation | true | Автоматическая пунктуация |
| hud_position | center | Позиция HUD (center/cursor) |
| autostart | false | Автозапуск с Windows |

## Архитектура

```
goodvoice/
├── main.py              # Точка входа
├── audio_recorder.py    # Запись аудио (sounddevice)
├── transcriber.py       # Распознавание (faster-whisper)
├── text_inserter.py     # Вставка текста (clipboard + Ctrl+V)
├── hotkey_manager.py    # Горячие клавиши (pynput)
├── hud_window.py        # Плавающее окно (customtkinter)
├── tray_icon.py         # Системный трей (pystray)
├── settings.py          # Настройки (JSON)
├── assets/
│   └── mic.png          # Иконка микрофона
└── requirements.txt
```

## Зависимости

- Python 3.10+
- faster-whisper (быстрое распознавание речи)
- customtkinter (современный UI)
- pynput (глобальные горячие клавиши)
- sounddevice (запись аудио)
- pyperclip + pyautogui (вставка текста)
- pystray (системный трей)
- Pillow (иконки)
