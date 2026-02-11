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

**Mouse Ops** is a powerful automation tool for Windows with advanced mouse and keyboard control capabilities. Features include auto-clicker, macro recorder, multi-point routes, drag & drop automation, and human-like movement simulation.

## ✨ Key Features

### 🎯 Auto-Clicker
- Customizable click speed (CPS)
- Left/Right/Middle mouse buttons
- Double-click mode
- Fixed position clicking
- Action limit counter

### ⌨️ Hotkey System
- Customizable global hotkeys (F1-F12)
- Toggle activation (F6 default)
- Show/Hide window (F7 default)
- Emergency stop (ESC)

### 🎬 Macro Recording  
- Record mouse clicks and keyboard actions
- Playback recorded sequences
- Save/Load macro profiles
- Custom delays between actions

### 🗺️ Multi-Point Routes
- Create click routes with multiple coordinates
- Set custom delays per point
- Different actions at each point
- Loop through routes automatically

### 🖱️ Drag & Drop Automation
- Automated drag operations
- Custom start/end coordinates
- Adjustable drag speed

### 🎲 Human-Like Behavior
- Natural mouse movement curves
- Hand tremor simulation
- Random micro-movements
- Variable click pressure
- Fatigue simulation
- Speed variation
- Random pauses
- Overshoot effects

### 🔧 Additional Features
- 📊 **Statistics** — Real-time action tracking and logs
- 🔊 **Sound Feedback** — Audio notifications with volume control
- 💾 **Profiles** — Save/Load different configurations
- 🌍 **Multi-language** — English and Russian
- 🎨 **Modern UI** — Dark theme with glassmorphism effects
- 🖼️ **System Tray** — Background operation support
- 🎯 **Coordinate Picker** — Visual coordinate selection
- ⏱️ **Timer** — Run for specific duration
- 🚫 **Anti-AFK** — Random movements to prevent idle

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

## 📦 System Requirements

- **OS**: Windows 10/11 (64-bit)
- **Python**: 3.8+ (for source)
- **RAM**: 100 MB minimum
- **Storage**: 50 MB free space

## 🎮 Default Hotkeys

| Key | Action |
|-----|--------|
| `F6` | Start/Stop automation |
| `F7` | Show/Hide window |
| `ESC` | Emergency stop & cancel selection |

## 🛠️ Technical Stack

**Core:**
- Python 3.8+
- Tkinter (GUI framework)
- pynput (mouse/keyboard automation)
- sv-ttk (modern dark theme)
- darkdetect (system theme detection)

**Optional:**
- pystray (system tray support)
- Pillow (tray icon generation)

**Dependencies:**
```
pynput>=1.7.6
sv-ttk>=2.6.0
darkdetect>=0.8.0
Pillow>=10.0.0
pystray>=0.19.4
```

## 📁 Project Structure

```
Mouse-Ops/
├── main.py              # Main application (3491 lines)
│
├── ui/                  # UI components
│   ├── __init__.py
│   ├── theme.py         # Modern theme styles
│   └── window.py        # Window management
│
├── utils/               # Utility modules
│   ├── __init__.py
│   ├── helpers.py       # HumanNoise, ToolTip
│   └── sound.py         # Sound manager
│
└── locales/             # Translations
    ├── en.json          # English
    └── ru.json          # Russian
```

## 🎨 Design Features

**Modern 2025-2026 Color Palette:**
- Electric Purple (#7c5cfc) — Primary accent
- Mint Teal (#00d4aa) — Success states
- Coral Pink (#ff6b9d) — Action buttons
- Dark backgrounds with gradients
- Glassmorphism effects with transparency
- Smooth animations and transitions

## 💡 Usage Examples

### Basic Auto-Clicker
1. Set click delay (e.g., 50ms)
2. Select mouse button (left/right/middle)
3. Press F6 to start
4. Press F6 again or ESC to stop

### Macro Recording
1. Switch to "Macros" tab
2. Click "Start Recording"
3. Perform actions (clicks, keyboard)
4. Click "Stop Recording"
5. Save macro with a name
6. Press F6 to replay

### Multi-Point Route
1. Go to "Routes" tab
2. Click "Add Point" and select coordinates
3. Set delay and action for each point
4. Click "Start Route"
5. Route will loop through all points

### Human-Like Clicking
1. Enable "Human-like behavior"
2. Adjust sliders:
   - Curviness (movement curves)
   - Hand Tremor (natural shake)
   - Micro-movements (small jitters)
   - Speed Variation (variable timing)
3. Start automation

## 🔧 Configuration

Settings are automatically saved to:
```
%TEMP%\mouse_ops_v5_config.json
%TEMP%\mouse_ops_v5_profiles.json
%TEMP%\mouse_ops_v5_macros.json
%TEMP%\mouse_ops_v5_coords.json
```

## 📜 License

MIT License - see [LICENSE](LICENSE)

**Russian version:** [docs/ru/LICENSE.md](docs/ru/LICENSE.md)

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Russian version:** [docs/ru/CONTRIBUTING.md](docs/ru/CONTRIBUTING.md)

## 🐛 Bug Reports & Feature Requests

[Open an issue](../../issues/new) with details:
- OS version and Python version
- Steps to reproduce
- Expected vs actual behavior
- Screenshots or error logs

## 💖 Support the Project

If you find Mouse Ops useful, consider supporting development:

<div align="center">

[![DonationAlerts](https://img.shields.io/badge/Donate-DonationAlerts-FF4500?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDJMMTUuMDkgOC4yNkwyMiA5LjI3TDE3IDEzLjE0TDE4LjE4IDIyTDEyIDE4LjI3TDUuODIgMjJMNyAxMy4xNEwyIDkuMjdMOC45MSA4LjI2TDEyIDJaIiBmaWxsPSJ3aGl0ZSIvPgo8L3N2Zz4=)](https://www.donationalerts.com/r/saylont)
[![Boosty](https://img.shields.io/badge/Donate-Boosty-8A2BE2?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEyIDIyQzE3LjUyMjggMjIgMjIgMTcuNTIyOCAyMiAxMkMyMiA2LjQ3NzE1IDE3LjUyMjggMiAxMiAyQzYuNDc3MTUgMiAyIDYuNDc3MTUgMiAxMkMyIDE3LjUyMjggNi40NzcxNSAyMiAxMiAyMloiIGZpbGw9IndoaXRlIi8+Cjwvc3ZnPg==)](https://boosty.to/saylontoff/donate)

</div>
