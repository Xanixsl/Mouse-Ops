"""Вспомогательные классы и функции"""

import math
import random
import tkinter as tk
import darkdetect


class HumanNoise:
    """Генератор шума для имитации человеческого поведения"""
    
    def __init__(self, octaves=4, seed=None):
        self.octaves = octaves
        rng = random.Random(seed)
        self._phases = [rng.uniform(0, 2 * math.pi) for _ in range(octaves)]
        self._freqs = [rng.uniform(0.3, 1.5) * (i + 1) for i in range(octaves)]
        self._amps = [1.0 / (i + 1) for i in range(octaves)]

    def value(self, t: float) -> float:
        """Получить значение шума в момент времени t"""
        total = sum(a * math.sin(f * t + p)
                    for a, f, p in zip(self._amps, self._freqs, self._phases))
        return total / sum(self._amps)


class ToolTip:
    """Модернизированная всплывающая подсказка с glassmorphism дизайном"""
    
    def __init__(self, widget, text, delay=400):
        self.widget = widget
        self.text = text
        self.delay = delay
        self._id = None
        self._win = None
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._cancel)
        widget.bind("<ButtonPress>", self._cancel)

    def _schedule(self, event=None):
        self._cancel()
        self._id = self.widget.after(self.delay, self._show)

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
        """Показать подсказку с современным дизайном"""
        # Современные цвета 2025-2026
        dark = darkdetect.isDark()
        bg = "#1a1a2e" if dark else "#f8f9fa"
        fg = "#e8e8f0" if dark else "#1a1a1a"
        border_color = "#7c5cfc" if dark else "#6c5ce7"
        
        try:
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        except Exception:
            return
        
        self._win = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-alpha", 0.95)  # Легкая прозрачность
        
        # Фрейм с границей для glassmorphism эффекта
        border_frame = tk.Frame(tw, bg=border_color, padx=1, pady=1)
        border_frame.pack()
        
        label = tk.Label(
            border_frame,
            text=self.text,
            justify="left",
            bg=bg,
            fg=fg,
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 9),
            wraplength=300,
            padx=12,
            pady=8
        )
        label.pack()
