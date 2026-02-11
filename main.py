# ═══════════════════════════════════════════════════════════════════════════════
# Mouse Ops — универсальный инструмент автоматизации мыши и клавиатуры
# Репозиторий: https://github.com/Xanixsl/Mouse-Ops
#
# Схема версионирования:
#   A — alpha   (ранняя, нестабильная, фичи сырые)
#   P — Pre-release / preview (промежуточный этап, ближе к бете)
#   B — beta    (фичи в основном готовы, фокус на багах и стабилизации)
#   R — release (финальная стабильная версия)
#
# Текущая версия: B-1.0 (beta - major redesign)
#   Изменения: удален пиксельный триггер, удалена светлая тема,
#   язык по умолчанию EN, современный дизайн, сохранение языка
# ═══════════════════════════════════════════════════════════════════════════════

import os
import sys
import json
import math
import time
import random
import ctypes
import struct
import threading
import tempfile
import webbrowser
import winsound
import io
import wave
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog, colorchooser
from datetime import datetime
from collections import deque

import sv_ttk
import darkdetect
from pynput.mouse import Controller as MouseController, Button, Listener as MouseListener
from pynput import keyboard as pynput_keyboard
from pynput.keyboard import Controller as KeyboardController, Listener as KBListener

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False


# ─────────────────────────────────────────────────────────────────────────────
# Вспомогательные классы
# ─────────────────────────────────────────────────────────────────────────────

class ToolTip:
    def __init__(self, widget, text, delay=400):
        self.widget = widget
        self.text = text
        self._id = None
        self._win = None
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._cancel)
        widget.bind("<ButtonPress>", self._cancel)

    def _schedule(self, event=None):
        self._cancel()
        self._id = self.widget.after(400, self._show)

    def _cancel(self, event=None):
        if self._id:
            self.widget.after_cancel(self._id)
            self._id = None
        if self._win:
            try:
                self._win.destroy()
            except Exception:
                pass
            self._win = None

    def _show(self):
        dark = darkdetect.isDark()
        bg = "#1a1a2e" if dark else "#ffffd0"
        fg = "#e8e8f0" if dark else "#1a1a1a"
        try:
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        except Exception:
            return
        self._win = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(tw, text=self.text, justify="left", bg=bg, fg=fg,
                 relief="flat", borderwidth=0, font=("Segoe UI", 9),
                 wraplength=300, padx=10, pady=6).pack()


class HumanNoise:
    def __init__(self, octaves=4, seed=None):
        self.octaves = octaves
        rng = random.Random(seed)
        self._phases = [rng.uniform(0, 2 * math.pi) for _ in range(octaves)]
        self._freqs = [rng.uniform(0.3, 1.5) * (i + 1) for i in range(octaves)]
        self._amps = [1.0 / (i + 1) for i in range(octaves)]

    def value(self, t: float) -> float:
        total = sum(a * math.sin(f * t + p)
                    for a, f, p in zip(self._amps, self._freqs, self._phases))
        return total / sum(self._amps)


# ─────────────────────────────────────────────────────────────────────────────
# Главный класс
# ─────────────────────────────────────────────────────────────────────────────

