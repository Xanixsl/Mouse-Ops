"""Главное окно приложения Mouse Ops"""

import tkinter as tk
from tkinter import ttk


class MouseOpsWindow:
    """Управление главным окном приложения"""
    
    def __init__(self, root, version="B-2.0"):
        self.root = root
        self.version = version
        self._setup_window()
    
    def _setup_window(self):
        """Начальная настройка окна"""
        self.root.title(f"Mouse Ops v{self.version}")
        self.root.geometry("1100x850")
        self.root.minsize(950, 750)
        self.root.resizable(True, True)
    
    def center(self):
        """Центрировать окно на экране"""
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
