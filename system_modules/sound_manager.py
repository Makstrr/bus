import pygame
import os
from typing import Dict, Optional
from system_modules.config import Config


class SoundManager:
    def __init__(self):
        self.sounds: Dict[str, pygame.mixer.Sound] = {}  # Список звуков, найденных в ассетах
        self.music: Dict[str, str] = {}  # Список музыки, найденной в ассетах
        self.current_music: Optional[str] = None
        self.music_volume = Config.MUSIC_VOLUME  # Громкость музыки по умолчанию (0.0-1.0)
        self.sound_volume = Config.SFX_VOLUME  # Громкость звуков по умолчанию (0.0-1.0)

        # Инициализация аудиосистемы
        pygame.mixer.init()

    def load_sounds(self, sound_dir: str):
        """Загружает все звуки из указанной директории"""
        for filename in os.listdir(sound_dir):
            if filename.endswith(('.wav', '.ogg')):
                name = os.path.splitext(filename)[0]
                try:
                    sound = pygame.mixer.Sound(os.path.join(sound_dir, filename))
                    self.sounds[name] = sound
                    print(f"Loaded sound: {name}")
                except Exception as e:
                    print(f"Error loading sound {filename}: {e}")

    def load_music(self, music_dir: str):
        """Регистрирует музыку из указанной директории"""
        for filename in os.listdir(music_dir):
            if filename.endswith(('.mp3', '.ogg', '.wav')):
                name = os.path.splitext(filename)[0]
                self.music[name] = os.path.join(music_dir, filename)
                print(f"Registered music: {name}")

    def play_sound(self, name: str, volume: float = None):
        """Воспроизводит звуковой эффект"""
        if name in self.sounds:
            sound = self.sounds[name]
            sound.set_volume(volume or self.sound_volume)
            sound.play()
        else:
            print(f"Sound not found: {name}")

    def play_music(self, name: str, loop: int = -1):
        """Воспроизводит музыку (loop=-1 для бесконечного повтора)"""
        if name in self.music:
            pygame.mixer.music.load(self.music[name])
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(loop)
            self.current_music = name
        else:
            print(f"Music not found: {name}")

    def stop_music(self):
        """Останавливает текущую музыку"""
        pygame.mixer.music.stop()
        self.current_music = None

    def pause_music(self):
        """Приостанавливает музыку"""
        pygame.mixer.music.pause()

    def unpause_music(self):
        """Возобновляет музыку"""
        pygame.mixer.music.unpause()

    def set_music_volume(self, volume: float):
        """Устанавливает громкость музыки (0.0-1.0)"""
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)

    def set_sound_volume(self, volume: float):
        """Устанавливает громкость звуков (0.0-1.0)"""
        self.sound_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.sound_volume)

    def is_music_playing(self) -> bool:
        """Проверяет, играет ли музыка"""
        return pygame.mixer.music.get_busy()

