import json
import numpy as np
import pygame
from PIL import Image
from typing import Optional, List
from config import Config
from game_object import GameObject


class GameMap:
    def __init__(self, path: str, objects_path: Optional[str] = None):
        self.heightmap = self._load_heightmap(path)
        self.objects: List[GameObject] = []
        self.width, self.height = self.heightmap.shape
        self.last_camera_pos = (Config.SCREEN_WIDTH / 2, Config.SCREEN_HEIGHT / 2)
        self.cached_surface = pygame.Surface((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        if objects_path:
            self._load_objects_from_json(objects_path)

    def _load_objects_from_json(self, path: str):
        with open(path, 'r') as f:
            objects_data = json.load(f)

        for obj in objects_data:
            game_object = GameObject(
                x=obj['x'],
                y=obj['y'],
                obj_type=obj['type'],
                z_order=obj.get('z_order', 0)
            )
            self.objects.append(game_object)

    def get_sorted_objects(self, camera_rect: pygame.Rect) -> List[GameObject]:
        visible_area = pygame.Rect(
            -camera_rect.x,
            -camera_rect.y,
            camera_rect.width,
            camera_rect.height
        )
        visible = [
            obj for obj in self.objects
            if visible_area.colliderect(obj.rect)
        ]
        visible.sort(key=lambda o: (o.z_order, o.base_y))
        return visible

    @staticmethod
    def _load_heightmap(path: str) -> np.ndarray:
        return np.load(path)

    def get_elevation(self, x: float, y: float) -> float:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.heightmap[int(x), int(y)] / 255.0
        return 0.0

    def draw(self, surface: pygame.Surface, camera) -> None:
        if self._should_redraw(camera):
            self._redraw_map(camera)

        surface.blit(self.cached_surface, (0, 0))

    def _should_redraw(self, camera) -> bool:
        return (abs(camera.camera_rect.x - self.last_camera_pos[0]) > 0 or
                abs(camera.camera_rect.y - self.last_camera_pos[1]) > 0 or
                self.cached_surface is None)

    def _redraw_map(self, camera) -> None:
        self.last_camera_pos = (camera.camera_rect.x, camera.camera_rect.y)
        self.cached_surface.fill(Config.BLACK)

        start_x = max(0, -camera.camera_rect.x // 10 * 10)
        end_x = min(self.width, start_x + Config.SCREEN_WIDTH + 10)

        start_y = max(0, -camera.camera_rect.y // 10 * 10)
        end_y = min(self.height, start_y + Config.SCREEN_HEIGHT + 10)

        for x in range(int(start_x), int(end_x), 10):
            for y in range(int(start_y), int(end_y), 10):
                height = self.get_elevation(x, y)
                color = (int(240 * height), int(230 * height), int(140 * height))
                pygame.draw.rect(
                    self.cached_surface,
                    color,
                    (x + camera.camera_rect.x, y + camera.camera_rect.y, 10, 10)
                )