class MouseOpsApp:
    VERSION = "B-1.0"
    CFG_FILE = os.path.join(tempfile.gettempdir(), "mouse_ops_v5_config.json")
    PROFILES_FILE = os.path.join(tempfile.gettempdir(), "mouse_ops_v5_profiles.json")
    COORDS_HISTORY_FILE = os.path.join(tempfile.gettempdir(), "mouse_ops_v5_coords.json")
    MACROS_FILE = os.path.join(tempfile.gettempdir(), "mouse_ops_v5_macros.json")

    DEFAULTS = {
        "hotkey": "F6", "radius": "30", "mouse_delay": "60",
        "movement_type": "free", "auto_clicker": True,
        "click_delay": "50", "action_type": "left", "kb_key": "space",
        "double_click": False, "fixed_click": False,
        "fixed_x": "0", "fixed_y": "0",
        "hours": "", "minutes": "", "seconds": "",
        "human_like": False, "human_delay_variation": "25",
        "human_pos_variation": "5", "curviness": 5, "hand_tremor": 3,
        "click_pressure": 5, "random_pauses": 3,
        "fatigue": 3, "overshoot": 4, "micro_movements": 3,
        "speed_variation": 5,
        "language": "en",
        "coord_select_button": "left",
        "sound_enabled": True, "action_limit_enabled": True,
        "action_limit_count": "5",
        "anti_afk": False, "anti_afk_interval": "30",
        "drag_enabled": False,
        "drag_start_x": "0", "drag_start_y": "0",
        "drag_end_x": "0", "drag_end_y": "0",
        "tray_enabled": False,
        "tray_start_minimized": False,
        "tray_show_startstop": True,
        "tray_show_coords": False,
        "sound_volume": 50,
    }

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"Mouse Ops v{self.VERSION}")
        self.root.geometry("1040x840")
        self.root.minsize(920, 760)
        self.root.resizable(True, True)
        self._set_icon()

        # ── Язык / локаль ──
        self.current_language = self.DEFAULTS["language"]
        self._locale = {}
        # Предварительно прочитать язык из конфига ДО построения интерфейса
        try:
            if os.path.exists(self.CFG_FILE):
                with open(self.CFG_FILE, "r", encoding="utf-8") as _cf:
                    _saved = json.load(_cf)
                    if "language" in _saved:
                        self.current_language = _saved["language"]
        except Exception:
            pass
        self._load_locale()

        # Set dark theme only
        sv_ttk.set_theme("dark")
        self.current_theme = "dark"

        self.mouse = MouseController()
        self.kb_ctrl = KeyboardController()

        # ── Состояние ──
        self.is_running = False
        self.stop_event = threading.Event()
        self.hotkey = pynput_keyboard.Key.f6
        self.cursor_locked = False
        self.duration = None

        # ── Базовые tk-переменные ──
        self.auto_clicker_enabled = tk.BooleanVar(value=True)
        self.action_type = tk.StringVar(value="left")
        self.kb_key_var = tk.StringVar(value="space")
        self.double_click_enabled = tk.BooleanVar(value=False)
        self.fixed_click_enabled = tk.BooleanVar(value=False)
        self.fixed_x = tk.StringVar(value="0")
        self.fixed_y = tk.StringVar(value="0")
        self.human_like_enabled = tk.BooleanVar(value=False)
        self._save_timer = None  # для дебаунса сохранения
        self._applying_config = False  # блокировка сохранения при применении профиля
        self.human_delay_variation = tk.StringVar(value="25")
        self.human_pos_variation = tk.StringVar(value="5")
        self.curviness = tk.IntVar(value=5)
        self.hand_tremor = tk.IntVar(value=3)
        self.click_pressure = tk.IntVar(value=5)
        self.random_pauses = tk.IntVar(value=3)
        self.fatigue_level = tk.IntVar(value=3)
        self.overshoot_level = tk.IntVar(value=4)
        self.micro_movements_level = tk.IntVar(value=3)
        self.speed_variation_level = tk.IntVar(value=5)
        self.coord_select_button = tk.StringVar(value="left")
        self.movement_var = tk.StringVar(value="free")

        # ── Координаты ──
        self.coords_select_mode = False
        self.coords_set = False
        self._coord_windows = []
        self.coords_history = []

        # ── Имитация человека ──
        self._noise_x = HumanNoise(seed=42)
        self._noise_y = HumanNoise(seed=137)
        self._fatigue_factor = 1.0
        self._action_count = 0

        # ── Профили ──
        self.current_profile = self._t("profile.default")
        self.profiles = {}

        # ── НОВОЕ v4: Звук ──
        self.sound_enabled = tk.BooleanVar(value=True)
        self.sound_volume = tk.IntVar(value=50)

        # ── НОВОЕ v4: Счётчик повторений ──
        self.action_limit_enabled = tk.BooleanVar(value=True)
        self.action_limit_count = tk.StringVar(value="5")
        self._total_actions_done = 0

        # ── НОВОЕ v4: Anti-AFK ──
        self.anti_afk_enabled = tk.BooleanVar(value=False)
        self.anti_afk_interval = tk.StringVar(value="30")

        # ── НОВОЕ v4: Drag & Drop ──
        self.drag_enabled = tk.BooleanVar(value=False)
        self.drag_start_x = tk.StringVar(value="0")
        self.drag_start_y = tk.StringVar(value="0")
        self.drag_end_x = tk.StringVar(value="0")
        self.drag_end_y = tk.StringVar(value="0")

        # ── НОВОЕ v5: Системный трей ──
        self.tray_enabled = tk.BooleanVar(value=False)
        self.tray_start_minimized = tk.BooleanVar(value=False)
        self.tray_show_startstop = tk.BooleanVar(value=True)
        self.tray_show_coords = tk.BooleanVar(value=False)
        self.tray_icon = None

        # ── НОВОЕ v4: Макросы ──
        self.macro_steps = []           # [{type, x, y, button, key, delay}, ...]
        self.saved_macros = {}          # {name: [steps]}
        self.is_recording = False
        self.recorded_events = []
        self._rec_mouse_listener = None
        self._rec_kb_listener = None
        self._rec_start_time = 0

        # ── НОВОЕ v4: Мульти-точки маршрут ──
        self.route_points = []          # [{x, y, delay, action}]

        # ── НОВОЕ v4: Лог действий ──
        self.action_log = deque(maxlen=500)

        # ── UI ──
        self._build_ui()

        # ── Конфиг ──
        self._load_config()
        self._load_coords_history()
        self._load_profiles()
        self._load_macros()

        # ── Глобальный хоткей ──
        self._kb_listener = pynput_keyboard.Listener(on_press=self._on_global_key)
        self._kb_listener.daemon = True
        self._kb_listener.start()

        # ── Привязки ──
        self.root.bind_all("<Button-1>", self._clear_focus_on_click, add="+")
        self.root.bind_all("<Button-3>", self._right_click_global, add="+")
        self.root.bind_all("<Escape>", self._cancel_coord_selection, add="+")
        self.root.bind("<Destroy>", lambda e: self._do_save_config())

        # ── Обработка закрытия окна ──
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # ── Системный трей ──
        if HAS_TRAY:
            self._setup_tray()

        # Убирать выделение текста при получении фокуса всеми Entry
        self.root.bind_class("TEntry", "<FocusIn>",
                             lambda e: e.widget.after(1, e.widget.selection_clear))
        # Начальный фокус — на кнопку, чтобы Entry не были выделены
        self.root.after(50, lambda: self.start_btn.focus_set())

        self._center_window()

        # Звук при запуске программы
        if self.sound_enabled.get():
            self.root.after(300, lambda: self._play_sound("startup"))

        # Запуск свёрнутым в трей
        if self.tray_start_minimized.get() and self.tray_enabled.get() and HAS_TRAY:
            self.root.after(100, self._minimize_to_tray)

    def _set_icon(self):
        try:
            base = sys._MEIPASS if getattr(sys, "frozen", False) \
                else os.path.dirname(os.path.abspath(__file__))
            ico = os.path.join(base, "mss.ico")
            if os.path.exists(ico):
                self.root.iconbitmap(ico)
        except Exception:
            pass

    # ── Локализация ───────────────────────────────────────────────────────────

    def _load_locale(self):
        """Загрузить файл локализации из locales/<lang>.json"""
        base = sys._MEIPASS if getattr(sys, "frozen", False) \
            else os.path.dirname(os.path.abspath(__file__))
        locale_path = os.path.join(base, "locales", f"{self.current_language}.json")
        try:
            if os.path.exists(locale_path):
                with open(locale_path, "r", encoding="utf-8") as f:
                    self._locale = json.load(f)
            else:
                self._locale = {}
        except Exception:
            self._locale = {}

    def _t(self, key, **kwargs):
        """Получить локализованную строку по ключу с подстановкой параметров."""
        text = self._locale.get(key, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError):
                pass
        return text

    def _switch_language(self):
        """Переключить язык и перестроить интерфейс."""
        langs = self._get_available_languages()
        if not langs:
            return
        idx = langs.index(self.current_language) if self.current_language in langs else -1
        self.current_language = langs[(idx + 1) % len(langs)]
        self._load_locale()
        self._do_save_config()  # Сохранить новый язык ДО перестройки UI
        self._rebuild_ui()

    def _get_available_languages(self):
        """Найти все доступные файлы локализации."""
        base = sys._MEIPASS if getattr(sys, "frozen", False) \
            else os.path.dirname(os.path.abspath(__file__))
        locales_dir = os.path.join(base, "locales")
        if not os.path.isdir(locales_dir):
            return ["ru"]
        langs = []
        for f in sorted(os.listdir(locales_dir)):
            if f.endswith(".json"):
                langs.append(f[:-5])
        return langs or ["ru"]

    def _rebuild_ui(self):
        """Перестроить весь интерфейс для смены языка."""
        geo = self.root.geometry()
        # Уничтожить все дочерние виджеты
        for w in self.root.winfo_children():
            if isinstance(w, tk.Menu):
                continue
            w.destroy()
        self.root.config(menu="")
        self._coord_windows = []
        self._build_ui()
        # Восстановить состояние
        self._load_config()
        self._load_coords_history()
        self._load_profiles()
        self._load_macros()
        self._on_action_type_change()
        self._on_human_toggle()
        self._on_limit_toggle()
        self._on_clicker_toggle()
        self._on_fixed_click_toggle()
        self._on_drag_toggle()
        self._on_afk_toggle()
        self._on_sound_toggle()
        self._on_tray_toggle()
        self._on_movement_change()
        self.root.geometry(geo)
        self.root.after(50, lambda: self.start_btn.focus_set())

    # ══════════════════════════════════════════════════════════════════════════
    #                      ПОСТРОЕНИЕ ИНТЕРФЕЙСА
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        # ── 2025/26 ULTRA MODERN Design System ────────────────────────────────
        # Вдохновлено: Glassmorphism, Neumorphism, и современными UI трендами
        self.COLORS = {
            "accent":       "#7c5cfc",   # Electric purple - основной акцент
            "accent_glow":  "#9b82ff",   # Lighter purple - свечение
            "accent2":      "#00d4aa",   # Mint teal - второй акцент
            "accent3":      "#ff6b9d",   # Coral pink - третий акцент
            "accent4":      "#ffc857",   # Golden yellow
            "success":      "#00d4aa",   # Успех (зеленый/бирюзовый)
            "warning":      "#ffc857",   # Предупреждение (желтый)
            "error":        "#ff5c5c",   # Ошибка (красный)
            "info":         "#5c9cff",   # Информация (синий)
            "text":         "#e8e8f0",   # Основной текст
            "text_sec":     "#8888a0",   # Вторичный текст
            "text_dim":     "#555570",   # Приглушенный текст
            "text_bright":  "#ffffff",   # Яркий текст
            "surface":      "#12121e",   # Основной фон
            "card":         "#1a1a2e",   # Фон карточек
            "card_hover":   "#222238",   # Карточки при наведении
            "border":       "#2a2a44",   # Границы
            "shadow":       "#0a0a10",   # Тени
        }

        self.style = ttk.Style()

        # ── 🎨 ULTRA MODERN Global Styles (2025-2026) ──
        self.style.configure(".", 
                             font=("Segoe UI", 10),
                             background=self.COLORS["surface"])
        
        # Labels с современной типографикой
        self.style.configure("TLabel", 
                             font=("Segoe UI", 10),
                             background=self.COLORS["surface"],
                             foreground=self.COLORS["text"])
        
        # LabelFrames - карточный стиль с акцентами
        self.style.configure("TLabelframe", 
                             padding=18,
                             background=self.COLORS["card"],
                             bordercolor=self.COLORS["border"],
                             relief="flat")
        self.style.configure("TLabelframe.Label",
                             font=("Segoe UI", 11, "bold"),
                             foreground=self.COLORS["accent"],
                             background=self.COLORS["card"])
        
        # Notebook tabs - минималистичный стиль
        self.style.configure("TNotebook",
                             background=self.COLORS["surface"],
                             borderwidth=0)
        self.style.configure("TNotebook.Tab",
                             padding=(22, 11),
                             font=("Segoe UI", 10, "bold"))
        
        # Checkbox & Radio - современный вид
        self.style.configure("TCheckbutton", 
                             font=("Segoe UI", 10),
                             background=self.COLORS["surface"])
        self.style.configure("TRadiobutton", 
                             font=("Segoe UI", 10),
                             background=self.COLORS["surface"])

        # ── 🔘 Modern Button Styles ──
        self.style.configure("Accent.TButton",
                             font=("Segoe UI", 13, "bold"), 
                             padding=(24, 14))
        self.style.configure("Secondary.TButton",
                             font=("Segoe UI", 10), 
                             padding=(14, 8))
        self.style.configure("Rec.TButton",
                             font=("Segoe UI", 10, "bold"), 
                             padding=(12, 7))
        self.style.configure("Compact.TLabelframe.Label",
                             font=("Segoe UI", 9, "bold"))

        # ── 📝 Modern Label Styles (Typography Hierarchy) ──
        self.style.configure("Title.TLabel",
                             font=("Segoe UI", 20, "bold"),
                             foreground=self.COLORS["text_bright"])
        self.style.configure("Subtitle.TLabel",
                             font=("Segoe UI", 9),
                             foreground=self.COLORS["text_dim"])
        self.style.configure("Section.TLabel",
                             font=("Segoe UI", 11, "bold"),
                             foreground=self.COLORS["accent"])
        self.style.configure("Coords.TLabel",
                             font=("Consolas", 11),
                             foreground=self.COLORS["accent2"])
        self.style.configure("Status.TLabel",
                             font=("Segoe UI", 11, "bold"))

        # ── Container ──
        container = ttk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True, padx=18, pady=14)

        self._build_header(container)

        # Более заметный разделитель
        sep = ttk.Separator(container, orient="horizontal")
        sep.pack(fill=tk.X, pady=(4, 10))

        nb = ttk.Notebook(container)
        nb.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        self.notebook = nb

        self._build_main_tab(nb)
        self._build_coords_tab(nb)
        self._build_macro_tab(nb)
        self._build_tools_tab(nb)
        self._build_human_tab(nb)
        self._build_stats_tab(nb)

        self._build_footer(container)

    # ── Заголовок (ULTRA MODERN) ──────────────────────────────────────────────

    def _build_header(self, parent):
        h = ttk.Frame(parent)
        h.pack(fill=tk.X, pady=(0, 12))

        # ── 🎨 Logo + Brand (Modern Design) ──
        brand_frame = ttk.Frame(h)
        brand_frame.pack(side=tk.LEFT)

        # App icon - Современный gradient circle с тенью
        icon_cv = tk.Canvas(brand_frame, width=52, height=52,
                            highlightthickness=0,
                            bg=self.COLORS["surface"])
        icon_cv.pack(side=tk.LEFT, padx=(0, 14))
        
        # Внешний контур (glow effect)
        icon_cv.create_oval(1, 1, 51, 51,
                            fill="", 
                            outline=self.COLORS["accent_glow"], 
                            width=2)
        # Основной круг
        icon_cv.create_oval(4, 4, 48, 48,
                            fill=self.COLORS["accent"],
                            outline="")
        # Иконка молнии
        icon_cv.create_text(26, 26, 
                            text="⚡", 
                            font=("Segoe UI Emoji", 18), 
                            fill="white")

        # App name & version - Современная типографика
        title_stack = ttk.Frame(brand_frame)
        title_stack.pack(side=tk.LEFT)
        
        ttk.Label(title_stack, 
                  text="Mouse Ops",
                  style="Title.TLabel").pack(anchor="w")
        ttk.Label(title_stack, 
                  text=f"v{self.VERSION}  •  Ultimate Automation Suite  •  2025-2026",
                  style="Subtitle.TLabel").pack(anchor="w")

        # ── ⚡ Status Indicator (Modern) ──
        status_card = ttk.Frame(h)
        status_card.pack(side=tk.LEFT, padx=28)

        # Status dot с современным дизайном
        self._status_canvas = tk.Canvas(status_card, width=14, height=14,
                                        highlightthickness=0,
                                        bg=self.COLORS["surface"])
        self._status_canvas.pack(side=tk.LEFT, padx=(0, 10), pady=2)
        
        # Создаем свечение
        self._status_oval = self._status_canvas.create_oval(
            2, 2, 12, 12, 
            fill=self.COLORS["text_dim"], 
            outline="")

        # Status text
        self.status_dot = ttk.Label(status_card, 
                                    text=self._t("status.stopped"),
                                    style="Status.TLabel",
                                    foreground=self.COLORS["text_dim"])
        self.status_dot.pack(side=tk.LEFT)

        # ── 📍 Live Coordinates (Modern Card) ──
        coords_card = tk.Frame(h, bg=self.COLORS["card"], 
                               padx=16, pady=10)
        coords_card.pack(side=tk.LEFT, padx=16)
        
        self.live_coords = tk.Label(coords_card, 
                                     text="X: 0  Y: 0",
                                     font=("Consolas", 12, "bold"),
                                     fg=self.COLORS["accent2"],
                                     bg=self.COLORS["card"])
        self.live_coords.pack()
        self._update_live_coords()

        # ── 🌍 Language Button (Modern) ──
        self.lang_btn = ttk.Button(h, 
                                    text=f"🌍 {self.current_language.upper()}",
                                    width=8, 
                                    command=self._switch_language)
        self.lang_btn.pack(side=tk.RIGHT, padx=4)
        ToolTip(self.lang_btn, self._t("tip.language"))

    def _update_live_coords(self):
        """Обновлять живые координаты мыши"""
        try:
            x, y = self.mouse.position
            self.live_coords.config(text=f"X: {x}  Y: {y}")
        except Exception:
            pass
        self.root.after(350, self._update_live_coords)

    def _update_status_dot(self, color):
        """Обновить цвет индикатора статуса с плавным переходом"""
        try:
            self._status_canvas.itemconfig(self._status_oval, fill=color)
            # Добавить легкое свечение
            if color == self.COLORS["success"]:
                # Зеленое свечение для активного состояния
                pass
            elif color == self.COLORS["error"]:
                # Красное свечение для ошибки
                pass
        except Exception:
            pass

    # ── Вкладка «Основное» ────────────────────────────────────────────────────

    def _build_main_tab(self, nb):
        tab = ttk.Frame(nb)
        nb.add(tab, text=f"  {self._t('tab.main')}  ")

        cols = ttk.Frame(tab)
        cols.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        cols.columnconfigure(0, weight=1)
        cols.columnconfigure(1, weight=1)
        cols.rowconfigure(0, weight=1)

        self._build_movement_panel(cols)
        self._build_clicker_panel(cols)

        # Timer progress - Современный стиль
        self.timer_frame = ttk.Frame(tab)
        tf_inner = ttk.Frame(self.timer_frame)
        tf_inner.pack(fill=tk.X, padx=10)
        
        self.timer_label = tk.Label(tf_inner, 
                                      text=self._t("lbl.remaining_init"),
                                      font=("Consolas", 10),
                                      foreground=self.COLORS["text_sec"],
                                      bg=self.COLORS["surface"])
        self.timer_label.pack(side=tk.LEFT, padx=6)
        
        self.progress_bar = ttk.Progressbar(tf_inner, mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(12, 0))

        # ── 🚀 START/STOP BUTTON (Ultra Modern) ──
        self.start_btn = ttk.Button(tab, 
                                    text=self._t("btn.start"),
                                    style="Accent.TButton", 
                                    command=self.toggle)
        self.start_btn.pack(fill=tk.X, padx=10, pady=(8, 10))
        ToolTip(self.start_btn, self._t("tip.start"))

    def _build_movement_panel(self, parent):
        frame = ttk.LabelFrame(parent, text=f"  {self._t('lbl.movement')}  ", padding=18)
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        # Радиус
        ttk.Label(frame, text=self._t("lbl.radius"),
                  style="Section.TLabel").pack(anchor="w", pady=(0, 4))
        self.radius_entry = self._entry(frame, "30")
        self.radius_entry.pack(fill=tk.X, ipady=6, pady=(0, 14))
        ToolTip(self.radius_entry, self._t("tip.radius"))

        # Задержка мыши
        ttk.Label(frame, text=self._t("lbl.mouse_delay"),
                  style="Section.TLabel").pack(anchor="w", pady=(0, 4))
        self.mouse_delay_entry = self._entry(frame, "60")
        self.mouse_delay_entry.pack(fill=tk.X, ipady=6, pady=(0, 18))
        ToolTip(self.mouse_delay_entry, self._t("tip.mouse_delay"))

        # Тип движения
        mv_box = ttk.LabelFrame(frame, text=f"  {self._t('lbl.movement_type')}  ", padding=12)
        mv_box.pack(fill=tk.X)
        
        for label, val in [
            (self._t("mv.left_right"), "left_right"), 
            (self._t("mv.up_down"), "up_down"),
            (self._t("mv.diagonal"), "diagonal"), 
            (self._t("mv.random"), "random"),
            (self._t("mv.circle"), "circle"), 
            (self._t("mv.eight"), "eight"),
            (self._t("mv.square"), "square"), 
            (self._t("mv.free"), "free"),
        ]:
            ttk.Radiobutton(mv_box, text=label, variable=self.movement_var,
                            value=val, command=self._on_movement_change).pack(anchor="w", pady=3)

    def _build_clicker_panel(self, parent):
        frame = ttk.LabelFrame(parent, text=f"  {self._t('lbl.clicker')}  ", padding=18)
        frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        # Hotkey input - Современный стиль
        ttk.Label(frame, text=self._t("lbl.hotkey"),
                  style="Section.TLabel").pack(anchor="w", pady=(0, 4))
        self.hotkey_entry = ttk.Entry(frame, font=("Consolas", 12, "bold"), justify="center")
        self.hotkey_entry.insert(0, "F6")
        self.hotkey_entry.bind("<KeyPress>", self._set_hotkey)
        self.hotkey_entry.pack(fill=tk.X, ipady=8, pady=(0, 14))
        ToolTip(self.hotkey_entry, self._t("tip.hotkey"))

        # Timer - Современный дизайн
        tf = ttk.LabelFrame(frame, text=f"  {self._t('lbl.timer')}  ", padding=10)
        tf.pack(fill=tk.X, pady=(0, 14))
        
        trow = ttk.Frame(tf)
        trow.pack(fill=tk.X)
        trow.columnconfigure(1, weight=1)
        trow.columnconfigure(3, weight=1)
        trow.columnconfigure(5, weight=1)
        
        for i, (lbl, attr) in enumerate([
            (self._t("lbl.hours"), "hours_entry"),
            (self._t("lbl.minutes"), "minutes_entry"),
            (self._t("lbl.seconds"), "seconds_entry")
        ]):
            ttk.Label(trow, text=lbl, font=("Segoe UI", 9)).grid(
                row=0, column=i*2, padx=(8 if i else 0, 4), sticky="w")
            e = self._entry(trow, "", width=7)
            e.grid(row=0, column=i*2+1, padx=(0, 8 if i < 2 else 0), sticky="ew")
            setattr(self, attr, e)
        ToolTip(tf, self._t("tip.timer"))

        # Action limit - Современный
        lf = ttk.LabelFrame(frame, text=f"  {self._t('lbl.action_limit')}  ", padding=10)
        lf.pack(fill=tk.X, pady=(0, 14))
        
        ttk.Checkbutton(lf, text=self._t("lbl.limit_enable"),
                        variable=self.action_limit_enabled,
                        command=self._on_limit_toggle).pack(anchor="w", pady=(0, 4))
        
        self._limit_container = ttk.Frame(lf)
        lr = ttk.Frame(self._limit_container)
        lr.pack(fill=tk.X, pady=(6, 0))
        
        ttk.Label(lr, text=self._t("lbl.limit_max"), 
                  font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Entry(lr, textvariable=self.action_limit_count, width=12,
                  font=("Consolas", 11)).pack(side=tk.LEFT)
        ToolTip(lf, self._t("tip.action_limit"))
        self._on_limit_toggle()

        # Enable clicker
        ttk.Checkbutton(frame, text=self._t("lbl.enable_clicker"),
                        variable=self.auto_clicker_enabled,
                        command=self._on_clicker_toggle).pack(anchor="w", pady=(0, 8))

        # Clicker settings container
        self._clicker_holder = ttk.Frame(frame)
        self._clicker_holder.pack(fill=tk.X)
        self._clicker_container = ttk.Frame(self._clicker_holder)
        
        ttk.Label(self._clicker_container, text=self._t("lbl.click_delay"),
                  style="Section.TLabel").pack(anchor="w", pady=(0, 4))
        self.click_delay_entry = self._entry(self._clicker_container, "50")
        self.click_delay_entry.pack(fill=tk.X, ipady=6, pady=(0, 14))
        ToolTip(self.click_delay_entry, self._t("tip.click_delay"))
        self._on_clicker_toggle()

        # Action type - Современные кнопки
        ab = ttk.LabelFrame(frame, text=f"  {self._t('lbl.action_type')}  ", padding=10)
        ab.pack(fill=tk.X, pady=(0, 10))
        
        btn_row = ttk.Frame(ab)
        btn_row.pack(fill=tk.X, pady=4)
        
        for lbl, val in [
            (self._t("act.left"), "left"), 
            (self._t("act.right"), "right"),
            (self._t("act.middle"), "middle"), 
            (self._t("act.keyboard"), "keyboard")
        ]:
            ttk.Radiobutton(btn_row, text=lbl, variable=self.action_type,
                            value=val, command=self._on_action_type_change
                            ).pack(side=tk.LEFT, padx=6)

        # Keyboard key input
        self.kb_key_frame = ttk.Frame(ab)
        ttk.Label(self.kb_key_frame, text=self._t("lbl.key")).pack(side=tk.LEFT, padx=(0, 8))
        self.kb_key_entry = ttk.Entry(self.kb_key_frame, textvariable=self.kb_key_var,
                                       width=14, font=("Consolas", 11))
        self.kb_key_entry.pack(side=tk.LEFT)
        ToolTip(self.kb_key_entry, self._t("tip.kb_key"))

        # Double click
        ttk.Checkbutton(frame, text=self._t("lbl.double_click"),
                        variable=self.double_click_enabled,
                        command=self._save_config).pack(anchor="w", pady=(10, 0))
        
        self._on_action_type_change()

    # ── Вкладка «Координаты» ──────────────────────────────────────────────────

    def _build_coords_tab(self, nb):
        tab = ttk.Frame(nb)
        nb.add(tab, text=f"  {self._t('tab.coords')}  ")
        self._coords_tab = tab

        top_chk = ttk.Frame(tab)
        top_chk.pack(fill=tk.X, padx=10, pady=(10, 6))
        ttk.Checkbutton(top_chk, text=self._t("coord.enable"),
                        variable=self.fixed_click_enabled,
                        command=self._on_fixed_click_toggle).pack(anchor="w")

        self._coords_container = ttk.Frame(tab)

        main = ttk.Frame(self._coords_container)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)

        left = ttk.LabelFrame(main, text=f"  {self._t('coord.title')}  ", padding=14)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        coord_row = ttk.Frame(left)
        coord_row.pack(fill=tk.X, pady=(0, 8))
        coord_row.columnconfigure(1, weight=1)
        coord_row.columnconfigure(3, weight=1)

        ttk.Label(coord_row, text=self._t("lbl.x"),
                  font=("Consolas", 14, "bold"),
                  foreground=self.COLORS["accent"]
                  ).grid(row=0, column=0, padx=(0, 6))
        self.fixed_x_entry = ttk.Entry(coord_row, textvariable=self.fixed_x,
                                        font=("Consolas", 14), justify="center")
        self.fixed_x_entry.grid(row=0, column=1, sticky="ew", padx=(0, 14))
        ToolTip(self.fixed_x_entry, self._t("tip.fixed_x"))

        ttk.Label(coord_row, text=self._t("lbl.y"),
                  font=("Consolas", 14, "bold"),
                  foreground=self.COLORS["accent3"]
                  ).grid(row=0, column=2, padx=(0, 6))
        self.fixed_y_entry = ttk.Entry(coord_row, textvariable=self.fixed_y,
                                        font=("Consolas", 14), justify="center")
        self.fixed_y_entry.grid(row=0, column=3, sticky="ew")
        ToolTip(self.fixed_y_entry, self._t("tip.fixed_y"))

        self.coord_info_lbl = ttk.Label(left, text=self._t("coord.not_set"),
                                        foreground=self.COLORS["text_dim"],
                                        font=("Segoe UI", 9))
        self.coord_info_lbl.pack(anchor="w", pady=(0, 10))

        self.pick_btn = ttk.Button(left, text=self._t("btn.pick_screen"),
                                   command=self._start_coord_selection,
                                   style="Accent.TButton")
        self.pick_btn.pack(fill=tk.X, pady=(0, 5))
        ToolTip(self.pick_btn, self._t("tip.coord_pick"))

        ttk.Button(left, text=self._t("btn.grab_pos"),
                   command=self._grab_current_pos).pack(fill=tk.X, pady=(0, 5))
        test_btn = ttk.Button(left, text=self._t("btn.test"),
                   command=self._test_click_at_coords)
        test_btn.pack(fill=tk.X, pady=(0, 10))
        ToolTip(test_btn, self._t("tip.coord_pick"))

        sel_row = ttk.Frame(left)
        sel_row.pack(anchor="w", pady=(0, 8))
        ttk.Label(sel_row, text=self._t("coord.pick_btn"),
                  font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 8))
        for lbl, val in [(self._t("act.left"), "left"), (self._t("act.right"), "right")]:
            ttk.Radiobutton(sel_row, text=lbl, variable=self.coord_select_button,
                            value=val).pack(side=tk.LEFT, padx=4)

        try:
            u32 = ctypes.windll.user32
            sw, sh = u32.GetSystemMetrics(0), u32.GetSystemMetrics(1)
        except Exception:
            sw, sh = 1920, 1080
        ttk.Label(left, text=self._t("lbl.screen_format").format(w=sw, h=sh),
                  font=("Segoe UI", 8),
                  foreground=self.COLORS["text_dim"]).pack(anchor="w")

        # ── Right: History ──
        right = ttk.LabelFrame(main, text=f"  {self._t('coord.history')}  ", padding=14)
        right.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        list_frame = ttk.Frame(right)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self.coords_history_listbox = tk.Listbox(
            list_frame, font=("Consolas", 9), selectmode=tk.SINGLE,
            activestyle="none", bd=0, relief="flat",
            bg="#1a1a2e", fg="#e8e8f0",
            selectbackground=self.COLORS["accent"],
            selectforeground="white",
            highlightthickness=1,
            highlightcolor=self.COLORS["border"],
            highlightbackground=self.COLORS["border"])
        self.coords_history_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.coords_history_listbox.bind("<Double-Button-1>", self._load_coords_from_history)
        ToolTip(self.coords_history_listbox, self._t("tip.history_dblclick"))

        sb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL,
                           command=self.coords_history_listbox.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.coords_history_listbox.config(yscrollcommand=sb.set)

        hist_btns = ttk.Frame(right)
        hist_btns.pack(fill=tk.X)
        load_btn = ttk.Button(hist_btns, text=self._t("btn.load"),
                   command=self._load_selected_coords)
        load_btn.pack(side=tk.LEFT, padx=(0, 4))
        ToolTip(load_btn, self._t("tip.load_coords"))
        del_btn = ttk.Button(hist_btns, text=self._t("btn.delete"),
                   command=self._delete_coord_from_history)
        del_btn.pack(side=tk.LEFT, padx=(0, 4))
        ToolTip(del_btn, self._t("tip.delete_entry"))
        clear_btn = ttk.Button(hist_btns, text=self._t("btn.clear"),
                   command=self._clear_coords_history)
        clear_btn.pack(side=tk.LEFT)
        ToolTip(clear_btn, self._t("tip.clear_history"))

        self._on_fixed_click_toggle()

    # ── Вкладка «Макросы» ────────────────────────────────────────────────────

    def _build_macro_tab(self, nb):
        tab = ttk.Frame(nb)
        nb.add(tab, text=f"  {self._t('tab.macros')}  ")

        top_nb = ttk.Notebook(tab)
        top_nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        self.macros_notebook = top_nb

        # ── Sub-tab: Macro Builder ──
        builder = ttk.Frame(top_nb, padding=10)
        top_nb.add(builder, text=f"  {self._t('tab.builder')}  ")

        # Steps list
        steps_frame = ttk.LabelFrame(builder, text=f"  {self._t('macro.steps')}  ", padding=8)
        steps_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        lf = ttk.Frame(steps_frame)
        lf.pack(fill=tk.BOTH, expand=True)

        self.macro_listbox = tk.Listbox(lf, font=("Consolas", 9), selectmode=tk.SINGLE,
                                         activestyle="none", bd=0, relief="flat",
                                         bg="#1a1a2e", fg="#e8e8f0",
                                         selectbackground="#7c5cfc",
                                         selectforeground="white",
                                         highlightthickness=1,
                                         highlightcolor="#2a2a44",
                                         highlightbackground="#2a2a44")
        self.macro_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        msb = ttk.Scrollbar(lf, orient=tk.VERTICAL, command=self.macro_listbox.yview)
        msb.pack(side=tk.RIGHT, fill=tk.Y)
        self.macro_listbox.config(yscrollcommand=msb.set)

        # Кнопки добавления
        add_row = ttk.Frame(builder)
        add_row.pack(fill=tk.X, pady=4)
        b = ttk.Button(add_row, text=self._t("macro.add_click"), command=self._macro_add_click)
        b.pack(side=tk.LEFT, padx=2)
        ToolTip(b, self._t("macro.add_click"))
        b = ttk.Button(add_row, text=self._t("macro.add_key"), command=self._macro_add_key)
        b.pack(side=tk.LEFT, padx=2)
        ToolTip(b, self._t("macro.add_key"))
        b = ttk.Button(add_row, text=self._t("macro.add_delay"), command=self._macro_add_delay)
        b.pack(side=tk.LEFT, padx=2)
        ToolTip(b, self._t("macro.add_delay"))
        b = ttk.Button(add_row, text=self._t("macro.add_move"), command=self._macro_add_move)
        b.pack(side=tk.LEFT, padx=2)
        ToolTip(b, self._t("macro.add_move"))
        b = ttk.Button(add_row, text=self._t("macro.add_drag"), command=self._macro_add_drag)
        b.pack(side=tk.LEFT, padx=2)
        ToolTip(b, self._t("macro.add_drag"))

        ctrl_row = ttk.Frame(builder)
        ctrl_row.pack(fill=tk.X, pady=2)
        b = ttk.Button(ctrl_row, text=self._t("macro.up") + " ", command=self._macro_move_up)
        b.pack(side=tk.LEFT, padx=2)
        b = ttk.Button(ctrl_row, text=self._t("macro.down") + " ", command=self._macro_move_down)
        b.pack(side=tk.LEFT, padx=2)
        b = ttk.Button(ctrl_row, text=self._t("macro.edit"), command=self._macro_edit_step)
        b.pack(side=tk.LEFT, padx=2)
        b = ttk.Button(ctrl_row, text=self._t("btn.delete"), command=self._macro_delete_step)
        b.pack(side=tk.LEFT, padx=2)
        b = ttk.Button(ctrl_row, text=self._t("btn.clear"), command=self._macro_clear)
        b.pack(side=tk.LEFT, padx=2)

        # Управление макросами
        save_row = ttk.Frame(builder)
        save_row.pack(fill=tk.X, pady=4)
        ttk.Label(save_row, text=self._t("macro.name")).pack(side=tk.LEFT, padx=(0, 4))
        self.macro_name_combo = ttk.Combobox(save_row, width=18, font=("Segoe UI", 9))
        self.macro_name_combo.pack(side=tk.LEFT, padx=2)
        self.macro_name_combo.bind("<<ComboboxSelected>>", self._macro_load_selected)
        ToolTip(self.macro_name_combo, self._t("tip.macro_combo"))
        ttk.Button(save_row, text=self._t("btn.save"), command=self._macro_save
                   ).pack(side=tk.LEFT, padx=2)
        b = ttk.Button(save_row, text=self._t("btn.delete"), command=self._macro_delete_saved)
        b.pack(side=tk.LEFT, padx=2)
        ToolTip(b, self._t("tip.delete_macro"))

        play_row = ttk.Frame(builder)
        play_row.pack(fill=tk.X, pady=4)
        ttk.Label(play_row, text=self._t("macro.repeats")).pack(side=tk.LEFT, padx=(0, 4))
        self.macro_repeats = ttk.Entry(play_row, width=6)
        self.macro_repeats.insert(0, "1")
        self.macro_repeats.pack(side=tk.LEFT, padx=2)
        ToolTip(self.macro_repeats, self._t("tip.macro_repeats"))
        b_play = ttk.Button(play_row, text=self._t("btn.play_macro"), style="Accent.TButton",
                   command=self._macro_play)
        b_play.pack(side=tk.LEFT, padx=(8, 2))
        b_stop = ttk.Button(play_row, text=self._t("btn.stop_macro"), command=self._macro_stop)
        b_stop.pack(side=tk.LEFT, padx=2)

        # ── Sub-tab: Recording ──
        rec_tab = ttk.Frame(top_nb, padding=10)
        top_nb.add(rec_tab, text=f"  {self._t('tab.recording')}  ")

        ttk.Label(rec_tab,
                  text=self._t("macro.recording_desc"),
                  font=("Segoe UI", 9), foreground=self.COLORS["text_dim"], wraplength=700
                  ).pack(anchor="w", pady=(0, 8))

        rec_btns = ttk.Frame(rec_tab)
        rec_btns.pack(fill=tk.X, pady=4)
        self.rec_btn = ttk.Button(rec_btns, text=self._t("btn.rec_start"),
                                   style="Rec.TButton", command=self._rec_start)
        self.rec_btn.pack(side=tk.LEFT, padx=4)
        self.rec_stop_btn = ttk.Button(rec_btns, text=self._t("btn.rec_stop"),
                                        command=self._rec_stop, state="disabled")
        self.rec_stop_btn.pack(side=tk.LEFT, padx=4)
        b_to_builder = ttk.Button(rec_btns, text=self._t("btn.rec_to_builder"),
                   command=self._rec_to_builder)
        b_to_builder.pack(side=tk.LEFT, padx=4)

        self.rec_status = ttk.Label(rec_tab, text=self._t("status.not_recording"),
                                     foreground=self.COLORS["text_dim"], font=("Segoe UI", 10))
        self.rec_status.pack(anchor="w", pady=4)

        rf = ttk.LabelFrame(rec_tab, text=f"  {self._t('macro.recorded_events')}  ", padding=8)
        rf.pack(fill=tk.BOTH, expand=True)
        rlf = ttk.Frame(rf)
        rlf.pack(fill=tk.BOTH, expand=True)
        self.rec_listbox = tk.Listbox(rlf, font=("Consolas", 9), activestyle="none",
                                       bd=0, relief="flat",
                                       bg="#1a1a2e", fg="#e8e8f0",
                                       selectbackground="#7c5cfc",
                                       selectforeground="white",
                                       highlightthickness=1,
                                       highlightcolor="#2a2a44",
                                       highlightbackground="#2a2a44")
        self.rec_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        rsb = ttk.Scrollbar(rlf, orient=tk.VERTICAL, command=self.rec_listbox.yview)
        rsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.rec_listbox.config(yscrollcommand=rsb.set)

        # ── Sub-tab: Multi-route ──
        route_tab = ttk.Frame(top_nb, padding=10)
        top_nb.add(route_tab, text=f"  {self._t('tab.route')}  ")
        self._route_tab = route_tab

        ttk.Label(route_tab,
                  text=self._t("macro.route_desc"),
                  font=("Segoe UI", 9), foreground=self.COLORS["text_dim"], wraplength=700
                  ).pack(anchor="w", pady=(0, 6))

        rframe = ttk.LabelFrame(route_tab, text=f"  {self._t('macro.route_points')}  ", padding=8)
        rframe.pack(fill=tk.BOTH, expand=True, pady=(0, 6))
        rlf2 = ttk.Frame(rframe)
        rlf2.pack(fill=tk.BOTH, expand=True)
        self.route_listbox = tk.Listbox(rlf2, font=("Consolas", 9), activestyle="none",
                                         bd=0, relief="flat",
                                         bg="#1a1a2e", fg="#e8e8f0",
                                         selectbackground="#7c5cfc",
                                         selectforeground="white",
                                         highlightthickness=1,
                                         highlightcolor="#2a2a44",
                                         highlightbackground="#2a2a44")
        self.route_listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        rsb2 = ttk.Scrollbar(rlf2, orient=tk.VERTICAL, command=self.route_listbox.yview)
        rsb2.pack(side=tk.RIGHT, fill=tk.Y)
        self.route_listbox.config(yscrollcommand=rsb2.set)

        rbtns = ttk.Frame(route_tab)
        rbtns.pack(fill=tk.X, pady=4)
        b = ttk.Button(rbtns, text=self._t("macro.route_add_pick"), command=self._route_add_pick)
        b.pack(side=tk.LEFT, padx=2)
        b = ttk.Button(rbtns, text=self._t("macro.route_add_current"), command=self._route_add_current)
        b.pack(side=tk.LEFT, padx=2)
        b = ttk.Button(rbtns, text=self._t("macro.edit"), command=self._route_edit)
        b.pack(side=tk.LEFT, padx=2)
        b = ttk.Button(rbtns, text=self._t("btn.delete"), command=self._route_delete)
        b.pack(side=tk.LEFT, padx=2)
        b = ttk.Button(rbtns, text=self._t("btn.clear"), command=self._route_clear)
        b.pack(side=tk.LEFT, padx=2)

        rplay = ttk.Frame(route_tab)
        rplay.pack(fill=tk.X, pady=4)
        ttk.Label(rplay, text=self._t("macro.repeats")).pack(side=tk.LEFT, padx=(0, 4))
        self.route_repeats = ttk.Entry(rplay, width=6)
        self.route_repeats.insert(0, "1")
        self.route_repeats.pack(side=tk.LEFT, padx=2)
        ToolTip(self.route_repeats, self._t("tip.route_repeats"))
        b_rp = ttk.Button(rplay, text=self._t("btn.play_route"), style="Accent.TButton",
                   command=self._route_play)
        b_rp.pack(side=tk.LEFT, padx=(8, 2))
        b_rs = ttk.Button(rplay, text=self._t("btn.stop_macro"), command=self._stop)
        b_rs.pack(side=tk.LEFT, padx=2)

    # ── Вкладка «Инструменты» ────────────────────────────────────────────────

    def _build_tools_tab(self, nb):
        tab = ttk.Frame(nb)
        nb.add(tab, text=f"  {self._t('tab.tools')}  ")

        canvas = tk.Canvas(tab, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        self._tools_canvas_win = canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=6)
        scrollbar.pack(side="right", fill="y")

        def _on_scrollable_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        scrollable.bind("<Configure>", _on_scrollable_configure)

        def _on_canvas_configure(e):
            canvas.itemconfigure(self._tools_canvas_win, width=e.width)
        canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        def _bind_mw(e):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
        def _unbind_mw(e):
            canvas.unbind_all("<MouseWheel>")
        canvas.bind("<Enter>", _bind_mw)
        canvas.bind("<Leave>", _unbind_mw)
        scrollable.bind("<Enter>", _bind_mw)
        scrollable.bind("<Leave>", _unbind_mw)

        # ── Drag & Drop ──
        dd = ttk.LabelFrame(scrollable, text=f"  {self._t('tool.drag_drop')}  ", padding=10)
        dd.pack(fill=tk.X, pady=(0, 8))
        self._dd_frame = dd
        ttk.Checkbutton(dd, text=self._t("tool.drag_enable"),
                        variable=self.drag_enabled,
                        command=self._on_drag_toggle).pack(anchor="w", pady=(0, 2))

        self._drag_container = ttk.Frame(dd)
        ttk.Label(self._drag_container, text=self._t("tool.drag_desc"),
                  font=("Segoe UI", 8), foreground=self.COLORS["text_dim"]).pack(anchor="w", pady=(0, 4))

        drow1 = ttk.Frame(self._drag_container)
        drow1.pack(fill=tk.X, pady=2)
        ttk.Label(drow1, text=self._t("tool.point_a"), font=("Consolas", 9)).pack(side=tk.LEFT)
        ttk.Entry(drow1, textvariable=self.drag_start_x, width=6,
                  font=("Consolas", 9)).pack(side=tk.LEFT, padx=3)
        ttk.Label(drow1, text=self._t("lbl.y"), font=("Consolas", 9)).pack(side=tk.LEFT)
        ttk.Entry(drow1, textvariable=self.drag_start_y, width=6,
                  font=("Consolas", 9)).pack(side=tk.LEFT, padx=3)
        ttk.Button(drow1, text="🎯", width=3,
                   command=lambda: self._pick_for_var(self.drag_start_x, self.drag_start_y)
                   ).pack(side=tk.LEFT, padx=3)

        drow2 = ttk.Frame(self._drag_container)
        drow2.pack(fill=tk.X, pady=2)
        ttk.Label(drow2, text=self._t("tool.point_b"), font=("Consolas", 9)).pack(side=tk.LEFT)
        ttk.Entry(drow2, textvariable=self.drag_end_x, width=6,
                  font=("Consolas", 9)).pack(side=tk.LEFT, padx=3)
        ttk.Label(drow2, text=self._t("lbl.y"), font=("Consolas", 9)).pack(side=tk.LEFT)
        ttk.Entry(drow2, textvariable=self.drag_end_y, width=6,
                  font=("Consolas", 9)).pack(side=tk.LEFT, padx=3)
        ttk.Button(drow2, text="🎯", width=3,
                   command=lambda: self._pick_for_var(self.drag_end_x, self.drag_end_y)
                   ).pack(side=tk.LEFT, padx=3)

        ttk.Button(self._drag_container, text=self._t("btn.test_drag"), command=self._test_drag
                   ).pack(anchor="w", pady=3)
        ToolTip(dd, self._t("tip.drag"))
        self._on_drag_toggle()

        # ── Anti-AFK ──
        afk = ttk.LabelFrame(scrollable, text=f"  {self._t('tool.anti_afk')}  ", padding=10)
        afk.pack(fill=tk.X, pady=(0, 8))
        ttk.Checkbutton(afk, text=self._t("tool.afk_enable"),
                        variable=self.anti_afk_enabled,
                        command=self._on_afk_toggle).pack(anchor="w", pady=(0, 2))
        self._afk_container = ttk.Frame(afk)
        ttk.Label(self._afk_container, text=self._t("tool.afk_desc"),
                  font=("Segoe UI", 8), foreground=self.COLORS["text_dim"]).pack(anchor="w", pady=(0, 3))
        arow = ttk.Frame(self._afk_container)
        arow.pack(fill=tk.X)
        ttk.Label(arow, text=self._t("tool.afk_interval")).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Entry(arow, textvariable=self.anti_afk_interval, width=7).pack(side=tk.LEFT)
        ToolTip(afk, self._t("tip.anti_afk"))
        self._on_afk_toggle()

        # ── Sound ──
        snd = ttk.LabelFrame(scrollable, text=f"  {self._t('tool.sound')}  ", padding=10)
        snd.pack(fill=tk.X, pady=(0, 8))
        ttk.Checkbutton(snd, text=self._t("tool.sound_enable"),
                        variable=self.sound_enabled,
                        command=self._on_sound_toggle).pack(anchor="w")
        self._sound_container = ttk.Frame(snd)
        vol_row = ttk.Frame(self._sound_container)
        vol_row.pack(fill=tk.X, pady=4)
        ttk.Label(vol_row, text=self._t("tool.sound_volume"),
                  font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 4))
        self._vol_val_lbl = ttk.Label(vol_row, text=f"{self.sound_volume.get()}%",
                                       width=5, anchor="center",
                                       font=("Consolas", 10, "bold"),
                                       foreground=self.COLORS["accent"])
        self._vol_val_lbl.pack(side=tk.RIGHT, padx=4)
        ttk.Scale(vol_row, from_=0, to=100, variable=self.sound_volume,
                  orient=tk.HORIZONTAL,
                  command=lambda v: self._vol_val_lbl.config(text=f"{int(float(v))}%")
                  ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        ToolTip(vol_row, self._t("tool.sound_volume_tip"))
        ttk.Button(self._sound_container, text=self._t("btn.test_sound"), command=self._test_sound
                   ).pack(anchor="w", pady=3)
        ToolTip(snd, self._t("tip.sound"))
        self._on_sound_toggle()

        # ── Tray ──
        tray_lf = ttk.LabelFrame(scrollable, text=f"  {self._t('tool.tray')}  ", padding=10)
        tray_lf.pack(fill=tk.X, pady=(0, 8))
        ttk.Checkbutton(tray_lf, text=self._t("tool.tray_enable"),
                        variable=self.tray_enabled,
                        command=self._on_tray_toggle).pack(anchor="w", pady=(0, 2))
        self._tray_container = ttk.Frame(tray_lf)
        ttk.Label(self._tray_container, text=self._t("tool.tray_desc"),
                  font=("Segoe UI", 8), foreground=self.COLORS["text_dim"], wraplength=600
                  ).pack(anchor="w", pady=(0, 4))
        ttk.Checkbutton(self._tray_container, text=self._t("tool.tray_start_minimized"),
                        variable=self.tray_start_minimized).pack(anchor="w", pady=(0, 2))

        # Настройки видимости пунктов меню трея
        tray_cfg_lf = ttk.LabelFrame(self._tray_container, text=f"  {self._t('tool.tray_settings')}  ", padding=8)
        tray_cfg_lf.pack(fill=tk.X, pady=(4, 4))
        ttk.Checkbutton(tray_cfg_lf, text=self._t("tray.menu_show_toggle"),
                        variable=self.tray_show_startstop).pack(anchor="w")
        ttk.Checkbutton(tray_cfg_lf, text=self._t("tray.menu_show_coords"),
                        variable=self.tray_show_coords).pack(anchor="w")

        tray_btn = ttk.Button(self._tray_container, text=self._t("btn.minimize_tray"),
                              command=self._minimize_to_tray)
        tray_btn.pack(anchor="w", pady=3)
        if not HAS_TRAY:
            tray_btn.config(state="disabled")
            ttk.Label(self._tray_container, text=self._t("tool.pystray_missing"),
                      font=("Segoe UI", 8), foreground=self.COLORS["error"]).pack(anchor="w")
        ToolTip(tray_lf, self._t("tip.tray"))
        self._on_tray_toggle()

    # ── Вкладка «Имитация» ───────────────────────────────────────────────────

    def _build_human_tab(self, nb):
        tab = ttk.Frame(nb)
        nb.add(tab, text=f"  {self._t('tab.human')}  ")
        self._human_tab = tab

        top = ttk.Frame(tab)
        top.pack(fill=tk.X, padx=10, pady=(10, 6))

        ttk.Checkbutton(top, text=self._t("human.enable"),
                        variable=self.human_like_enabled,
                        command=self._on_human_toggle).pack(anchor="w")
        ttk.Label(top,
                  text=self._t("human.desc"),
                  font=("Segoe UI", 8), foreground=self.COLORS["text_dim"],
                  wraplength=700
                  ).pack(anchor="w", pady=(2, 0))

        self._human_container = ttk.Frame(tab)

        hn = ttk.Notebook(self._human_container)
        hn.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        mt = ttk.Frame(hn, padding=12)
        hn.add(mt, text=f"  {self._t('tab.movement')}  ")
        self._make_slider(mt, self._t("human.curviness"), self.curviness, 1, 10,
                          self._t("human.curviness"))
        self._make_slider(mt, self._t("human.tremor"), self.hand_tremor, 0, 10,
                          self._t("human.tremor"))
        self._make_slider(mt, self._t("human.overshoot"), self.overshoot_level, 0, 10,
                          self._t("human.overshoot"))
        self._make_slider(mt, self._t("human.speed_var"), self.speed_variation_level, 0, 10,
                          self._t("human.speed_var"))
        self._make_slider(mt, self._t("human.micro"), self.micro_movements_level, 0, 10,
                          self._t("human.micro"))
        ttk.Label(mt, text=self._t("human.pos_var"),
                  style="Section.TLabel").pack(anchor="w", pady=(10, 2))
        pos_var_entry = ttk.Entry(mt, textvariable=self.human_pos_variation,
                                   font=("Consolas", 10))
        pos_var_entry.pack(fill=tk.X)
        ToolTip(pos_var_entry, self._t("tip.pos_var"))

        ct = ttk.Frame(hn, padding=12)
        hn.add(ct, text=f"  {self._t('tab.clicks')}  ")
        self._make_slider(ct, self._t("human.pressure"), self.click_pressure, 0, 10,
                          self._t("human.pressure"))
        self._make_slider(ct, self._t("human.pauses"), self.random_pauses, 0, 10,
                          self._t("human.pauses"))
        self._make_slider(ct, self._t("human.fatigue"), self.fatigue_level, 0, 10,
                          self._t("human.fatigue"))
        ttk.Label(ct, text=self._t("human.delay_var"),
                  style="Section.TLabel").pack(anchor="w", pady=(10, 2))
        delay_var_entry = ttk.Entry(ct, textvariable=self.human_delay_variation,
                                     font=("Consolas", 10))
        delay_var_entry.pack(fill=tk.X)
        ToolTip(delay_var_entry, self._t("tip.delay_var"))

        pv = ttk.Frame(hn, padding=12)
        hn.add(pv, text=f"  {self._t('tab.preview')}  ")
        self.preview_canvas = tk.Canvas(pv, width=400, height=220, bg="#0b0b14",
                                         highlightthickness=1,
                                         highlightbackground=self.COLORS["border"])
        self.preview_canvas.pack(pady=8)
        preview_btn = ttk.Button(pv, text=self._t("btn.preview"),
                   command=self._preview_trajectory)
        preview_btn.pack(pady=6)
        self.preview_info = ttk.Label(pv, text=self._t("human.preview_hint"),
                                      font=("Segoe UI", 8),
                                      foreground=self.COLORS["text_dim"])
        self.preview_info.pack()

        self._on_human_toggle()

    def _make_slider(self, parent, label, var, from_, to_, tip):
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=4)
        lbl = ttk.Label(row, text=label, width=28, anchor="w",
                         font=("Segoe UI", 10))
        lbl.pack(side=tk.LEFT)
        val_lbl = ttk.Label(row, text=str(var.get()), width=3, anchor="center",
                             font=("Consolas", 11, "bold"),
                             foreground=self.COLORS["accent"])
        val_lbl.pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Scale(row, from_=from_, to=to_, variable=var, orient=tk.HORIZONTAL,
                  command=lambda v, vl=val_lbl: vl.config(text=str(int(float(v))))
                  ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ToolTip(lbl, tip)

    # ── Вкладка «Статистика + Лог» ───────────────────────────────────────────

    def _build_stats_tab(self, nb):
        tab = ttk.Frame(nb)
        nb.add(tab, text=f"  {self._t('tab.stats')}  ")

        st_nb = ttk.Notebook(tab)
        st_nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        # ── Sub-tab: Session Stats ──
        sf_tab = ttk.Frame(st_nb, padding=12)
        st_nb.add(sf_tab, text=f"  {self._t('tab.session')}  ")

        sf = ttk.LabelFrame(sf_tab, text=f"  {self._t('stat.session')}  ", padding=16)
        sf.pack(fill=tk.X)

        self.stat_clicks = tk.IntVar(value=0)
        self.stat_actions = tk.IntVar(value=0)
        self.stat_elapsed = tk.StringVar(value="00:00:00")
        self.stat_cps = tk.StringVar(value="0.0")
        self.stat_distance = tk.IntVar(value=0)
        self._session_start = None
        self._last_mouse_pos = None

        for lbl, var in [
            (self._t("stat.clicks"), self.stat_clicks),
            (self._t("stat.actions"), self.stat_actions),
            (self._t("stat.elapsed"), self.stat_elapsed),
            (self._t("stat.cps"), self.stat_cps),
            (self._t("stat.distance"), self.stat_distance),
        ]:
            row = ttk.Frame(sf)
            row.pack(fill=tk.X, pady=3)
            ttk.Label(row, text=lbl, width=26, anchor="w",
                      font=("Segoe UI", 10)).pack(side=tk.LEFT)
            ttk.Label(row, textvariable=var,
                      font=("Consolas", 12, "bold"),
                      foreground=self.COLORS["accent"]).pack(side=tk.LEFT)

        # Limit counter
        self.limit_frame = ttk.Frame(sf)
        self.limit_frame.pack(fill=tk.X, pady=(6, 0))
        ttk.Label(self.limit_frame, text=self._t("stat.limit"), width=26,
                  anchor="w", font=("Segoe UI", 10)).pack(side=tk.LEFT)
        self.limit_progress = ttk.Progressbar(self.limit_frame, mode='determinate',
                                               maximum=100, length=160)
        self.limit_progress.pack(side=tk.LEFT, padx=6)
        self.limit_label = ttk.Label(self.limit_frame, text="0/∞",
                                      font=("Consolas", 10, "bold"),
                                      foreground=self.COLORS["accent2"])
        self.limit_label.pack(side=tk.LEFT)

        self.fatigue_frame = ttk.Frame(sf)
        self.fatigue_frame.pack(fill=tk.X, pady=(6, 0))
        ttk.Label(self.fatigue_frame, text=self._t("stat.fatigue"), width=26,
                  anchor="w", font=("Segoe UI", 10)).pack(side=tk.LEFT)
        self.fatigue_bar = ttk.Progressbar(self.fatigue_frame, mode='determinate',
                                            maximum=100, length=160)
        self.fatigue_bar.pack(side=tk.LEFT, padx=6)
        self.fatigue_pct = ttk.Label(self.fatigue_frame, text="0%",
                                      font=("Consolas", 10, "bold"),
                                      foreground=self.COLORS["warning"])
        self.fatigue_pct.pack(side=tk.LEFT)

        reset_btn = ttk.Button(sf_tab, text=self._t("btn.reset_stats"),
                   command=self._reset_stats)
        reset_btn.pack(pady=8)
        ToolTip(reset_btn, self._t("tip.reset_stats"))

        # ── Sub-tab: Log ──
        log_tab = ttk.Frame(st_nb, padding=12)
        st_nb.add(log_tab, text=f"  {self._t('tab.log')}  ")

        log_frame = ttk.Frame(log_tab)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_frame, font=("Consolas", 9), wrap=tk.NONE,
                                state=tk.DISABLED, bd=0, relief="flat",
                                bg="#1a1a2e", fg="#e8e8f0",
                                insertbackground="#e8e8f0",
                                selectbackground="#7c5cfc",
                                selectforeground="white",
                                highlightthickness=1,
                                highlightcolor="#2a2a44",
                                highlightbackground="#2a2a44")
        self.log_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        log_sb = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_sb.set)

        log_btns = ttk.Frame(log_tab)
        log_btns.pack(fill=tk.X, pady=6)
        exp_btn = ttk.Button(log_btns, text=self._t("btn.export"), command=self._export_log)
        exp_btn.pack(side=tk.LEFT, padx=2)
        clr_btn = ttk.Button(log_btns, text=self._t("btn.clear"), command=self._clear_log)
        clr_btn.pack(side=tk.LEFT, padx=2)

    def _reset_stats(self):
        self.stat_clicks.set(0)
        self.stat_actions.set(0)
        self.stat_elapsed.set("00:00:00")
        self.stat_cps.set("0.0")
        self.stat_distance.set(0)
        self._session_start = None
        self._fatigue_factor = 1.0
        self._action_count = 0
        self._total_actions_done = 0
        self.fatigue_bar["value"] = 0
        self.fatigue_pct.config(text="0%")
        self.limit_progress["value"] = 0
        self.limit_label.config(text="0/∞")

    def _tick_stats(self):
        if not (self.is_running and self._session_start):
            return
        elapsed = time.time() - self._session_start
        h, rem = divmod(int(elapsed), 3600)
        m, s = divmod(rem, 60)
        self.stat_elapsed.set(f"{h:02}:{m:02}:{s:02}")

        total = self.stat_clicks.get() + self.stat_actions.get()
        self.stat_cps.set(f"{total / max(elapsed, 0.001):.1f}")

        try:
            cx, cy = self.mouse.position
            if self._last_mouse_pos:
                dx, dy = cx - self._last_mouse_pos[0], cy - self._last_mouse_pos[1]
                self.stat_distance.set(self.stat_distance.get() + int(math.hypot(dx, dy)))
            self._last_mouse_pos = (cx, cy)
        except Exception:
            pass

        if self.human_like_enabled.get():
            pct = min(100, int((self._fatigue_factor - 1.0) / 0.5 * 100))
            self.fatigue_bar["value"] = pct
            self.fatigue_pct.config(text=f"{pct}%")

        # Лимит
        if self.action_limit_enabled.get():
            try:
                lim = int(self.action_limit_count.get() or 100)
                self.limit_progress["maximum"] = lim
                self.limit_progress["value"] = self._total_actions_done
                self.limit_label.config(text=f"{self._total_actions_done}/{lim}")
            except Exception:
                pass
        else:
            self.limit_label.config(text=f"{self._total_actions_done}/∞")

        self.root.after(1000, self._tick_stats)

    # ── Подвал (MODERN FOOTER) ────────────────────────────────────────────────

    def _build_footer(self, parent):
        ttk.Separator(parent, orient="horizontal").pack(fill=tk.X, pady=(4, 10))

        f = ttk.Frame(parent)
        f.pack(fill=tk.X)

        # Version badge - Современный стиль
        ver_frame = ttk.Frame(f)
        ver_frame.pack(side=tk.LEFT, padx=6)
        
        ttk.Label(ver_frame, text="Mouse Ops",
                  font=("Segoe UI", 9, "bold"),
                  foreground=self.COLORS["text_sec"]).pack(side=tk.LEFT)
        ttk.Label(ver_frame, text=f"  v{self.VERSION}  •  Ultra Modern Edition",
                  font=("Segoe UI", 8),
                  foreground=self.COLORS["text_dim"]).pack(side=tk.LEFT)

        # Profile selector - Современный
        pf = tk.Frame(f, bg=self.COLORS["card"], padx=12, pady=6)
        pf.pack(side=tk.LEFT, padx=20)
        
        tk.Label(pf, text="📋",
                  font=("Segoe UI", 10),
                  bg=self.COLORS["card"],
                  fg=self.COLORS["text_sec"]).pack(side=tk.LEFT, padx=(0, 6))
        
        self.profile_combo = ttk.Combobox(pf, width=18, 
                                          font=("Segoe UI", 9), 
                                          state="readonly")
        self.profile_combo.pack(side=tk.LEFT)
        self.profile_combo.bind("<<ComboboxSelected>>", self._load_profile)
        ToolTip(self.profile_combo, self._t("tip.profile_combo"))
        
        save_btn = ttk.Button(pf, text="💾", width=4, command=self._save_profile)
        save_btn.pack(side=tk.LEFT, padx=6)
        ToolTip(save_btn, self._t("tip.profile_save"))

        # Меню бар
        menubar = tk.Menu(self.root)
        
        file_m = tk.Menu(menubar, tearoff=0)
        file_m.add_command(label=self._t("menu.export_cfg"), command=self._export_cfg)
        file_m.add_command(label=self._t("menu.import_cfg"), command=self._import_cfg)
        file_m.add_separator()
        file_m.add_command(label=self._t("menu.reset_cfg"), command=self._reset_cfg)
        menubar.add_cascade(label=self._t("menu.file_label"), menu=file_m)

        prof_m = tk.Menu(menubar, tearoff=0)
        prof_m.add_command(label=self._t("menu.new_profile"), command=self._new_profile)
        prof_m.add_command(label=self._t("menu.rename_profile"), command=self._rename_profile)
        prof_m.add_command(label=self._t("menu.delete_profile"), command=self._delete_profile)
        menubar.add_cascade(label=self._t("menu.profiles_label"), menu=prof_m)
        self.root.config(menu=menubar)

        # Link - Современный стиль
        lnk_frame = tk.Frame(f, bg=self.COLORS["surface"])
        lnk_frame.pack(side=tk.RIGHT, padx=8)
        
        tk.Label(lnk_frame, text="Made with ❤️  by",
                 font=("Segoe UI", 8),
                 fg=self.COLORS["text_dim"],
                 bg=self.COLORS["surface"]).pack(side=tk.LEFT, padx=4)
        
        lnk = tk.Label(lnk_frame, text="@saylont", 
                        foreground=self.COLORS["accent"],
                        bg=self.COLORS["surface"],
                        cursor="hand2", 
                        font=("Segoe UI", 9, "underline bold"))
        lnk.pack(side=tk.LEFT)
        lnk.bind("<Button-1>", lambda e: webbrowser.open("https://www.tiktok.com/@saylont"))

    # ── Утилиты UI (MODERN) ───────────────────────────────────────────────────

    def _entry(self, parent, default="", width=None):
        """Создать современное поле ввода"""
        kw = {"font": ("Consolas", 11)}
        if width:
            kw["width"] = width
        e = ttk.Entry(parent, **kw)
        e.insert(0, default)
        e.bind("<Return>", lambda ev: self.start_btn.focus_set())
        return e

    # ══════════════════════════════════════════════════════════════════════════
    #                       ОБРАБОТЧИКИ UI
    # ══════════════════════════════════════════════════════════════════════════

    def _clear_focus_on_click(self, event):
        """Снять фокус при клике вне полей ввода.
        Пропускает комбобоксы и их выпадающие списки."""
        try:
            w = event.widget
            if isinstance(w, str):
                return
            wclass = w.winfo_class()
            # Пропускаем поля ввода, списки, комбобоксы и их выпадающие меню
            if wclass in ("TEntry", "Entry", "Listbox", "Text",
                          "TCombobox", "ComboboxPopdown", "TScrollbar"):
                return
        except Exception:
            return
        # Переводим фокус на кнопку, а не на root (иначе фокус перейдёт на первый Entry)
        try:
            self.start_btn.focus_set()
        except Exception:
            pass
        self._save_config()

    def _right_click_global(self, event):
        if self.coords_select_mode and self.coord_select_button.get() == "right":
            self._pick_coord(*self.mouse.position)

    def _set_hotkey(self, event):
        self.hotkey_entry.delete(0, tk.END)
        self.hotkey_entry.insert(0, event.keysym)
        self.hotkey = getattr(pynput_keyboard.Key, event.keysym.lower(),
                              event.keysym.lower())
        self._save_config()
        return "break"

    def _on_movement_change(self):
        mv = self.movement_var.get()
        is_free = (mv == "free")
        # Клик по координатам, Drag & Drop, Маршрут, Имитация — только в режиме «Без движения»
        if not is_free:
            self.fixed_click_enabled.set(False)
            self.drag_enabled.set(False)
            self.human_like_enabled.set(False)
            self.notebook.tab(self._coords_tab, state='disabled')
            self.notebook.tab(self._human_tab, state='disabled')
            self.macros_notebook.tab(self._route_tab, state='disabled')
            self._set_frame_state(self._dd_frame, 'disabled')
        else:
            self.notebook.tab(self._coords_tab, state='normal')
            self.notebook.tab(self._human_tab, state='normal')
            self.macros_notebook.tab(self._route_tab, state='normal')
            self._set_frame_state(self._dd_frame, 'normal')
        self._on_fixed_click_toggle()
        self._on_drag_toggle()
        self._on_human_toggle()
        self._save_config()

    def _on_action_type_change(self):
        if self.action_type.get() == "keyboard":
            self.kb_key_frame.pack(fill=tk.X, pady=(4, 0))
        else:
            self.kb_key_frame.pack_forget()
        self._save_config()

    def _on_fixed_click_toggle(self):
        if self.fixed_click_enabled.get():
            self._coords_container.pack(fill=tk.BOTH, expand=True)
        else:
            self._coords_container.pack_forget()
        self._save_config()

    def _on_limit_toggle(self):
        if self.action_limit_enabled.get():
            self._limit_container.pack(fill=tk.X, pady=(4, 0))
        else:
            self._limit_container.pack_forget()
        self._save_config()

    def _on_clicker_toggle(self):
        if self.auto_clicker_enabled.get():
            self._clicker_container.pack(fill=tk.X)
        else:
            self._clicker_container.pack_forget()
        self._save_config()

    def _on_drag_toggle(self):
        if self.drag_enabled.get():
            self._drag_container.pack(fill=tk.X, pady=(4, 0))
        else:
            self._drag_container.pack_forget()
        self._save_config()

    def _on_afk_toggle(self):
        if self.anti_afk_enabled.get():
            self._afk_container.pack(fill=tk.X, pady=(4, 0))
        else:
            self._afk_container.pack_forget()
        self._save_config()

    def _on_sound_toggle(self):
        if self.sound_enabled.get():
            self._sound_container.pack(fill=tk.X, pady=(4, 0))
        else:
            self._sound_container.pack_forget()
        self._save_config()

    def _on_tray_toggle(self):
        if self.tray_enabled.get():
            self._tray_container.pack(fill=tk.X, pady=(4, 0))
        else:
            self._tray_container.pack_forget()
        self._save_config()

    def _set_frame_state(self, frame, state):
        """Recursively set state on all children widgets."""
        for child in frame.winfo_children():
            try:
                child.configure(state=state)
            except (tk.TclError, AttributeError):
                pass
            self._set_frame_state(child, state)

    def _on_human_toggle(self):
        if self.human_like_enabled.get():
            self._human_container.pack(fill=tk.BOTH, expand=True)
        else:
            self._human_container.pack_forget()
        self._save_config()

    # ══════════════════════════════════════════════════════════════════════════
    #                   ВЫБОР КООРДИНАТ — полноэкранный оверлей
    # ══════════════════════════════════════════════════════════════════════════

    def _start_coord_selection(self):
        self.coords_select_mode = True
        self._coord_callback = None
        self._show_fullscreen_crosshair()

    def _pick_for_var(self, var_x, var_y):
        """Выбор координат для любых двух переменных."""
        self.coords_select_mode = True
        self._coord_callback = (var_x, var_y)
        self._show_fullscreen_crosshair()

    def _show_fullscreen_crosshair(self):
        self._destroy_coord_windows()
        try:
            u32 = ctypes.windll.user32
            sw, sh = u32.GetSystemMetrics(0), u32.GetSystemMetrics(1)
        except Exception:
            sw, sh = 1920, 1080

        overlay = tk.Toplevel(self.root)
        overlay.attributes("-fullscreen", True)
        overlay.attributes("-topmost", True)
        overlay.attributes("-alpha", 0.01)
        overlay.configure(bg="#000001")
        overlay.config(cursor="crosshair")
        self._coord_windows.append(overlay)

        if self.coord_select_button.get() == "left":
            overlay.bind("<Button-1>", self._overlay_click)
        else:
            overlay.bind("<Button-3>", self._overlay_click)
        overlay.bind("<Escape>", self._cancel_coord_selection)
        overlay.focus_force()

        h_line = tk.Toplevel(self.root)
        h_line.overrideredirect(True)
        h_line.attributes("-topmost", True)
        h_line.attributes("-alpha", 0.45)
        h_line.configure(bg="#7c5cfc")
        h_line.geometry(f"{sw}x1")
        self._h_line = h_line
        self._coord_windows.append(h_line)

        v_line = tk.Toplevel(self.root)
        v_line.overrideredirect(True)
        v_line.attributes("-topmost", True)
        v_line.attributes("-alpha", 0.45)
        v_line.configure(bg="#7c5cfc")
        v_line.geometry(f"1x{sh}")
        self._v_line = v_line
        self._coord_windows.append(v_line)

        cross = tk.Toplevel(self.root)
        cross.overrideredirect(True)
        cross.attributes("-topmost", True)
        cross.attributes("-alpha", 0.65)
        cross.configure(bg="#000001")
        cross.attributes("-transparentcolor", "#000001")
        self._cross_win = cross
        self._coord_windows.append(cross)
        sz = 40
        cv = tk.Canvas(cross, width=sz*2, height=sz*2, bg="#000001", highlightthickness=0)
        cv.pack()
        cv.create_line(sz, 0, sz, sz*2, fill="#00d4aa", width=2, dash=(6, 3))
        cv.create_line(0, sz, sz*2, sz, fill="#00d4aa", width=2, dash=(6, 3))
        cv.create_oval(sz-8, sz-8, sz+8, sz+8, outline="#7c5cfc", width=2)
        cv.create_oval(sz-2, sz-2, sz+2, sz+2, fill="#7c5cfc", outline="")

        info = tk.Toplevel(self.root)
        info.overrideredirect(True)
        info.attributes("-topmost", True)
        info.attributes("-alpha", 0.92)
        info.configure(bg="#0b0b14")
        self._info_win = info
        self._coord_windows.append(info)

        hdr = tk.Frame(info, bg="#12121e", padx=10, pady=6)
        hdr.pack(fill=tk.X)
        btn_name = self._t("act.left") if self.coord_select_button.get() == "left" else self._t("act.right")
        tk.Label(hdr, text=self._t("overlay.pick_hint").format(btn=btn_name),
                 bg="#12121e", fg="#7c5cfc", font=("Segoe UI", 10, "bold")).pack()

        cf = tk.Frame(info, bg="#0b0b14", padx=12, pady=8)
        cf.pack(fill=tk.X)
        self._ov_x = tk.Label(cf, text=self._t("lbl.x_val").format(x=0), bg="#0b0b14", fg="#00d4aa",
                              font=("Consolas", 18, "bold"), anchor="w")
        self._ov_x.pack(side=tk.LEFT, padx=(0, 24))
        self._ov_y = tk.Label(cf, text=self._t("lbl.y_val").format(y=0), bg="#0b0b14", fg="#ff6b9d",
                              font=("Consolas", 18, "bold"), anchor="w")
        self._ov_y.pack(side=tk.LEFT)

        ef = tk.Frame(info, bg="#0b0b14", padx=12, pady=4)
        ef.pack(fill=tk.X)
        self._ov_extra = tk.Label(ef, text=self._t("lbl.screen_format").format(w=sw, h=sh),
                                   bg="#0b0b14", fg="#555570", font=("Consolas", 9))
        self._ov_extra.pack(anchor="w")

        self._screen_w, self._screen_h = sw, sh
        self._update_crosshair()

    def _overlay_click(self, event):
        if self.coords_select_mode:
            x, y = self.mouse.position
            if hasattr(self, '_coord_callback') and self._coord_callback:
                cb = self._coord_callback
                self._coord_callback = None
                self._cancel_coord_selection()
                if isinstance(cb, tuple) and cb[0] == "__route__":
                    delay = getattr(self, '_route_pending_delay', 500)
                    self.route_points.append({"x": x, "y": y, "delay": delay, "action": "click"})
                    self._route_refresh()
                elif isinstance(cb, tuple) and len(cb) == 2:
                    var_x, var_y = cb
                    var_x.set(str(x))
                    var_y.set(str(y))
            else:
                self._pick_coord(x, y)

    def _update_crosshair(self):
        if not self.coords_select_mode:
            return
        try:
            x, y = self.mouse.position
            if hasattr(self, '_info_win') and self._info_win.winfo_exists():
                iw = 280
                ix = x - iw - 30 if x + 50 + iw > self._screen_w else x + 30
                iy = y + 30 if y + 130 < self._screen_h else y - 100
                self._info_win.geometry(f"+{ix}+{iy}")
                self._ov_x.config(text=self._t("lbl.x_val").format(x=x))
                self._ov_y.config(text=self._t("lbl.y_val").format(y=y))
                pct_x = x * 100 // max(self._screen_w, 1)
                pct_y = y * 100 // max(self._screen_h, 1)
                self._ov_extra.config(
                    text=self._t("lbl.screen_detail").format(w=self._screen_w, h=self._screen_h, x=pct_x, y=pct_y))
            if hasattr(self, '_cross_win') and self._cross_win.winfo_exists():
                self._cross_win.geometry(f"+{x-40}+{y-40}")
            if hasattr(self, '_h_line') and self._h_line.winfo_exists():
                self._h_line.geometry(f"+0+{y}")
            if hasattr(self, '_v_line') and self._v_line.winfo_exists():
                self._v_line.geometry(f"+{x}+0")
        except Exception:
            pass
        self.root.after(16, self._update_crosshair)

    def _pick_coord(self, x, y):
        self.fixed_x.set(str(x))
        self.fixed_y.set(str(y))
        self.coords_set = True
        self.coord_info_lbl.config(text=f"✅ X={x}, Y={y}", foreground="#00d4aa")

        ts = datetime.now().strftime("%H:%M:%S")
        entry = {"x": x, "y": y, "label": f"X={x:>5}, Y={y:>5}  [{ts}]"}
        if not self.coords_history or \
                (self.coords_history[0]["x"] != x or self.coords_history[0]["y"] != y):
            self.coords_history.insert(0, entry)
            if len(self.coords_history) > 20:
                self.coords_history.pop()
            self._update_coords_history_ui()
            self._save_coords_history()

        self._cancel_coord_selection()
        self._save_config()

    def _cancel_coord_selection(self, event=None):
        self.coords_select_mode = False
        self._coord_callback = None
        self._destroy_coord_windows()

    def _destroy_coord_windows(self):
        for w in self._coord_windows:
            try:
                w.destroy()
            except Exception:
                pass
        self._coord_windows.clear()

    def _grab_current_pos(self):
        x, y = self.mouse.position
        self.fixed_x.set(str(x))
        self.fixed_y.set(str(y))
        self.coords_set = True
        self.coord_info_lbl.config(text=f"✅ X={x}, Y={y}", foreground="#00d4aa")

        ts = datetime.now().strftime("%H:%M:%S")
        entry = {"x": x, "y": y, "label": f"X={x:>5}, Y={y:>5}  [{ts}]"}
        if not self.coords_history or \
                (self.coords_history[0]["x"] != x or self.coords_history[0]["y"] != y):
            self.coords_history.insert(0, entry)
            if len(self.coords_history) > 20:
                self.coords_history.pop()
            self._update_coords_history_ui()
            self._save_coords_history()
        self._save_config()

    def _test_click_at_coords(self):
        try:
            x, y = int(self.fixed_x.get()), int(self.fixed_y.get())
        except ValueError:
            messagebox.showerror(self._t("title.error"), self._t("msg.bad_coords_err"))
            return
        old = self.mouse.position
        self.mouse.position = (x, y)
        time.sleep(0.05)
        self.mouse.click(Button.left)
        time.sleep(0.3)
        self.mouse.position = old
        self.coord_info_lbl.config(text=self._t("coord.test_result").format(x=x, y=y), foreground="#00d4aa")

    def _load_coords_from_history(self, event=None):
        self._load_selected_coords()

    def _load_selected_coords(self):
        sel = self.coords_history_listbox.curselection()
        if not sel or sel[0] >= len(self.coords_history):
            return
        c = self.coords_history[sel[0]]
        self.fixed_x.set(str(c["x"]))
        self.fixed_y.set(str(c["y"]))
        self.coords_set = True
        self.coord_info_lbl.config(text=f"📥 X={c['x']}, Y={c['y']}", foreground="#00d4aa")
        self._save_config()

    def _delete_coord_from_history(self):
        sel = self.coords_history_listbox.curselection()
        if sel and sel[0] < len(self.coords_history):
            self.coords_history.pop(sel[0])
            self._update_coords_history_ui()
            self._save_coords_history()

    def _clear_coords_history(self):
        if messagebox.askyesno(self._t("title.confirm"), self._t("msg.clear_history_confirm")):
            self.coords_history.clear()
            self._update_coords_history_ui()
            self._save_coords_history()

    def _update_coords_history_ui(self):
        self.coords_history_listbox.delete(0, tk.END)
        for c in self.coords_history:
            self.coords_history_listbox.insert(tk.END, c["label"])

    def _save_coords_history(self):
        try:
            with open(self.COORDS_HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.coords_history, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _load_coords_history(self):
        try:
            if os.path.exists(self.COORDS_HISTORY_FILE):
                with open(self.COORDS_HISTORY_FILE, "r", encoding="utf-8") as f:
                    self.coords_history = json.load(f)
                    self._update_coords_history_ui()
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    #                       МАКРОСЫ — Конструктор
    # ══════════════════════════════════════════════════════════════════════════

    def _macro_step_label(self, step):
        t = step.get("type", "?")
        if t == "click":
            return f"🖱 Клик {step.get('button','left').upper()} в ({step.get('x',0)}, {step.get('y',0)})"
        elif t == "key":
            return f"⌨ Клавиша [{step.get('key','?')}]"
        elif t == "delay":
            return f"⏱ Пауза {step.get('delay',0)} мс"
        elif t == "move":
            return f"↗ Переместить в ({step.get('x',0)}, {step.get('y',0)})"
        elif t == "drag":
            return f"🔃 Drag ({step.get('x1',0)},{step.get('y1',0)})→({step.get('x2',0)},{step.get('y2',0)})"
        return f"? {t}"

    def _macro_refresh_list(self):
        self.macro_listbox.delete(0, tk.END)
        for i, step in enumerate(self.macro_steps):
            self.macro_listbox.insert(tk.END, f"{i+1}. {self._macro_step_label(step)}")

    def _macro_add_click(self):
        x, y = self.mouse.position
        xs = simpledialog.askstring(self._t("dialog.click_title"), self._t("dialog.x_coord"), initialvalue=str(x))
        if xs is None:
            return
        ys = simpledialog.askstring(self._t("dialog.click_title"), self._t("dialog.y_coord"), initialvalue=str(y))
        if ys is None:
            return
        btn = simpledialog.askstring(self._t("dialog.click_title"), self._t("dialog.button"), initialvalue="left")
        if btn is None:
            return
        self.macro_steps.append({"type": "click", "x": int(xs), "y": int(ys), "button": btn or "left"})
        self._macro_refresh_list()

    def _macro_add_key(self):
        k = simpledialog.askstring(self._t("dialog.key_title"), self._t("dialog.key_name"), initialvalue="space")
        if k:
            self.macro_steps.append({"type": "key", "key": k.strip()})
            self._macro_refresh_list()

    def _macro_add_delay(self):
        d = simpledialog.askstring(self._t("dialog.pause_title"), self._t("dialog.pause_duration"), initialvalue="500")
        if d:
            self.macro_steps.append({"type": "delay", "delay": int(d)})
            self._macro_refresh_list()

    def _macro_add_move(self):
        x, y = self.mouse.position
        xs = simpledialog.askstring(self._t("dialog.move_title"), self._t("lbl.x"), initialvalue=str(x))
        if xs is None:
            return
        ys = simpledialog.askstring(self._t("dialog.move_title"), self._t("lbl.y"), initialvalue=str(y))
        if ys is None:
            return
        self.macro_steps.append({"type": "move", "x": int(xs), "y": int(ys)})
        self._macro_refresh_list()

    def _macro_add_drag(self):
        x, y = self.mouse.position
        x1 = simpledialog.askstring(self._t("dialog.drag_start"), "X1:", initialvalue=str(x))
        if x1 is None:
            return
        y1 = simpledialog.askstring(self._t("dialog.drag_start"), "Y1:", initialvalue=str(y))
        if y1 is None:
            return
        x2 = simpledialog.askstring(self._t("dialog.drag_end"), "X2:", initialvalue=str(x))
        if x2 is None:
            return
        y2 = simpledialog.askstring(self._t("dialog.drag_end"), "Y2:", initialvalue=str(y))
        if y2 is None:
            return
        self.macro_steps.append({"type": "drag", "x1": int(x1), "y1": int(y1),
                                  "x2": int(x2), "y2": int(y2)})
        self._macro_refresh_list()

    def _macro_move_up(self):
        sel = self.macro_listbox.curselection()
        if sel and sel[0] > 0:
            i = sel[0]
            self.macro_steps[i], self.macro_steps[i-1] = self.macro_steps[i-1], self.macro_steps[i]
            self._macro_refresh_list()
            self.macro_listbox.selection_set(i-1)

    def _macro_move_down(self):
        sel = self.macro_listbox.curselection()
        if sel and sel[0] < len(self.macro_steps) - 1:
            i = sel[0]
            self.macro_steps[i], self.macro_steps[i+1] = self.macro_steps[i+1], self.macro_steps[i]
            self._macro_refresh_list()
            self.macro_listbox.selection_set(i+1)

    def _macro_edit_step(self):
        sel = self.macro_listbox.curselection()
        if not sel or sel[0] >= len(self.macro_steps):
            return
        step = self.macro_steps[sel[0]]
        t = step["type"]
        if t == "click":
            xs = simpledialog.askstring(self._t("dialog.edit_title"), self._t("lbl.x"), initialvalue=str(step["x"]))
            if xs is None:
                return
            ys = simpledialog.askstring(self._t("dialog.edit_title"), self._t("lbl.y"), initialvalue=str(step["y"]))
            if ys is None:
                return
            step["x"], step["y"] = int(xs), int(ys)
        elif t == "key":
            k = simpledialog.askstring(self._t("dialog.edit_title"), self._t("dialog.key_name").replace(" (space, enter, a, f1…):", ":"), initialvalue=step["key"])
            if k:
                step["key"] = k.strip()
        elif t == "delay":
            d = simpledialog.askstring(self._t("dialog.edit_title"), self._t("dialog.pause_duration"), initialvalue=str(step["delay"]))
            if d:
                step["delay"] = int(d)
        elif t == "move":
            xs = simpledialog.askstring(self._t("dialog.edit_title"), self._t("lbl.x"), initialvalue=str(step["x"]))
            if xs is None:
                return
            ys = simpledialog.askstring(self._t("dialog.edit_title"), self._t("lbl.y"), initialvalue=str(step["y"]))
            if ys is None:
                return
            step["x"], step["y"] = int(xs), int(ys)
        self._macro_refresh_list()

    def _macro_delete_step(self):
        sel = self.macro_listbox.curselection()
        if sel and sel[0] < len(self.macro_steps):
            self.macro_steps.pop(sel[0])
            self._macro_refresh_list()

    def _macro_clear(self):
        self.macro_steps.clear()
        self._macro_refresh_list()

    def _macro_save(self):
        name = self.macro_name_combo.get().strip()
        if not name:
            name = simpledialog.askstring(self._t("dialog.save_macro_title"), self._t("dialog.macro_name"))
        if not name:
            return
        self.saved_macros[name] = list(self.macro_steps)
        self._save_macros()
        self.macro_name_combo["values"] = list(self.saved_macros.keys())
        self.macro_name_combo.set(name)
        messagebox.showinfo(self._t("title.done"), self._t("msg.macro_saved_detail").format(name=name, n=len(self.macro_steps)))

    def _macro_load_selected(self, event=None):
        name = self.macro_name_combo.get()
        if name in self.saved_macros:
            self.macro_steps = list(self.saved_macros[name])
            self._macro_refresh_list()

    def _macro_delete_saved(self):
        name = self.macro_name_combo.get()
        if name and name in self.saved_macros:
            if messagebox.askyesno(self._t("title.delete"), self._t("msg.delete_macro_confirm").format(name=name)):
                del self.saved_macros[name]
                self._save_macros()
                self.macro_name_combo["values"] = list(self.saved_macros.keys())
                self.macro_name_combo.set("")

    def _save_macros(self):
        try:
            with open(self.MACROS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.saved_macros, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _load_macros(self):
        try:
            if os.path.exists(self.MACROS_FILE):
                with open(self.MACROS_FILE, "r", encoding="utf-8") as f:
                    self.saved_macros = json.load(f)
                self.macro_name_combo["values"] = list(self.saved_macros.keys())
        except Exception:
            pass

    # ── Воспроизведение макроса ────────────────────────────────────────────────

    def _macro_play(self):
        if not self.macro_steps:
            messagebox.showwarning(self._t("title.macro"), self._t("msg.no_steps_warn"))
            return
        try:
            repeats = max(1, int(self.macro_repeats.get() or 1))
        except ValueError:
            repeats = 1

        self.is_running = True
        self.stop_event.clear()
        self._session_start = time.time()
        self._total_actions_done = 0
        self._tick_stats()
        self._play_sound("start")

        self.start_btn.config(text=self._t("btn.stop"))
        self.status_dot.config(text=self._t("status.macro"), foreground="#ff6b9d")
        self._update_status_dot("#ff6b9d")

        threading.Thread(target=self._macro_execute, args=(repeats,), daemon=True).start()

    def _macro_execute(self, repeats):
        btn_map = {"left": Button.left, "right": Button.right, "middle": Button.middle}
        for rep in range(repeats):
            for step in self.macro_steps:
                if not self.is_running or self.stop_event.is_set():
                    break
                if self._check_action_limit():
                    break
                t = step["type"]
                try:
                    if t == "click":
                        self.mouse.position = (step["x"], step["y"])
                        time.sleep(0.02)
                        self.mouse.click(btn_map.get(step.get("button", "left"), Button.left))
                        self._safe_inc(self.stat_clicks)
                        self._total_actions_done += 1
                        self._log_action(f"Клик {step.get('button','left')} в ({step['x']}, {step['y']})")
                    elif t == "key":
                        self._press_key(step["key"])
                        self._safe_inc(self.stat_actions)
                        self._total_actions_done += 1
                        self._log_action(f"Клавиша [{step['key']}]")
                    elif t == "delay":
                        time.sleep(step["delay"] / 1000)
                    elif t == "move":
                        self.mouse.position = (step["x"], step["y"])
                        self._log_action(f"Переместить в ({step['x']}, {step['y']})")
                    elif t == "drag":
                        self._do_drag(step["x1"], step["y1"], step["x2"], step["y2"])
                        self._safe_inc(self.stat_clicks)
                        self._total_actions_done += 1
                        self._log_action(f"Drag ({step['x1']},{step['y1']})→({step['x2']},{step['y2']})")
                except Exception as e:
                    self._log_action(f"ОШИБКА: {e}")
            if not self.is_running:
                break
        self.root.after(0, self._stop)

    def _macro_stop(self):
        self._stop()

    # ══════════════════════════════════════════════════════════════════════════
    #                   ЗАПИСЬ ДЕЙСТВИЙ
    # ══════════════════════════════════════════════════════════════════════════

    def _rec_start(self):
        self.is_recording = True
        self.recorded_events.clear()
        self.rec_listbox.delete(0, tk.END)
        self._rec_start_time = time.time()
        self.rec_btn.config(state="disabled")
        self.rec_stop_btn.config(state="normal")
        self.rec_status.config(text=self._t("status.recording"), foreground="#ff5c5c")

        self._rec_mouse_listener = MouseListener(
            on_click=self._rec_on_click, on_move=self._rec_on_move)
        self._rec_mouse_listener.start()

        self._rec_kb_listener = KBListener(on_press=self._rec_on_key)
        self._rec_kb_listener.start()

    def _rec_stop(self):
        self.is_recording = False
        self.rec_btn.config(state="normal")
        self.rec_stop_btn.config(state="disabled")
        self.rec_status.config(
            text=self._t("status.recorded_n").format(n=len(self.recorded_events)), foreground=self.COLORS["text_dim"])

        if self._rec_mouse_listener:
            self._rec_mouse_listener.stop()
            self._rec_mouse_listener = None
        if self._rec_kb_listener:
            self._rec_kb_listener.stop()
            self._rec_kb_listener = None

    def _rec_on_click(self, x, y, button, pressed):
        if not self.is_recording or not pressed:
            return
        dt = int((time.time() - self._rec_start_time) * 1000)
        btn_name = "left" if button == Button.left else "right" if button == Button.right else "middle"
        ev = {"type": "click", "x": x, "y": y, "button": btn_name, "time_ms": dt}
        self.recorded_events.append(ev)
        self.root.after(0, lambda: self.rec_listbox.insert(
            tk.END, f"[{dt:>6}ms] 🖱 {btn_name} ({x}, {y})"))

    def _rec_on_move(self, x, y):
        pass  # не записываем каждое перемещение (слишком много)

    def _rec_on_key(self, key):
        if not self.is_recording:
            return
        dt = int((time.time() - self._rec_start_time) * 1000)
        try:
            k = key.char if hasattr(key, 'char') and key.char else key.name
        except Exception:
            k = str(key)
        # Не записываем Escape (используется для стопа)
        if k == 'escape':
            self.root.after(0, self._rec_stop)
            return
        ev = {"type": "key", "key": k, "time_ms": dt}
        self.recorded_events.append(ev)
        self.root.after(0, lambda: self.rec_listbox.insert(
            tk.END, f"[{dt:>6}ms] ⌨ [{k}]"))

    def _rec_to_builder(self):
        if not self.recorded_events:
            messagebox.showinfo(self._t("title.empty"), self._t("msg.no_events_info"))
            return
        self.macro_steps.clear()
        prev_time = 0
        for ev in self.recorded_events:
            dt = ev.get("time_ms", 0) - prev_time
            if dt > 50:
                self.macro_steps.append({"type": "delay", "delay": dt})
            if ev["type"] == "click":
                self.macro_steps.append({"type": "click", "x": ev["x"], "y": ev["y"],
                                          "button": ev.get("button", "left")})
            elif ev["type"] == "key":
                self.macro_steps.append({"type": "key", "key": ev["key"]})
            prev_time = ev.get("time_ms", 0)
        self._macro_refresh_list()
        messagebox.showinfo(self._t("title.done"), self._t("msg.rec_converted_detail").format(n=len(self.macro_steps)))

    # ══════════════════════════════════════════════════════════════════════════
    #                   МУЛЬТИ-МАРШРУТ
    # ══════════════════════════════════════════════════════════════════════════

    def _route_refresh(self):
        self.route_listbox.delete(0, tk.END)
        for i, pt in enumerate(self.route_points):
            self.route_listbox.insert(
                tk.END, f"{i+1}. X={pt['x']}, Y={pt['y']}  | "
                         f"Задержка: {pt.get('delay',500)}мс  | {pt.get('action','click')}")

    def _route_add_pick(self):
        """Добавить точку через полноэкранный выбор."""
        delay = simpledialog.askstring(self._t("dialog.delay_title"), self._t("dialog.delay_after_click"), initialvalue="500")
        if delay is None:
            return
        self._route_pending_delay = int(delay or 500)
        self.coords_select_mode = True
        self._coord_callback = ("__route__", None)
        self._show_fullscreen_crosshair()

    def _route_add_current(self):
        x, y = self.mouse.position
        delay = simpledialog.askstring(self._t("dialog.delay_title"), self._t("dialog.delay_after_click"), initialvalue="500")
        if delay is None:
            return
        self.route_points.append({"x": x, "y": y, "delay": int(delay or 500), "action": "click"})
        self._route_refresh()

    def _route_edit(self):
        sel = self.route_listbox.curselection()
        if not sel or sel[0] >= len(self.route_points):
            return
        pt = self.route_points[sel[0]]
        xs = simpledialog.askstring(self._t("dialog.edit_title"), self._t("lbl.x"), initialvalue=str(pt["x"]))
        if xs is None:
            return
        ys = simpledialog.askstring(self._t("dialog.edit_title"), self._t("lbl.y"), initialvalue=str(pt["y"]))
        if ys is None:
            return
        ds = simpledialog.askstring(self._t("dialog.edit_title"), self._t("dialog.delay_title"), initialvalue=str(pt.get("delay", 500)))
        if ds is None:
            return
        pt["x"], pt["y"], pt["delay"] = int(xs), int(ys), int(ds)
        self._route_refresh()

    def _route_delete(self):
        sel = self.route_listbox.curselection()
        if sel and sel[0] < len(self.route_points):
            self.route_points.pop(sel[0])
            self._route_refresh()

    def _route_clear(self):
        self.route_points.clear()
        self._route_refresh()

    def _route_play(self):
        if not self.route_points:
            messagebox.showwarning(self._t("title.route"), self._t("msg.no_points_warn"))
            return
        try:
            repeats = max(1, int(self.route_repeats.get() or 1))
        except ValueError:
            repeats = 1

        self.is_running = True
        self.stop_event.clear()
        self._session_start = time.time()
        self._total_actions_done = 0
        self._tick_stats()
        self._play_sound("start")
        self.start_btn.config(text=self._t("btn.stop"))
        self.status_dot.config(text=self._t("status.route"), foreground="#7c5cfc")
        self._update_status_dot("#7c5cfc")

        threading.Thread(target=self._route_execute, args=(repeats,), daemon=True).start()

    def _route_execute(self, repeats):
        for rep in range(repeats):
            for pt in self.route_points:
                if not self.is_running or self.stop_event.is_set():
                    break
                if self._check_action_limit():
                    break
                self.mouse.position = (pt["x"], pt["y"])
                time.sleep(0.03)
                if pt.get("action", "click") == "click":
                    self.mouse.click(Button.left)
                    self._safe_inc(self.stat_clicks)
                    self._total_actions_done += 1
                    self._log_action(f"Маршрут: клик в ({pt['x']}, {pt['y']})")
                time.sleep(pt.get("delay", 500) / 1000)
            if not self.is_running:
                break
        self.root.after(0, self._stop)

    # ══════════════════════════════════════════════════════════════════════════
    #                       ИНСТРУМЕНТЫ
    # ══════════════════════════════════════════════════════════════════════════

    # ── Drag & Drop ──

    def _do_drag(self, x1, y1, x2, y2):
        """Перетащить: зажать ЛКМ в (x1,y1), переместить в (x2,y2), отпустить."""
        self.mouse.position = (x1, y1)
        time.sleep(0.05)
        self.mouse.press(Button.left)
        steps = max(10, int(math.hypot(x2 - x1, y2 - y1) / 5))
        for i in range(1, steps + 1):
            t = i / steps
            self.mouse.position = (int(x1 + (x2 - x1) * t), int(y1 + (y2 - y1) * t))
            time.sleep(0.01)
        self.mouse.release(Button.left)

    def _test_drag(self):
        try:
            x1 = int(self.drag_start_x.get())
            y1 = int(self.drag_start_y.get())
            x2 = int(self.drag_end_x.get())
            y2 = int(self.drag_end_y.get())
        except ValueError:
            messagebox.showerror(self._t("title.error"), self._t("msg.bad_coords_err"))
            return
        threading.Thread(target=self._do_drag, args=(x1, y1, x2, y2), daemon=True).start()

    # ── Anti-AFK ──

    def _anti_afk_loop(self):
        try:
            interval = max(5, int(self.anti_afk_interval.get() or 30))
        except ValueError:
            interval = 30
        keys = ['w', 'a', 's', 'd', 'space']
        while self.is_running and not self.stop_event.is_set():
            time.sleep(interval * random.uniform(0.7, 1.3))
            if not self.is_running:
                break
            action = random.choice(["key", "mouse_move"])
            if action == "key":
                k = random.choice(keys)
                try:
                    key = getattr(pynput_keyboard.Key, k, None)
                    if key is None:
                        key = pynput_keyboard.KeyCode.from_char(k)
                    self.kb_ctrl.press(key)
                    time.sleep(random.uniform(0.05, 0.2))
                    self.kb_ctrl.release(key)
                    self._log_action(f"Anti-AFK: нажал [{k}]")
                except Exception:
                    pass
            else:
                cx, cy = self.mouse.position
                dx, dy = random.randint(-30, 30), random.randint(-30, 30)
                self.mouse.position = (cx + dx, cy + dy)
                time.sleep(0.1)
                self.mouse.position = (cx, cy)
                self._log_action(f"Anti-AFK: двинул мышь ±{abs(dx)},{abs(dy)}")

    # ── Звук ──

    def _play_sound(self, event_type):
        if not self.sound_enabled.get():
            return
        threading.Thread(target=self._play_sound_worker, args=(event_type,), daemon=True).start()

    def _generate_beep(self, frequency, duration_ms):
        """Generate WAV beep in memory with current volume."""
        sample_rate = 22050
        n_samples = int(sample_rate * duration_ms / 1000)
        volume = max(0, min(100, self.sound_volume.get())) / 100.0
        samples = []
        for i in range(n_samples):
            val = int(32767 * volume * math.sin(2 * math.pi * frequency * i / sample_rate))
            samples.append(val)
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sample_rate)
            w.writeframes(struct.pack(f'<{n_samples}h', *samples))
        return buf.getvalue()

    def _play_beep(self, frequency, duration_ms):
        """Play beep with current volume."""
        try:
            data = self._generate_beep(frequency, duration_ms)
            winsound.PlaySound(data, winsound.SND_MEMORY)
        except Exception:
            pass

    def _play_sound_worker(self, event_type):
        try:
            if event_type == "start":
                self._play_beep(800, 150)
                self._play_beep(1000, 100)
            elif event_type == "stop":
                self._play_beep(600, 150)
                self._play_beep(400, 100)
            elif event_type == "finish":
                self._play_beep(1000, 100)
                self._play_beep(1200, 100)
                self._play_beep(1500, 200)
            elif event_type == "startup":
                self._play_beep(600, 80)
                self._play_beep(800, 80)
                self._play_beep(1000, 120)
        except Exception:
            pass

    def _test_sound(self):
        self._play_sound("finish")

    # ── Лог действий ──

    def _log_action(self, msg):
        ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        entry = f"[{ts}] {msg}"
        self.action_log.append(entry)
        try:
            self.root.after(0, self._append_log_ui, entry)
        except Exception:
            pass

    def _append_log_ui(self, entry):
        try:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, entry + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        except Exception:
            pass

    def _export_log(self):
        p = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("Text", "*.txt")],
            initialfile="mouse_ops_log.txt")
        if p:
            try:
                with open(p, "w", encoding="utf-8") as f:
                    for line in self.action_log:
                        f.write(line + "\n")
                messagebox.showinfo(self._t("title.done"), self._t("msg.export_log_detail").format(n=len(self.action_log)))
            except Exception as e:
                messagebox.showerror(self._t("title.error"), str(e))

    def _clear_log(self):
        self.action_log.clear()
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)

    # ══════════════════════════════════════════════════════════════════════════
    #                   ПРЕДПРОСМОТР ТРАЕКТОРИИ
    # ══════════════════════════════════════════════════════════════════════════

    def _preview_trajectory(self):
        c = self.preview_canvas
        c.delete("all")
        w, h = c.winfo_width() or 380, c.winfo_height() or 200
        cx, cy = w // 2, h // 2
        r = min(w, h) // 3

        saved = self.human_like_enabled.get()
        self.human_like_enabled.set(True)
        self._cache_human_params()

        mv = self.movement_var.get()
        pts = []
        if mv == "circle":
            for i in range(61):
                a = (i / 60) * 2 * math.pi
                pts.append(self._apply_tremor(cx + int(r * math.cos(a)),
                                              cy + int(r * math.sin(a))))
        elif mv == "eight":
            for i in range(81):
                t = (i / 80) * 2 * math.pi
                pts.append(self._apply_tremor(cx + int(r * math.sin(t)),
                                              cy + int(r * 0.6 * math.sin(2 * t))))
        elif mv == "square":
            corners = [(cx-r, cy-r), (cx+r, cy-r), (cx+r, cy+r), (cx-r, cy+r)]
            for i in range(4):
                ni = (i + 1) % 4
                pts += self._bezier_points(corners[i][0], corners[i][1],
                                           corners[ni][0], corners[ni][1], n=15)
        else:
            pts = (self._bezier_points(cx - r, cy, cx + r, cy, n=30) +
                   self._bezier_points(cx + r, cy, cx - r, cy, n=30))

        self.human_like_enabled.set(saved)

        for i in range(1, len(pts)):
            frac = i / len(pts)
            cr0 = int(124 + 131 * frac)
            cg0 = int(92 + 120 * (1 - frac))
            cb0 = int(252 - 82 * frac)
            c.create_line(pts[i-1][0], pts[i-1][1], pts[i][0], pts[i][1],
                         fill=f"#{cr0:02x}{cg0:02x}{cb0:02x}", width=2)

        if pts:
            c.create_oval(pts[0][0]-4, pts[0][1]-4, pts[0][0]+4, pts[0][1]+4,
                         fill="#00d4aa", outline="")
            c.create_text(pts[0][0], pts[0][1]-12, text=self._t("canvas.start"),
                         fill="#00d4aa", font=("Consolas", 7))
            c.create_oval(pts[-1][0]-4, pts[-1][1]-4, pts[-1][0]+4, pts[-1][1]+4,
                         fill="#ff6b9d", outline="")

        self.preview_info.config(
            text=self._t("human.preview_info").format(
                c=self.curviness.get(), t=self.hand_tremor.get(),
                o=self.overshoot_level.get()))

    # ══════════════════════════════════════════════════════════════════════════
    #                       ЗАПУСК / ОСТАНОВКА
    # ══════════════════════════════════════════════════════════════════════════

    def toggle(self):
        if self.is_running:
            self._stop()
        else:
            self._start()

    def _start(self):
        try:
            self.radius = max(1, min(2000, int(self.radius_entry.get() or "30")))
            self.mouse_delay = max(1, min(60000, int(self.mouse_delay_entry.get() or "50"))) / 1000
            self.click_delay = max(1, min(60000, int(self.click_delay_entry.get() or "100"))) / 1000

            h = max(0, int(self.hours_entry.get() or 0))
            m = max(0, int(self.minutes_entry.get() or 0))
            s = max(0, int(self.seconds_entry.get() or 0))
            self.duration = h * 3600 + m * 60 + s or None
            self._cache_human_params()
        except ValueError as e:
            messagebox.showerror(self._t("title.error"), self._t("msg.bad_values").format(e=e))
            return

        self.is_running = True
        self.stop_event.clear()
        self.movement_type = self.movement_var.get()
        self._session_start = time.time()
        self._fatigue_factor = 1.0
        self._action_count = 0
        self._total_actions_done = 0
        self._last_mouse_pos = self.mouse.position
        self._noise_x = HumanNoise(seed=random.randint(0, 99999))
        self._noise_y = HumanNoise(seed=random.randint(0, 99999))
        self._tick_stats()

        self._play_sound("start")
        self._log_action("▶ СТАРТ")

        if self.duration:
            self.timer_frame.pack(fill=tk.X, padx=6, pady=(4, 0))
            self.progress_bar["maximum"] = self.duration
            self._update_timer_progress()
        else:
            self.timer_frame.pack_forget()

        # Drag & Drop режим (только в free)
        if self.drag_enabled.get() and self.movement_type == "free":
            threading.Thread(target=self._drag_loop, daemon=True).start()
        elif self.fixed_click_enabled.get() and self.coords_set and self.movement_type == "free":
            fx, fy = int(self.fixed_x.get()), int(self.fixed_y.get())
            self._lock_cursor(fx, fy)
            threading.Thread(target=self._fixed_clicker_loop,
                             args=(fx, fy), daemon=True).start()
        else:
            self._start_pos = self.mouse.position
            threading.Thread(target=self._movement_loop, daemon=True).start()
            if self.auto_clicker_enabled.get():
                threading.Thread(target=self._clicker_loop, daemon=True).start()

        # Anti-AFK
        if self.anti_afk_enabled.get():
            threading.Thread(target=self._anti_afk_loop, daemon=True).start()

        if self.duration:
            self.root.after(int(self.duration * 1000), self._stop)

        self.start_btn.config(text=self._t("btn.stop"))
        self.status_dot.config(text=self._t("status.running"), foreground="#00d4aa")
        self._update_status_dot("#00d4aa")

    def _cache_human_params(self):
        if self.human_like_enabled.get():
            self.h_delay_var = max(0, int(self.human_delay_variation.get() or 0))
            self.h_pos_var = max(0, int(self.human_pos_variation.get() or 0))
            self.h_curviness = self.curviness.get()
            self.h_tremor = self.hand_tremor.get()
            self.h_pressure = self.click_pressure.get()
            self.h_pauses = self.random_pauses.get()
            self.h_fatigue = self.fatigue_level.get()
            self.h_overshoot = self.overshoot_level.get()
            self.h_micro = self.micro_movements_level.get()
            self.h_speed_var = self.speed_variation_level.get()
        else:
            for attr in ('h_delay_var', 'h_pos_var', 'h_curviness', 'h_tremor',
                         'h_pauses', 'h_fatigue', 'h_overshoot', 'h_micro', 'h_speed_var'):
                setattr(self, attr, 0)
            self.h_pressure = 5

    def _stop(self):
        was = self.is_running
        self.is_running = False
        self.stop_event.set()
        self._unlock_cursor()
        self.start_btn.config(text=self._t("btn.start"))
        self.status_dot.config(text=self._t("status.stopped"), foreground="#555570")
        self._update_status_dot("#555570")
        self.timer_frame.pack_forget()

        if was:
            self._play_sound("stop")
            self._log_action("⬛ СТОП")

        if was and getattr(self, 'duration', None) and self._session_start:
            elapsed = time.time() - self._session_start
            if elapsed >= self.duration - 1.5:
                total = self.stat_clicks.get() + self.stat_actions.get()
                self._play_sound("finish")
                messagebox.showinfo(self._t("title.timer_done"),
                    self._t("msg.timer_done_detail").format(n=total, time=self._fmt(int(elapsed))))

    def _check_action_limit(self):
        if not self.action_limit_enabled.get():
            return False
        try:
            limit = int(self.action_limit_count.get() or 100)
        except ValueError:
            return False
        if self._total_actions_done >= limit:
            self._log_action(f"🔢 Достигнут лимит {limit} действий")
            self.root.after(0, self._stop)
            return True
        return False

    # ══════════════════════════════════════════════════════════════════════════
    #                         ДВИЖЕНИЕ
    # ══════════════════════════════════════════════════════════════════════════

    def _movement_loop(self):
        pos = self._start_pos
        while self.is_running and not self.stop_event.is_set():
            try:
                mt = self.movement_type
                if mt == "left_right":   self._move_lr(pos)
                elif mt == "up_down":    self._move_ud(pos)
                elif mt == "diagonal":   self._move_diag(pos)
                elif mt == "random":     self._move_random(pos)
                elif mt == "circle":     self._move_circle(pos)
                elif mt == "eight":      self._move_eight(pos)
                elif mt == "square":     self._move_square(pos)
                elif mt == "free":
                    if self.human_like_enabled.get() and self.h_micro > 0:
                        self._do_micro()
                    time.sleep(self.mouse_delay)
                self._maybe_pause()
            except Exception:
                break

    def _bezier_points(self, x1, y1, x2, y2, n=20):
        if not self.human_like_enabled.get():
            return [(int(x1 + (x2-x1)*i/n), int(y1 + (y2-y1)*i/n)) for i in range(n+1)]

        dist = math.hypot(x2 - x1, y2 - y1)
        strength = dist * 0.3 * (self.h_curviness / 5.0)
        angle = math.atan2(y2 - y1, x2 - x1)
        perp = angle + math.pi / 2

        d1 = random.uniform(-strength, strength)
        d2 = random.uniform(-strength, strength)
        c1x = x1 + (x2-x1)*0.33 + d1 * math.cos(perp)
        c1y = y1 + (y2-y1)*0.33 + d1 * math.sin(perp)
        c2x = x1 + (x2-x1)*0.66 + d2 * math.cos(perp)
        c2y = y1 + (y2-y1)*0.66 + d2 * math.sin(perp)

        pts = []
        for i in range(n + 1):
            t = i / n
            if self.h_speed_var > 0:
                ease = self.h_speed_var / 10.0
                t = t*t*(3 - 2*t) * ease + t * (1 - ease)
            u = 1 - t
            x = u**3*x1 + 3*u**2*t*c1x + 3*u*t**2*c2x + t**3*x2
            y = u**3*y1 + 3*u**2*t*c1y + 3*u*t**2*c2y + t**3*y2
            pts.append((int(x), int(y)))

        if self.h_overshoot > 0 and dist > 20:
            od = dist * 0.08 * (self.h_overshoot / 10.0) * random.uniform(0.5, 1.5)
            ox = x2 + od * math.cos(angle)
            oy = y2 + od * math.sin(angle)
            for i in range(max(3, int(n * 0.15))):
                t = i / max(3, int(n * 0.15))
                pts.append((int(x2 + (ox - x2) * (1 - t*t)),
                            int(y2 + (oy - y2) * (1 - t*t))))
            pts.append((int(x2), int(y2)))
        return pts

    def _apply_tremor(self, x, y):
        if self.human_like_enabled.get() and self.h_tremor > 0:
            t = time.time() * 5
            return (int(x + self._noise_x.value(t) * self.h_tremor),
                    int(y + self._noise_y.value(t) * self.h_tremor))
        return x, y

    def _do_micro(self):
        if random.random() > self.h_micro / 15.0:
            return
        try:
            cx, cy = self.mouse.position
            self.mouse.position = (int(cx + random.gauss(0, self.h_micro * 0.4)),
                                   int(cy + random.gauss(0, self.h_micro * 0.4)))
        except Exception:
            pass

    def _maybe_pause(self):
        if self.human_like_enabled.get() and self.h_pauses > 0:
            if random.random() < self.h_pauses / 500.0:
                time.sleep(random.uniform(0.2, 1.0 + self.h_pauses * 0.2))

    def _hdelay(self):
        d = self.mouse_delay
        if self.human_like_enabled.get():
            if self.h_speed_var > 0:
                d *= random.uniform(1 - self.h_speed_var/20, 1 + self.h_speed_var/20)
            d *= self._fatigue_factor
        return max(0.001, d)

    def _move_lr(self, sp):
        for pts in [self._bezier_points(sp[0]-self.radius, sp[1], sp[0]+self.radius, sp[1]),
                    self._bezier_points(sp[0]+self.radius, sp[1], sp[0]-self.radius, sp[1])]:
            for x, y in pts:
                if not self.is_running: return
                self.mouse.position = self._apply_tremor(x, y)
                time.sleep(self._hdelay())

    def _move_ud(self, sp):
        for pts in [self._bezier_points(sp[0], sp[1]-self.radius, sp[0], sp[1]+self.radius),
                    self._bezier_points(sp[0], sp[1]+self.radius, sp[0], sp[1]-self.radius)]:
            for x, y in pts:
                if not self.is_running: return
                self.mouse.position = self._apply_tremor(x, y)
                time.sleep(self._hdelay())

    def _move_diag(self, sp):
        r = self.radius
        for pts in [self._bezier_points(sp[0]-r, sp[1]-r, sp[0]+r, sp[1]+r),
                    self._bezier_points(sp[0]+r, sp[1]+r, sp[0]-r, sp[1]-r)]:
            for x, y in pts:
                if not self.is_running: return
                self.mouse.position = self._apply_tremor(x, y)
                time.sleep(self._hdelay())

    def _move_random(self, sp):
        cx, cy = self.mouse.position
        while self.is_running and not self.stop_event.is_set():
            tx = sp[0] + random.randint(-self.radius, self.radius)
            ty = sp[1] + random.randint(-self.radius, self.radius)
            for x, y in self._bezier_points(cx, cy, tx, ty, n=12):
                if not self.is_running: return
                self.mouse.position = self._apply_tremor(x, y)
                time.sleep(self._hdelay())
            cx, cy = tx, ty
            self._maybe_pause()

    def _move_circle(self, sp):
        for i in range(61):
            if not self.is_running: return
            a = (i / 60) * 2 * math.pi
            self.mouse.position = self._apply_tremor(
                sp[0] + int(self.radius * math.cos(a)),
                sp[1] + int(self.radius * math.sin(a)))
            time.sleep(self._hdelay())

    def _move_eight(self, sp):
        for i in range(81):
            if not self.is_running: return
            t = (i / 80) * 2 * math.pi
            self.mouse.position = self._apply_tremor(
                sp[0] + int(self.radius * math.sin(t)),
                sp[1] + int(self.radius * 0.6 * math.sin(2 * t)))
            time.sleep(self._hdelay())

    def _move_square(self, sp):
        r = self.radius
        corners = [(sp[0]-r, sp[1]-r), (sp[0]+r, sp[1]-r),
                   (sp[0]+r, sp[1]+r), (sp[0]-r, sp[1]+r)]
        for i in range(4):
            if not self.is_running: return
            ni = (i + 1) % 4
            for x, y in self._bezier_points(corners[i][0], corners[i][1],
                                            corners[ni][0], corners[ni][1], n=15):
                if not self.is_running: return
                self.mouse.position = self._apply_tremor(x, y)
                time.sleep(self._hdelay())

    # ══════════════════════════════════════════════════════════════════════════
    #                           КЛИКЕР
    # ══════════════════════════════════════════════════════════════════════════

    def _get_button(self):
        a = self.action_type.get()
        return {"right": Button.right, "middle": Button.middle}.get(a, Button.left)

    def _do_action(self, x=None, y=None):
        if self._check_action_limit():
            return

        if self.human_like_enabled.get() and self.h_pauses > 0:
            if random.random() < self.h_pauses / 80.0:
                time.sleep(random.uniform(0.3, 1 + self.h_pauses * 0.15) * self._fatigue_factor)

        at = self.action_type.get()
        if at == "keyboard":
            self._press_key(self.kb_key_var.get().strip())
            self._safe_inc(self.stat_actions)
            self._log_action(f"⌨ Клавиша [{self.kb_key_var.get().strip()}]")
        else:
            btn = self._get_button()
            n = 2 if self.double_click_enabled.get() else 1
            if x is not None and y is not None:
                if self.human_like_enabled.get():
                    self._human_click(btn, n, x, y)
                else:
                    self.mouse.position = (x, y)
                    self.mouse.click(btn, n)
            else:
                if self.human_like_enabled.get():
                    self._human_click(btn, n, *self.mouse.position)
                else:
                    self.mouse.click(btn, n)
            self._safe_inc(self.stat_clicks)
            pos = f"({x},{y})" if x is not None else "текущ."
            self._log_action(f"🖱 {at} {'дв.' if n == 2 else ''} {pos}")

        self._total_actions_done += 1
        self._update_fatigue()

    def _safe_inc(self, var):
        try:
            self.root.after(0, lambda: var.set(var.get() + 1))
        except Exception:
            pass

    def _press_key(self, key_name: str):
        try:
            key = getattr(pynput_keyboard.Key, key_name.lower(), None)
            if key is None:
                key = pynput_keyboard.KeyCode.from_char(key_name[0])
            n = 2 if self.double_click_enabled.get() else 1
            for i in range(n):
                hold = (random.uniform(0.03, 0.12) * (1 + self.h_pressure * 0.05)
                        if self.human_like_enabled.get() else 0.04)
                self.kb_ctrl.press(key)
                time.sleep(hold)
                self.kb_ctrl.release(key)
                if i < n - 1:
                    time.sleep(random.uniform(0.04, 0.12))
        except Exception as e:
            print(f"Ошибка клавиши '{key_name}': {e}")

    def _human_click(self, button, n, x, y):
        hpv = self.h_pos_var
        for i in range(n):
            ox = int(random.gauss(0, hpv * 0.5)) if hpv > 0 else 0
            oy = int(random.gauss(0, hpv * 0.5)) if hpv > 0 else 0
            self.mouse.position = (x + ox, y + oy)
            dur = random.uniform(0.04, 0.10) * (1 + self.h_pressure * 0.08) * self._fatigue_factor
            self.mouse.press(button)
            time.sleep(dur)
            self.mouse.release(button)
            if i < n - 1:
                time.sleep(random.uniform(0.04, 0.15))

    def _clicker_loop(self):
        while self.is_running and not self.stop_event.is_set():
            self._do_action()
            time.sleep(self._varied_delay())

    def _fixed_clicker_loop(self, fx, fy):
        while self.is_running and not self.stop_event.is_set():
            self._do_action(fx, fy)
            time.sleep(self._varied_delay())

    def _drag_loop(self):
        """Цикл Drag & Drop."""
        try:
            x1, y1 = int(self.drag_start_x.get()), int(self.drag_start_y.get())
            x2, y2 = int(self.drag_end_x.get()), int(self.drag_end_y.get())
        except ValueError:
            return
        while self.is_running and not self.stop_event.is_set():
            if self._check_action_limit():
                break
            self._do_drag(x1, y1, x2, y2)
            self._safe_inc(self.stat_clicks)
            self._total_actions_done += 1
            self._log_action(f"🔃 Drag ({x1},{y1})→({x2},{y2})")
            time.sleep(self._varied_delay())

    def _varied_delay(self):
        d = self.click_delay
        if self.human_like_enabled.get():
            v = self.h_delay_var / 100.0
            d *= random.uniform(1 - v, 1 + v) * self._fatigue_factor
        return max(0.01, d)

    def _update_fatigue(self):
        if not self.human_like_enabled.get() or self.h_fatigue <= 0:
            return
        self._action_count += 1
        if self._action_count % 100 == 0:
            self._fatigue_factor = min(1.5, self._fatigue_factor + 0.005 * self.h_fatigue / 5)

    # ── Блокировка курсора ────────────────────────────────────────────────────

    def _lock_cursor(self, x, y):
        self.cursor_locked = True
        threading.Thread(target=self._cursor_lock_loop, args=(x, y), daemon=True).start()

    def _cursor_lock_loop(self, x, y):
        try:
            u32 = ctypes.windll.user32
            while self.cursor_locked and self.is_running:
                if self.human_like_enabled.get() and self.h_tremor > 0:
                    t = time.time() * 5
                    u32.SetCursorPos(x + int(self._noise_x.value(t) * self.h_tremor),
                                     y + int(self._noise_y.value(t) * self.h_tremor))
                else:
                    u32.SetCursorPos(x, y)
                time.sleep(0.01)
        except Exception:
            pass

    def _unlock_cursor(self):
        self.cursor_locked = False

    # ── Горячая клавиша ───────────────────────────────────────────────────────

    def _on_global_key(self, key):
        try:
            if key == self.hotkey:
                self.root.after(0, self.toggle)
        except Exception:
            pass

    # ══════════════════════════════════════════════════════════════════════════
    #                     КОНФИГ / ПРОФИЛИ
    # ══════════════════════════════════════════════════════════════════════════

    def _collect_config(self):
        return {
            "hotkey":                self.hotkey_entry.get(),
            "radius":                self.radius_entry.get(),
            "mouse_delay":           self.mouse_delay_entry.get(),
            "movement_type":         self.movement_var.get(),
            "auto_clicker":          self.auto_clicker_enabled.get(),
            "click_delay":           self.click_delay_entry.get(),
            "action_type":           self.action_type.get(),
            "kb_key":                self.kb_key_var.get(),
            "double_click":          self.double_click_enabled.get(),
            "fixed_click":           self.fixed_click_enabled.get(),
            "fixed_x":               self.fixed_x.get(),
            "fixed_y":               self.fixed_y.get(),
            "hours":                 self.hours_entry.get(),
            "minutes":               self.minutes_entry.get(),
            "seconds":               self.seconds_entry.get(),
            "human_like":            self.human_like_enabled.get(),
            "human_delay_variation": self.human_delay_variation.get(),
            "human_pos_variation":   self.human_pos_variation.get(),
            "curviness":             self.curviness.get(),
            "hand_tremor":           self.hand_tremor.get(),
            "click_pressure":        self.click_pressure.get(),
            "random_pauses":         self.random_pauses.get(),
            "fatigue":               self.fatigue_level.get(),
            "overshoot":             self.overshoot_level.get(),
            "micro_movements":       self.micro_movements_level.get(),
            "speed_variation":       self.speed_variation_level.get(),
            "theme":                 self.current_theme,
            "coord_select_button":   self.coord_select_button.get(),
            "sound_enabled":         self.sound_enabled.get(),
            "action_limit_enabled":  self.action_limit_enabled.get(),
            "action_limit_count":    self.action_limit_count.get(),
            "anti_afk":              self.anti_afk_enabled.get(),
            "anti_afk_interval":     self.anti_afk_interval.get(),
            "drag_enabled":          self.drag_enabled.get(),
            "drag_start_x":          self.drag_start_x.get(),
            "drag_start_y":          self.drag_start_y.get(),
            "drag_end_x":            self.drag_end_x.get(),
            "drag_end_y":            self.drag_end_y.get(),
            "tray_enabled":          self.tray_enabled.get(),
            "tray_start_minimized":  self.tray_start_minimized.get(),
            "tray_show_startstop":   self.tray_show_startstop.get(),
            "tray_show_coords":      self.tray_show_coords.get(),
            "sound_volume":          self.sound_volume.get(),
            "language":              self.current_language,
            "current_profile":       self.current_profile,
        }

    def _save_config(self, *_):
        """Debounced save — отложенное сохранение через 300мс"""
        if self._applying_config:
            return
        if self._save_timer:
            self.root.after_cancel(self._save_timer)
        self._save_timer = self.root.after(300, self._do_save_config)

    def _do_save_config(self):
        """Непосредственное сохранение конфига на диск"""
        self._save_timer = None
        try:
            with open(self.CFG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._collect_config(), f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _load_config(self):
        if not os.path.exists(self.CFG_FILE):
            return
        try:
            with open(self.CFG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            return
        self._apply_config(cfg)
        # Язык уже загружен до построения UI, обновим только кнопку
        if "language" in cfg:
            self.current_language = cfg["language"]
            self._load_locale()
            self.lang_btn.config(text=f"🌍 {self.current_language.upper()}")
        if "current_profile" in cfg:
            self.current_profile = cfg["current_profile"]
        fx, fy = cfg.get("fixed_x", "0"), cfg.get("fixed_y", "0")
        if self.fixed_click_enabled.get() and fx != "0":
            self.coord_info_lbl.config(text=f"✅ X={fx}, Y={fy}", foreground="#00d4aa")
            self.coords_set = True

    def _apply_config(self, cfg):
        self._applying_config = True
        try:
            self._apply_config_inner(cfg)
        finally:
            self._applying_config = False

    def _apply_config_inner(self, cfg):
        def _se(entry, key):
            v = cfg.get(key)
            if v is not None:
                entry.delete(0, tk.END)
                entry.insert(0, str(v))

        _se(self.hotkey_entry, "hotkey")
        _se(self.radius_entry, "radius")
        _se(self.mouse_delay_entry, "mouse_delay")
        _se(self.click_delay_entry, "click_delay")
        _se(self.hours_entry, "hours")
        _se(self.minutes_entry, "minutes")
        _se(self.seconds_entry, "seconds")

        for key, var in [
            ("hotkey", None),
            ("movement_type", self.movement_var),
            ("auto_clicker", self.auto_clicker_enabled),
            ("action_type", self.action_type),
            ("kb_key", self.kb_key_var),
            ("double_click", self.double_click_enabled),
            ("fixed_click", self.fixed_click_enabled),
            ("fixed_x", self.fixed_x),
            ("fixed_y", self.fixed_y),
            ("human_like", self.human_like_enabled),
            ("human_delay_variation", self.human_delay_variation),
            ("human_pos_variation", self.human_pos_variation),
            ("curviness", self.curviness),
            ("hand_tremor", self.hand_tremor),
            ("click_pressure", self.click_pressure),
            ("random_pauses", self.random_pauses),
            ("fatigue", self.fatigue_level),
            ("overshoot", self.overshoot_level),
            ("micro_movements", self.micro_movements_level),
            ("speed_variation", self.speed_variation_level),
            ("coord_select_button", self.coord_select_button),
            ("sound_enabled", self.sound_enabled),
            ("action_limit_enabled", self.action_limit_enabled),
            ("action_limit_count", self.action_limit_count),
            ("anti_afk", self.anti_afk_enabled),
            ("anti_afk_interval", self.anti_afk_interval),
            ("drag_enabled", self.drag_enabled),
            ("drag_start_x", self.drag_start_x),
            ("drag_start_y", self.drag_start_y),
            ("drag_end_x", self.drag_end_x),
            ("drag_end_y", self.drag_end_y),
            ("tray_enabled", self.tray_enabled),
            ("tray_start_minimized", self.tray_start_minimized),
            ("tray_show_startstop", self.tray_show_startstop),
            ("tray_show_coords", self.tray_show_coords),
            ("sound_volume", self.sound_volume),
        ]:
            if key == "hotkey":
                if "hotkey" in cfg:
                    self.hotkey = getattr(pynput_keyboard.Key,
                                         cfg["hotkey"].lower(), cfg["hotkey"].lower())
            elif key in cfg and var is not None:
                var.set(cfg[key])

        self._on_action_type_change()
        self._on_human_toggle()
        self._on_limit_toggle()
        self._on_clicker_toggle()
        self._on_fixed_click_toggle()
        self._on_drag_toggle()
        self._on_afk_toggle()
        self._on_sound_toggle()
        self._on_tray_toggle()
        self._on_movement_change()

    def _export_cfg(self):
        p = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("JSON", "*.json")],
            initialfile="mouse_ops_config.json")
        if p:
            try:
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(self._collect_config(), f, indent=2, ensure_ascii=False)
                messagebox.showinfo(self._t("title.success"), self._t("msg.exported"))
            except Exception as e:
                messagebox.showerror(self._t("title.error"), str(e))

    def _import_cfg(self):
        p = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if p:
            try:
                with open(p, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                self._apply_config(cfg)
                self._save_config()
                messagebox.showinfo(self._t("title.success"), self._t("msg.imported"))
            except Exception as e:
                messagebox.showerror(self._t("title.error"), str(e))

    def _reset_cfg(self):
        if messagebox.askyesno(self._t("title.reset"), self._t("msg.reset_confirm_detail")):
            # Удалить файлы конфигурации
            for fpath in [self.CFG_FILE, self.PROFILES_FILE]:
                try:
                    os.remove(fpath)
                except Exception:
                    pass
            # Apply factory settings
            self._apply_config(self.DEFAULTS)
            # Reset profiles
            self.current_profile = self._t("profile.default")
            self.profiles = {self._t("profile.default"): dict(self.DEFAULTS)}
            self._save_profiles()
            self.profile_combo["values"] = list(self.profiles.keys())
            self.profile_combo.set(self.current_profile)
            # Сбросить статистику
            self._reset_stats()
            # Сохранить
            self._do_save_config()
            messagebox.showinfo(self._t("title.done"), self._t("msg.reset_done_detail"))

    # ── Профили ───────────────────────────────────────────────────────────────

    def _save_profiles(self):
        try:
            with open(self.PROFILES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.profiles, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _load_profiles(self):
        try:
            if os.path.exists(self.PROFILES_FILE):
                with open(self.PROFILES_FILE, "r", encoding="utf-8") as f:
                    self.profiles = json.load(f)
            if not self.profiles:
                self.profiles = {self._t("profile.default"): self._collect_config()}
                self._save_profiles()
            # Если current_profile отсутствует среди ключей — выбрать первый
            if self.current_profile not in self.profiles:
                self.current_profile = list(self.profiles.keys())[0]
            self.profile_combo["values"] = list(self.profiles.keys())
            self.profile_combo.set(self.current_profile)
        except Exception:
            pass

    def _new_profile(self):
        name = simpledialog.askstring(self._t("dialog.profile_title"), self._t("dialog.profile_name"))
        if name and name.strip():
            name = name.strip()
            if name in self.profiles:
                messagebox.showwarning(self._t("title.warning"), self._t("msg.profile_exists_warn"))
                return
            self.profiles[name] = self._collect_config()
            self.current_profile = name
            self._save_profiles()
            self.profile_combo["values"] = list(self.profiles.keys())
            self.profile_combo.set(name)

    def _save_profile(self):
        name = self.profile_combo.get()
        if not name:
            name = simpledialog.askstring(self._t("dialog.profile_title"), self._t("dialog.profile_name"))
        if not name or not name.strip():
            return
        name = name.strip()
        self.profiles[name] = self._collect_config()
        self.current_profile = name
        self._save_profiles()
        self.profile_combo["values"] = list(self.profiles.keys())
        self.profile_combo.set(name)
        messagebox.showinfo(self._t("title.success"), self._t("msg.profile_saved_detail").format(name=name))

    def _load_profile(self, event=None):
        name = self.profile_combo.get()
        if name and name in self.profiles:
            pcfg = self.profiles[name]
            self._apply_config(pcfg)
            self.current_profile = name
            self.profile_combo.set(name)
            self._do_save_config()

    def _rename_profile(self):
        old = self.profile_combo.get()
        if not old or old == self._t("profile.default"):
            return
        new = simpledialog.askstring(self._t("dialog.rename_title"), self._t("dialog.rename_prompt").format(old=old))
        if new and new.strip():
            new = new.strip()
            if new in self.profiles:
                return
            self.profiles[new] = self.profiles.pop(old)
            self.current_profile = new
            self._save_profiles()
            self.profile_combo["values"] = list(self.profiles.keys())
            self.profile_combo.set(new)

    def _delete_profile(self):
        name = self.profile_combo.get()
        if not name or name == self._t("profile.default"):
            return
        if messagebox.askyesno(self._t("title.delete"), self._t("msg.delete_profile_confirm").format(name=name)):
            del self.profiles[name]
            self._save_profiles()
            self.current_profile = self._t("profile.default")
            self.profile_combo["values"] = list(self.profiles.keys())
            self.profile_combo.set(self.current_profile)

    # ── Утилиты ───────────────────────────────────────────────────────────────

    def _update_timer_progress(self):
        if not self.is_running or not self.duration:
            return
        elapsed = time.time() - self._session_start
        remaining = max(0, self.duration - elapsed)
        self.progress_bar["value"] = elapsed
        self.timer_label.config(text=self._t("lbl.remaining").format(time=self._fmt(int(remaining))))
        if remaining > 0:
            self.root.after(500, self._update_timer_progress)

    def _fmt(self, sec):
        h, rem = divmod(sec, 3600)
        m, s = divmod(rem, 60)
        return f"{h:02}:{m:02}:{s:02}"

    def _center_window(self):
        self.root.update_idletasks()
        w, h = self.root.winfo_width(), self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    # ══════════════════════════════════════════════════════════════════════════
    #                     СИСТЕМНЫЙ ТРЕЙ
    # ══════════════════════════════════════════════════════════════════════════

    def _setup_tray(self):
        """Создать иконку в системном трее."""
        if not HAS_TRAY:
            return
        try:
            # Создаём иконку программно
            img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            # Фон
            draw.rounded_rectangle([2, 2, 62, 62], radius=12,
                                    fill=(11, 11, 20, 255), outline=(124, 92, 252, 255), width=2)
            # Cursor arrow
            draw.polygon([(20, 14), (20, 48), (30, 38), (42, 50), (46, 46), (34, 34), (44, 24)],
                         fill=(0, 212, 170, 255))

            self.tray_icon = pystray.Icon(
                "mouse_ops",
                img,
                f"Mouse Ops v{self.VERSION}",
                menu=pystray.Menu(
                    pystray.MenuItem(
                        lambda item: self._t("tray.hide") if self._is_window_visible() else self._t("tray.show"),
                        self._tray_toggle_window,
                        default=True
                    ),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem(
                        lambda item: self._t("tray.stop") if self.is_running else self._t("tray.start"),
                        self._tray_toggle_action,
                        visible=lambda item: self.tray_show_startstop.get()
                    ),
                    pystray.MenuItem(
                        lambda item: f"X: {self.mouse.position[0]}  Y: {self.mouse.position[1]}",
                        None,
                        enabled=False,
                        visible=lambda item: self.tray_show_coords.get()
                    ),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem(self._t("tray.exit"), self._tray_exit)
                )
            )
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception as e:
            print(f"Tray setup error: {e}")

    def _is_window_visible(self):
        try:
            return self.root.winfo_viewable()
        except Exception:
            return False

    def _minimize_to_tray(self):
        """Свернуть окно в трей."""
        if not HAS_TRAY:
            return
        if not hasattr(self, 'tray_icon') or self.tray_icon is None:
            self._setup_tray()
        self.root.withdraw()

    def _tray_toggle_window(self, icon=None, item=None):
        """Показать/скрыть окно из трея."""
        if self._is_window_visible():
            self.root.withdraw()
        else:
            self.root.after(0, self._show_from_tray)

    def _show_from_tray(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _tray_toggle_action(self, icon=None, item=None):
        """Запустить/остановить из меню трея."""
        self.root.after(0, self.toggle)

    def _tray_exit(self, icon=None, item=None):
        """Полный выход из трея."""
        if hasattr(self, 'tray_icon') and self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        self.root.after(0, self._real_quit)

    def _on_close(self):
        """Обработка закрытия окна — свернуть в трей или выйти."""
        if self.tray_enabled.get() and HAS_TRAY:
            self._minimize_to_tray()
        else:
            self._real_quit()

    def _real_quit(self):
        """Полный выход из приложения."""
        self._do_save_config()
        if hasattr(self, 'tray_icon') and self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        try:
            self.root.destroy()
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    app = MouseOpsApp(root)
    root.mainloop()
