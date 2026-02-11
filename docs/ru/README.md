<div align="center">

# 🖱️ Mouse Ops

### Универсальный инструмент автоматизации мыши и клавиатуры

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.md)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![Version](https://img.shields.io/badge/version-B--1.0-purple.svg)](../../../../releases)

![Visits](https://hitscounter.dev/api/hit?url=https%3A%2F%2Fgithub.com%2FXanixsl%2FMouse-Ops&label=Visits&icon=github&color=%237c5cfc)
[![Downloads](https://img.shields.io/github/downloads/Xanixsl/Mouse-Ops/total?label=Downloads&style=flat-square&color=00d4aa)](../../../../releases)

[English](../../README.md) | **[Русский](#russian)**

</div>

---

## 📖 Описание

Современный инструмент автоматизации для Windows с продвинутыми функциями управления мышью и клавиатурой. Создан для геймеров, стримеров и всех, кто ценит продуктивность.

## ✨ Возможности

- 🎯 **Автокликер** — настраиваемая частота кликов (CPS), левая/правая кнопка
- ⌨️ **Горячие клавиши** — гибкая настройка (F6, F7, ESC)
- 🎨 **Современный UI** — темная тема с эффектами glassmorphism
- 🌍 **Мультиязычность** — английский и русский языки
- 🔊 **Звуковая обратная связь** — аудио уведомления
- 📊 **Статистика** — отслеживание кликов в реальном времени
- 🎲 **Гуманизация** — имитация естественных движений мыши
- 💾 **Автосохранение** — сохранение настроек между сессиями
- 🖼️ **Системный трей** — работа в фоновом режиме

## 🚀 Установка

### Скачать EXE (Рекомендуется)

1. Перейдите в [Releases](../../../../releases)
2. Скачайте и распакуйте архив
3. Запустите `MouseOps.exe`

### Запуск из исходников

```bash
git clone https://github.com/Xanixsl/Mouse-Ops.git
cd Mouse-Ops
pip install -r requirements.txt
python main.py
```

## 📦 Требования

- Windows 10/11 (64-bit)
- Python 3.8+ (для запуска из исходников)

## 🎮 Горячие клавиши

| Клавиша | Действие |
|---------|----------|
| `F6` | Включить/выключить автокликер |
| `F7` | Показать/скрыть окно |
| `ESC` | Экстренная остановка |

## 🛠️ Технические детали

**Основано на:**
- Python 3.8+
- Tkinter (GUI)
- pynput (автоматизация)
- sv-ttk (темная тема)

**Зависимости:**
```
pynput>=1.7.6
sv-ttk>=2.6.0
darkdetect>=0.8.0
Pillow>=10.0.0
pystray>=0.19.4
```

## 📁 Структура

```
Mouse-Ops/
├── main.py           # Основное приложение (3491 строк)
├── ui/               # UI компоненты (тема, окно)
├── utils/            # Утилиты (helpers, звук)
└── locales/          # Переводы (en, ru)
```

## 📜 Лицензия

MIT License - см. [LICENSE](../../LICENSE) | [Русская версия](LICENSE.md)

## 🤝 Участие

Приветствуются улучшения! Читайте [CONTRIBUTING.md](../../CONTRIBUTING.md) | [Русская версия](CONTRIBUTING.md)

## 🐛 Сообщения об ошибках

[Откройте issue](../../../../issues/new) с указанием версии ОС, шагов воспроизведения и скриншотов.

## 💖 Поддержать проект

Если проект полезен, поддержите автора кофе:

<div align="center">

[![DonationAlerts](https://img.shields.io/badge/Donate-DonationAlerts-FF4500?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMTUuMDkgOC4yNkwyMiA5LjI3TDE3IDEzLjE0TDE4LjE4IDIyTDEyIDE4LjI3TDUuODIgMjJMNyAxMy4xNEwyIDkuMjdMOC45MSA4LjI2TDEyIDJaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4=)](https://www.donationalerts.com/r/saylont)
[![Boosty](https://img.shields.io/badge/Donate-Boosty-8A2BE2?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDIyQzE3LjUyMjggMjIgMjIgMTcuNTIyOCAyMiAxMkMyMiA2LjQ3NzE1IDE3LjUyMjggMiAxMiAyQzYuNDc3MTUgMiAyIDYuNDc3MTUgMiAxMkMyIDE3LjUyMjggNi40NzcxNSAyMiAxMiAyMloiIGZpbGw9IndoaXRlIi8+Cjwvc3ZnPg==)](https://boosty.to/saylontoff/donate)

</div>

---

<div align="center">

**Сделано с ❤️ командой Mouse Ops**

⭐ Поставьте звезду, если проект полезен!

</div>
