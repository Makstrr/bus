import pygame
from game_state import GameState


class BaseScreen:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.font = game.font
        self.assets = game.assets

    def handle_events(self, event: pygame.event.Event) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def render(self) -> None:
        pass

    def on_enter(self, **kwargs) -> None:
        pass

    def on_exit(self) -> None:
        pass
