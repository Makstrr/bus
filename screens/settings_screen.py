import pygame
from screens.base_screen import BaseScreen
from game_state import GameState
from config import Config


# TODO: реализовать функционал и сохранение настроек в config.json
class SettingsScreen(BaseScreen):
    def __init__(self, game):
        super().__init__(game)
        self.options = ["Громкость музыки", "Громкость звуков", "Управление", "Назад"]
        self.selected_option = 0

    def handle_events(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(self.options)
            elif event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                if self.selected_option == len(self.options) - 1:
                    self.game.change_state(GameState.MAIN_MENU)
            elif event.key == pygame.K_ESCAPE:
                self.game.change_state(GameState.MAIN_MENU)

    def render(self) -> None:
        self.screen.fill(Config.BLACK)

        title = self.font.render("Настройки", True, Config.WHITE)
        title_rect = title.get_rect(center=(Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT // 4))
        self.screen.blit(title, title_rect)

        for i, option in enumerate(self.options):
            color = Config.YELLOW if i == self.selected_option else Config.WHITE
            text = self.font.render(option, True, color)
            text_rect = text.get_rect(center=(Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT // 2 + i * 40))
            self.screen.blit(text, text_rect)
