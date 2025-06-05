import pygame
from screens.base_screen import BaseScreen
from game_state import GameState
from config import Config


class MainMenuScreen(BaseScreen):
    def __init__(self, game):
        super().__init__(game)
        self.title_font = pygame.font.SysFont('Monospace Regular', 60)
        self.menu_items = ["Начать игру", "Настройки", "Выход"]
        self.selected_item = 0

    def handle_events(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                self.selected_item = (self.selected_item + 1) % len(self.menu_items)
            elif event.key == pygame.K_UP:
                self.selected_item = (self.selected_item - 1) % len(self.menu_items)
            elif event.key == pygame.K_RETURN:
                if self.selected_item == 0:
                    self.game.change_state(GameState.STORY, story_file='story.json')
                elif self.selected_item == 1:
                    self.game.change_state(GameState.SETTINGS)
                elif self.selected_item == 2:
                    self.game.change_state(GameState.QUIT)

    def render(self) -> None:
        self.screen.fill(Config.BLACK)

        title = self.title_font.render("Симулятор Автобуса", True, Config.WHITE)
        title_rect = title.get_rect(center=(Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT // 4))
        self.screen.blit(title, title_rect)

        for i, item in enumerate(self.menu_items):
            color = Config.YELLOW if i == self.selected_item else Config.WHITE
            text = self.font.render(item, True, color)
            text_rect = text.get_rect(center=(Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT // 2 + i * 50))
            self.screen.blit(text, text_rect)
