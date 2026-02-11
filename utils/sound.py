"""Менеджер звуков для Mouse Ops"""

import io
import math
import struct
import wave
import winsound
import threading


class SoundManager:
    """Управление звуковыми эффектами с контролем громкости"""
    
    def __init__(self, volume=50):
        self.volume = volume
        self.enabled = True
    
    def set_volume(self, volume: int):
        """Установить громкость (0-100)"""
        self.volume = max(0, min(100, volume))
    
    def set_enabled(self, enabled: bool):
        """Включить/выключить звуки"""
        self.enabled = enabled
    
    def _generate_beep(self, frequency: int, duration_ms: int) -> bytes:
        """Генерировать WAV beep с текущей громкостью"""
        sample_rate = 22050
        n_samples = int(sample_rate * duration_ms / 1000)
        volume = self.volume / 100.0
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
    
    def _play_beep(self, frequency: int, duration_ms: int):
        """Воспроизвести beep"""
        if not self.enabled:
            return
        
        try:
            data = self._generate_beep(frequency, duration_ms)
            winsound.PlaySound(data, winsound.SND_MEMORY)
        except Exception:
            pass
    
    def play(self, event_type: str):
        """Воспроизвести звук для типа события"""
        if not self.enabled:
            return
        
        threading.Thread(target=self._play_worker, args=(event_type,), daemon=True).start()
    
    def _play_worker(self, event_type: str):
        """Рабочий поток для воспроизведения звука"""
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
