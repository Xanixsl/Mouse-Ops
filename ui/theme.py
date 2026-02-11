"""Современная тема для Mouse Ops в стиле 2025-2026

Использует:
- Glassmorphism эффекты
- Градиенты и свечения
- Минималистичная цветовая палитра с яркими акцентами
- Плавные переходы и анимации
- Современная типографика
"""

from tkinter import ttk


class ModernTheme:
    """Современная цветовая схема и стили 2025-2026"""
    
    # Цветовая палитра inspired by современными UI трендами
    COLORS = {
        # Акцентные цвета
        "accent": "#7c5cfc",        # Electric purple - основной акцент
        "accent_glow": "#9b82ff",   # Lighter purple для свечения
        "accent2": "#00d4aa",       # Mint teal - второй акцент
        "accent3": "#ff6b9d",       # Coral pink - третий акцент
        "accent4": "#ffc857",       # Golden yellow
        
        # Статусные цвета
        "success": "#00d4aa",
        "warning": "#ffc857",
        "error": "#ff5c5c",
        "info": "#5c9cff",
        
        # Текст
        "text": "#e8e8f0",          # Основной текст
        "text_sec": "#8888a0",      # Вторичный текст
        "text_dim": "#555570",      # Приглушенный текст
        "text_bright": "#ffffff",   # Яркий текст
        
        # Поверхности и фоны
        "surface": "#12121e",       # Основной фон
        "card": "#1a1a2e",          # Карточки
        "card_hover": "#222238",    # Карточки при наведении
        "border": "#2a2a44",        # Границы
        "shadow": "#0a0a10",        # Тени
        
        # Градиенты (для будущего использования)
        "gradient_start": "#7c5cfc",
        "gradient_end": "#ff6b9d",
    }
    
    @staticmethod
    def apply(style: ttk.Style):
        """Применить современную тему к приложению"""
        
        # Глобальные стили
        style.configure(".", 
            font=("Segoe UI", 10),
            background=ModernTheme.COLORS["surface"],
            foreground=ModernTheme.COLORS["text"]
        )
        
        # Labels
        style.configure("TLabel",
            font=("Segoe UI", 10),
            background=ModernTheme.COLORS["surface"],
            foreground=ModernTheme.COLORS["text"]
        )
        
        # Title labels
        style.configure("Title.TLabel",
            font=("Segoe UI", 20, "bold"),
            foreground=ModernTheme.COLORS["text_bright"]
        )
        
        style.configure("Subtitle.TLabel",
            font=("Segoe UI", 9),
            foreground=ModernTheme.COLORS["text_dim"]
        )
        
        style.configure("Section.TLabel",
            font=("Segoe UI", 10, "bold"),
            foreground=ModernTheme.COLORS["accent"]
        )
        
        style.configure("Coords.TLabel",
            font=("Consolas", 10),
            foreground=ModernTheme.COLORS["accent2"]
        )
        
        style.configure("Status.TLabel",
            font=("Segoe UI", 10, "bold")
        )
        
        # Frames
        style.configure("TFrame",
            background=ModernTheme.COLORS["surface"]
        )
        
        style.configure("Card.TFrame",
            background=ModernTheme.COLORS["card"],
            relief="flat"
        )
        
        # LabelFrames - современный стиль с акцентными границами
        style.configure("TLabelframe",
            background=ModernTheme.COLORS["card"],
            bordercolor=ModernTheme.COLORS["border"],
            relief="flat",
            padding=16
        )
        
        style.configure("TLabelframe.Label",
            font=("Segoe UI", 10, "bold"),
            foreground=ModernTheme.COLORS["accent"],
            background=ModernTheme.COLORS["card"]
        )
        
        style.configure("Compact.TLabelframe.Label",
            font=("Segoe UI", 9, "bold")
        )
        
        # Buttons - современный gradient-подобный стиль
        style.configure("TButton",
            font=("Segoe UI", 10),
            borderwidth=0,
            focuscolor="none",
            padding=(12, 8)
        )
        
        # Accent button - главная кнопка
        style.configure("Accent.TButton",
            font=("Segoe UI", 12, "bold"),
            padding=(24, 14)
        )
        
        # Secondary button
        style.configure("Secondary.TButton",
            font=("Segoe UI", 10),
            padding=(14, 8)
        )
        
        # Recording button
        style.configure("Rec.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(12, 6)
        )
        
        # Notebook (вкладки)
        style.configure("TNotebook",
            background=ModernTheme.COLORS["surface"],
            borderwidth=0
        )
        
        style.configure("TNotebook.Tab",
            padding=(20, 10),
            font=("Segoe UI", 10, "bold")
        )
        
        # Checkbuttons и Radiobuttons
        style.configure("TCheckbutton",
            font=("Segoe UI", 10),
            background=ModernTheme.COLORS["surface"]
        )
        
        style.configure("TRadiobutton",
            font=("Segoe UI", 10),
            background=ModernTheme.COLORS["surface"]
        )
        
        # Entry fields
        style.configure("TEntry",
            fieldbackground=ModernTheme.COLORS["card"],
            foreground=ModernTheme.COLORS["text"],
            borderwidth=1,
            relief="flat"
        )
        
        # Combobox  
        style.configure("TCombobox",
            fieldbackground=ModernTheme.COLORS["card"],
            background=ModernTheme.COLORS["card"],
            foreground=ModernTheme.COLORS["text"],
            borderwidth=1,
            arrowcolor=ModernTheme.COLORS["accent"]
        )
        
        # Progressbar - с акцентным цветом
        style.configure("TProgressbar",
            background=ModernTheme.COLORS["accent"],
            troughcolor=ModernTheme.COLORS["border"],
            borderwidth=0,
            thickness=8
        )
        
        # Scrollbar
        style.configure("TScrollbar",
            background=ModernTheme.COLORS["card"],
            troughcolor=ModernTheme.COLORS["surface"],
            borderwidth=0,
            arrowsize=12
        )
        
        # Separator
        style.configure("TSeparator",
            background=ModernTheme.COLORS["border"]
        )
        
        # Scale (слайдеры)
        style.configure("TScale",
            background=ModernTheme.COLORS["surface"],
            troughcolor=ModernTheme.COLORS["border"],
            borderwidth=0,
            sliderthickness=20
        )
    
    @staticmethod
    def get_gradient_colors(start_color: str, end_color: str, steps: int):
        """Генерировать градиент между двумя цветами"""
        # Парсинг hex цветов
        start = tuple(int(start_color[i:i+2], 16) for i in (1, 3, 5))
        end = tuple(int(end_color[i:i+2], 16) for i in (1, 3, 5))
        
        # Генерация промежуточных цветов
        colors = []
        for i in range(steps):
            t = i / (steps - 1) if steps > 1 else 0
            r = int(start[0] + (end[0] - start[0]) * t)
            g = int(start[1] + (end[1] - start[1]) * t)
            b = int(start[2] + (end[2] - start[2]) * t)
            colors.append(f"#{r:02x}{g:02x}{b:02x}")
        
        return colors


def setup_modern_theme():
    """Быстрая настройка современной темы"""
    style = ttk.Style()
    ModernTheme.apply(style)
    return ModernTheme.COLORS
