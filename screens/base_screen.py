import pygame


class BaseScreen:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.sound_manager = game.sound_manager
        self.font = pygame.font.SysFont('Monospace Regular', 30)
        self.small_font = pygame.font.SysFont('Monospace Regular', 18)
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
