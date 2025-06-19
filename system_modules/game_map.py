import json
import numpy as np
import pygame
from typing import Optional, List
from system_modules.config import Config
from entities.objects.game_object import GameObject, Stop, RadioactiveZone, GasStation


class GameMap:
    def __init__(self, path: str, objects_path: Optional[str] = None):
        self.heightmap = self._load_heightmap(path)
        self.max_height = self.heightmap.max()
        self.objects: List[GameObject] = []
        self.width, self.height = self.heightmap.shape
        self.last_camera_pos = (Config.SCREEN_WIDTH / 2, Config.SCREEN_HEIGHT / 2)
        self.cached_surface = pygame.Surface((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        if objects_path:
            self._load_objects_from_json(objects_path)
        self.terrain = self._load_terrain_texture()
        self.tile_cache = {}
        self.tile_elevation_cache = {}

    @staticmethod
    def _load_terrain_texture():
        try:
            terrain = pygame.image.load('./assets/terrain.png').convert_alpha()
            return pygame.transform.scale(terrain, (100, 100))
        except FileNotFoundError:
            print("Terrain texture not found")
            return None

    def _load_objects_from_json(self, path: str):
        with open(path, 'r') as f:
            objects_data = json.load(f)

        for obj in objects_data:
            if obj['type'] == "stop":
                game_object = Stop(
                    x=obj['x'],
                    y=obj['y'],
                    name=obj['name'],
                    capacity=obj['capacity']
                )
            elif obj['type'] == "radioactive_zone":
                game_object = RadioactiveZone(
                    x=obj['x'],
                    y=obj['y'],
                    radius=obj['radius'],
                    intensity=obj['intensity']
                )
            elif obj['type'] == "gas_station":
                game_object = GasStation(
                    x=obj['x'],
                    y=obj['y'],
                    fuel_capacity=obj.get('fuel_capacity', 5000.0)
                )
            else:
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
        return np.load(path)['arr_0']

    def get_elevation(self, x: float, y: float) -> float:
        return self.heightmap[int(max(0, min(x, self.width-1))), int(max(0, min(y, self.height-1)))] / self.max_height

    def draw(self, surface: pygame.Surface, camera) -> None:
        if self._should_redraw(camera):
            self._redraw_map(camera)

        surface.blit(self.cached_surface, (0, 0))

    def _should_redraw(self, camera) -> bool:
        return (abs(camera.camera_rect.x - self.last_camera_pos[0]) > 0 or
                abs(camera.camera_rect.y - self.last_camera_pos[1]) > 0 or
                self.cached_surface is None)

    def _create_tile_surface(self, height: float, tile_size: int) -> pygame.Surface:
        """Создает поверхность плитки с учетом высоты (кэширует результат)"""
        # Используем кэш при наличии
        if height in self.tile_cache:
            return self.tile_cache[height]

        # Создаем поверхность для плитки
        tile_surf = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)

        # Заливаем базовый цвет в зависимости от высоты
        base_color = (int(255 * height), int(255 * height), int(255 * height))
        tile_surf.fill(base_color)

        # Накладываем текстуру если доступна
        if self.terrain:
            # Масштабируем текстуру к размеру плитки
            texture = pygame.transform.smoothscale(self.terrain, (tile_size, tile_size))
            # Комбинируем с альфа-каналом
            tile_surf.blit(texture, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        # Кэшируем результат
        self.tile_cache[height] = tile_surf
        return tile_surf

    def get_tile_elevation(self, x: int, y: int, tile_size: int) -> float:
        """Вычисляет среднюю высоту для тайла 10x10 с началом в (x, y)"""
        # Проверяем кэш
        cache_key = (x // tile_size, y // tile_size)
        if cache_key in self.tile_elevation_cache:
            return self.tile_elevation_cache[cache_key]

        # Определяем границы тайла
        x_end = min(x + tile_size, self.width)
        y_end = min(y + tile_size, self.height)

        # Вычисляем среднюю высоту
        total = 0.0
        count = 0

        for i in range(int(x), int(x_end), 4):
            for j in range(int(y), int(y_end), 4):
                total += self.get_elevation(i, j)
                count += 1

        avg_height = total / count if count > 0 else 0.0

        # Сохраняем в кэш
        self.tile_elevation_cache[cache_key] = avg_height
        return avg_height

    def _redraw_map(self, camera) -> None:
        self.last_camera_pos = (camera.camera_rect.x, camera.camera_rect.y)
        self.cached_surface.fill(Config.BLACK)

        tile_size = 20
        start_x = max(0, -camera.camera_rect.x // tile_size * tile_size)
        end_x = min(self.width, start_x + Config.SCREEN_WIDTH + tile_size)

        start_y = max(0, -camera.camera_rect.y // tile_size * tile_size)
        end_y = min(self.height, start_y + Config.SCREEN_HEIGHT + tile_size)

        if self.terrain:
            for x in range(int(start_x), int(end_x), tile_size):
                for y in range(int(start_y), int(end_y), tile_size):
                    height_val = self.get_tile_elevation(x, y, tile_size)
                    tile_surf = self._create_tile_surface(height_val, tile_size)

                    # Позиция с учетом камеры
                    screen_x = x + camera.camera_rect.x
                    screen_y = y + camera.camera_rect.y

                    # Рисуем готовую плитку
                    self.cached_surface.blit(tile_surf, (screen_x, screen_y))
        else:
            for x in range(int(start_x), int(end_x), tile_size):
                for y in range(int(start_y), int(end_y), tile_size):
                    height = self.get_elevation(x, y)
                    color = (int(240 * height), int(230 * height), int(140 * height))
                    pygame.draw.rect(
                        self.cached_surface,
                        color,
                        (x + camera.camera_rect.x, y + camera.camera_rect.y, 10, 10)
                    )
