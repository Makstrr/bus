import pygame
from screens.base_screen import BaseScreen
from game_state import GameState
from config import Config
from typing import Optional, Callable


class EventScreen(BaseScreen):
    def __init__(self, game):
        super().__init__(game)
        self.event_text = ""
        self.callback = None

    def on_enter(self, text: str = "", callback: Optional[Callable] = None, **kwargs) -> None:
        self.event_text = text
        self.callback = callback

    def handle_events(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
            if self.callback:
                self.callback()
            self.game.change_state(GameState.GAME)

    def render(self) -> None:
        overlay = pygame.Surface((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        lines = self._wrap_text(self.event_text, Config.SCREEN_WIDTH - 100)
        for i, line in enumerate(lines):
            text = self.font.render(line, True, Config.WHITE)
            text_rect = text.get_rect(center=(Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT // 2 + i * 30))
            self.screen.blit(text, text_rect)

        hint = self.font.render("Нажмите Enter для продолжения...", True, Config.YELLOW)
        hint_rect = hint.get_rect(center=(Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT - 50))
        self.screen.blit(hint, hint_rect)

    def _wrap_text(self, text: str, max_width: int) -> list:
        words = text.split(' ')
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            if self.font.size(test_line)[0] <= max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines
