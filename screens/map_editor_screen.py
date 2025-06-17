from map_editor import MapEditor
from screens.base_screen import BaseScreen
import pygame


class MapEditorScreen(BaseScreen):
    def __init__(self, game):
        super().__init__(game)
        self.editor = MapEditor(game)

    def handle_events(self, event: pygame.event.Event) -> None:
        self.editor.handle_events(event)

    def update(self, dt: float) -> None:
        self.editor.update(dt)

    def render(self) -> None:
        self.editor.draw()

    def on_enter(self, **kwargs) -> None:
        # Инициализируем редактор при входе
        self.editor = MapEditor(self.game)

    def on_exit(self) -> None:
        # Очищаем ресурсы при выходе
        self.editor = None
