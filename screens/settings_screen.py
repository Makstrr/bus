import pygame
from screens.base_screen import BaseScreen
from system_modules.game_state import GameState
from system_modules.config import Config


# TODO: реализовать функционал и сохранение настроек в config.json
class SettingsScreen(BaseScreen):
    def __init__(self, game):
        super().__init__(game)
        self.options = ["Громкость музыки", "Громкость звуков", "Управление", "Назад"]
        self.selected_option = 0
        self.music_volume = self.game.sound_manager.music_volume
        self.sound_volume = self.game.sound_manager.sound_volume
        self.editing_volume = False

    def handle_events(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if self.editing_volume:
                if event.key == pygame.K_LEFT:
                    self._adjust_volume(-0.1)
                elif event.key == pygame.K_RIGHT:
                    self._adjust_volume(0.1)
                elif event.key == pygame.K_RETURN:
                    self.sound_manager.play_sound('click')
                    self.editing_volume = False
            else:
                if event.key == pygame.K_DOWN:
                    self.selected_option = (self.selected_option + 1) % len(self.options)
                elif event.key == pygame.K_UP:
                    self.selected_option = (self.selected_option - 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    self.sound_manager.play_sound('click')
                    if self.selected_option == len(self.options) - 1:
                        self.game.change_state(GameState.MAIN_MENU)
                    elif self.selected_option in [0, 1]:
                        self.editing_volume = True
                elif event.key == pygame.K_ESCAPE:
                    self.game.change_state(GameState.MAIN_MENU)

    def _adjust_volume(self, delta: float):
        """Регулирует текущую громкость"""
        if self.selected_option == 0:  # Музыка
            self.music_volume = max(0.0, min(1.0, self.music_volume + delta))
            self.game.sound_manager.set_music_volume(self.music_volume)
        elif self.selected_option == 1:  # Звуки
            self.sound_volume = max(0.0, min(1.0, self.sound_volume + delta))
            self.game.sound_manager.set_sound_volume(self.sound_volume)

    def render(self) -> None:
        self.screen.fill(Config.BLACK)

        title = self.font.render("Настройки", True, Config.WHITE)
        title_rect = title.get_rect(center=(Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT // 4))
        self.screen.blit(title, title_rect)

        for i, option in enumerate(self.options):
            if i in [0, 1]:
                volume = self.music_volume if i == 0 else self.sound_volume
                color = Config.YELLOW if i == self.selected_option else Config.WHITE
                if i == self.selected_option and self.editing_volume:
                    text = self.font.render(">  " + option + f": {volume:.1}  <", True, color)
                else:
                    text = self.font.render(option + f": {volume:.1}", True, color)
                text_rect = text.get_rect(center=(Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT // 2 + i * 40))
                self.screen.blit(text, text_rect)
            else:
                color = Config.YELLOW if i == self.selected_option else Config.WHITE
                text = self.font.render(option, True, color)
                text_rect = text.get_rect(center=(Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT // 2 + i * 40))
                self.screen.blit(text, text_rect)
