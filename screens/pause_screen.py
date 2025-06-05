import pygame
from screens.base_screen import BaseScreen
from game_state import GameState
from config import Config


class PauseScreen(BaseScreen):
    def __init__(self, game):
        super().__init__(game)
        self.options = ["Продолжить", "Настройки", "В главное меню"]
        self.selected_option = 0
        self.overlay = self._create_overlay()

    @staticmethod
    def _create_overlay() -> pygame.Surface:
        """Создает полупрозрачный оверлей"""
        overlay = pygame.Surface(
            (Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT),
            pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 180))
        return overlay

    def handle_events(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(self.options)
            elif event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                if self.selected_option == 0:
                    self.game.change_state(GameState.GAME)
                elif self.selected_option == 1:
                    self.game.change_state(GameState.SETTINGS)
                elif self.selected_option == 2:
                    self.game.change_state(GameState.MAIN_MENU)
            elif event.key == pygame.K_ESCAPE:
                self.game.change_state(GameState.GAME)

    def render(self) -> None:
        if self.game.last_frame:
            self.screen.blit(self.game.last_frame, (0, 0))
        else:
            self.screen.fill(Config.BLACK)

        self.screen.blit(self.overlay, (0, 0))

        title = self.font.render("Пауза", True, Config.WHITE)
        title_rect = title.get_rect(center=(Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT // 3))
        self.screen.blit(title, title_rect)

        for i, option in enumerate(self.options):
            color = Config.YELLOW if i == self.selected_option else Config.WHITE
            text = self.font.render(option, True, color)
            text_rect = text.get_rect(center=(Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT // 2 + i * 40))
            self.screen.blit(text, text_rect)
