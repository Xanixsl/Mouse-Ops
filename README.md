<div align="center">

# 🖱️ Mouse Ops

### Universal Mouse & Keyboard Automation Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![Version](https://img.shields.io/badge/version-B--1.0-purple.svg)](../../releases)

![Visits](https://hitscounter.dev/api/hit?url=https%3A%2F%2Fgithub.com%2FXanixsl%2FMouse-Ops&label=Visits&icon=github&color=%237c5cfc)
[![Downloads](https://img.shields.io/github/downloads/Xanixsl/Mouse-Ops/total?label=Downloads&style=flat-square&color=00d4aa)](../../releases)

**[English](#english)** | [Русский](docs/ru/README.md)

</div>

---

## 📖 About

Modern automation tool for Windows with advanced mouse and keyboard control. Built for gamers, streamers, and productivity users.

## ✨ Features

- 🎯 **Auto-clicker** — Customizable CPS, left/right mouse button
- ⌨️ **Hotkeys** — Flexible configuration (F6, F7, ESC)
- 🎨 **Modern UI** — Dark theme with glassmorphism effects
- 🌍 **Multi-language** — English and Russian
- 🔊 **Sound Feedback** — Audio notifications
- 📊 **Statistics** — Real-time click tracking
- 🎲 **Humanization** — Natural mouse movement simulation
- 💾 **Auto-save** — Settings persistence
- 🖼️ **System Tray** — Background operation

## 🚀 Installation

### Download EXE (Recommended)

1. Go to [Releases](../../releases)
2. Download and extract archive
3. Run `MouseOps.exe`

### Run from Source

```bash
git clone https://github.com/Xanixsl/Mouse-Ops.git
cd Mouse-Ops
pip install -r requirements.txt
python main.py
```

## 📦 Requirements

- Windows 10/11 (64-bit)
- Python 3.8+ (for source)

## 🎮 Default Hotkeys

| Key | Action |
|-----|--------|
| `F6` | Toggle auto-clicker |
| `F7` | Show/Hide window |
| `ESC` | Emergency stop |

## 🛠️ Technical Details

**Built with:**
- Python 3.8+
- Tkinter (GUI)
- pynput (automation)
- sv-ttk (dark theme)

**Dependencies:**
```
pynput>=1.7.6
sv-ttk>=2.6.0
darkdetect>=0.8.0
Pillow>=10.0.0
pystray>=0.19.4
```

## 📁 Structure

```
Mouse-Ops/
├── main.py           # Main application (3491 lines)
├── ui/               # UI components (theme, window)
├── utils/            # Utilities (helpers, sound)
└── locales/          # Translations (en, ru)
```

## 📜 License

MIT License - see [LICENSE](LICENSE) | [Russian version](docs/ru/LICENSE.md)

## 🤝 Contributing

Contributions welcome! Read [CONTRIBUTING.md](CONTRIBUTING.md) | [Russian version](docs/ru/CONTRIBUTING.md)

## 🐛 Bug Reports

[Open an issue](../../issues/new) with OS version, steps to reproduce, and screenshots.

## 💖 Support the Project

If you find this project useful, consider buying me a coffee:

<div align="center">

[![DonationAlerts](https://img.shields.io/badge/Donate-DonationAlerts-FF4500?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMTUuMDkgOC4yNkwyMiA5LjI3TDE3IDEzLjE0TDE4LjE4IDIyTDEyIDE4LjI3TDUuODIgMjJMNyAxMy4xNEwyIDkuMjdMOC45MSA4LjI2TDEyIDJaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4=)](https://www.donationalerts.com/r/saylont)
[![Boosty](https://img.shields.io/badge/Donate-Boosty-8A2BE2?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDIyQzE3LjUyMjggMjIgMjIgMTcuNTIyOCAyMiAxMkMyMiA2LjQ3NzE1IDE3LjUyMjggMiAxMiAyQzYuNDc3MTUgMiAyIDYuNDc3MTUgMiAxMkMyIDE3LjUyMjggNi40NzcxNSAyMiAxMiAyMloiIGZpbGw9IndoaXRlIi8+Cjwvc3ZnPg==)](https://boosty.to/saylontoff/donate)

</div>

---

<div align="center">

**Made with ❤️ by Mouse Ops Team**

⭐ Star this repo if you find it useful!

</div>

## 🔧 Зависимости

```
tkinter (встроен в Python)
sv-ttk
darkdetect
pynput
pystray (опционально)
Pillow (опционально)
```

## 📝 Изменения

### Версия B-2.0 (2025)
- ✨ Полностью переработанный модерный дизайн
- 📦 Модульная структура проекта
- 🎨 Тема в стиле 2025-2026 (glassmorphism, градиенты)
- 🔧 Улучшенная архитектура кода
- 🎯 Сохранена вся функциональность оригинала

### Версия B-1.0 (2024)
- Удален пиксельный триггер
- Удалена светлая тема
- Язык по умолчанию EN
- Базовый современный дизайн

## 🎯 Рекомендации

- Используйте **main.py** для полного функционала (макросы, координаты, профили, etc.)
- Используйте **main_modern.py** для простого и быстрого автокликера с крутым дизайном
- Оба файла используют одни и те же модули из `utils/` и `ui/`

## 📧 Контакты

TikTok: [@saylont](https://www.tiktok.com/@saylont)
GitHub: [Xanixsl/Mouse-Ops](https://github.com/Xanixsl/Mouse-Ops)
