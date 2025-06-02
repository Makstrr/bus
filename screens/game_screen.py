import pygame
import math
from screens.base_screen import BaseScreen
from game_state import GameState
from config import Config
from camera import Camera


class GameScreen(BaseScreen):
    def __init__(self, game):
        super().__init__(game)
        self.game_map = game.game_map
        self.bus = game.bus
        self.debug_mode = False
        self.camera = None

    def on_enter(self, **kwargs) -> None:
        self.camera = Camera(
            Config.SCREEN_WIDTH,
            Config.SCREEN_HEIGHT,
            self.game_map.width,
            self.game_map.height
        )

    def handle_events(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.change_state(GameState.PAUSE)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
            self.debug_mode = not self.debug_mode

    def update(self, dt: float) -> None:
        all_entities = self.game_map.get_sorted_objects(self.camera.camera_rect)
        all_colliders = [entity.collider for entity in all_entities]
        self.bus.update(self.game_map.width, self.game_map.height, self.game_map, all_colliders)
        self.camera.update(self.bus)

    def render(self) -> None:
        self.game_map.draw(self.screen, self.camera)

        all_entities = self.game_map.get_sorted_objects(self.camera.camera_rect)
        all_entities.append(self.bus)
        all_entities.sort(key=lambda e: (e.z_order, e.base_y))

        for entity in all_entities:
            self.screen.blit(entity.image, self.camera.apply(entity))

        if self.debug_mode:
            self._draw_colliders()
            self.bus.draw_debug(self.screen, self.camera)

        fps_text = self.font.render(f"FPS: {int(self.game.clock.get_fps())}", False, Config.WHITE)
        self.screen.blit(fps_text, (10, 10))

    def _draw_colliders(self) -> None:
        all_entities = self.game_map.objects + [self.bus]

        for entity in all_entities:
            if hasattr(entity, 'collider'):
                vertices = entity.collider.get_vertices()
                screen_vertices = []
                for x, y in vertices:
                    screen_x = x + self.camera.camera_rect.x
                    screen_y = y + self.camera.camera_rect.y
                    screen_vertices.append((screen_x, screen_y))

                pygame.draw.lines(
                    self.screen,
                    Config.RED,
                    True,
                    screen_vertices,
                    1
                )

                center = (
                    entity.collider.center[0] + self.camera.camera_rect.x,
                    entity.collider.center[1] + self.camera.camera_rect.y
                )
                axis_length = 30

                angle = entity.collider.angle
                end_x = center[0] + axis_length * math.cos(angle)
                end_y = center[1] + axis_length * math.sin(angle)
                pygame.draw.line(
                    self.screen,
                    Config.RED,
                    center,
                    (end_x, end_y),
                    2
                )

                perp_angle = angle + math.pi / 2
                end_x = center[0] + axis_length * math.cos(perp_angle)
                end_y = center[1] + axis_length * math.sin(perp_angle)
                pygame.draw.line(
                    self.screen,
                    Config.GREEN,
                    center,
                    (end_x, end_y),
                    2
                )
