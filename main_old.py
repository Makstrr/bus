import math
import json
import numpy as np
import pygame
from PIL import Image
from random import randint
from typing import Tuple, Optional, List, Dict


class Config:
    """Конфигурационные параметры игры"""
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    FPS = 60

    # Цвета
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GRAY = (100, 100, 100)
    GREEN = (0, 128, 0)
    BLUE = (0, 0, 255)
    RED = (255, 0, 0)
    YELLOW = (255, 255, 0)
    BROWN = (139, 69, 19)
    PURPLE = (128, 0, 128)
    MAGENTA = (255, 0, 255)


class Camera:
    """Класс для управления камерой, следующей за объектом"""

    def __init__(self, width: int, height: int, map_width: int, map_height: int):
        self.camera_rect = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.map_width = map_width
        self.map_height = map_height

    def apply(self, entity: pygame.sprite.Sprite) -> pygame.Rect:
        """Применяет смещение камеры к позиции объекта"""
        return entity.rect.move(self.camera_rect.x, self.camera_rect.y)

    def update(self, target: pygame.sprite.Sprite) -> None:
        """Обновляет позицию камеры для следования за целью"""
        x = -target.rect.centerx + self.width // 2
        y = -target.rect.centery + self.height // 2

        # Ограничение камеры границами карты
        x = min(0, x)  # Левая граница
        y = min(0, y)  # Верхняя граница
        x = max(-(self.map_width - self.width), x)  # Правая граница
        y = max(-(self.map_height - self.height), y)  # Нижняя граница

        self.camera_rect = pygame.Rect(x, y, self.width, self.height)


class Collider:
    """Класс коллайдеров для игровых объектов"""
    def __init__(self, center: Tuple[float, float], width: int, height: int, angle: float):
        self.center = center
        self.width = width
        self.height = height
        self.angle = angle  # В радианах

    def update(self, center: Tuple[float, float], angle: float) -> None:
        self.center = center
        self.angle = angle

    def check_intersections(self, colliders: List['Collider']) -> bool:
        for collider in colliders:
            if collider is self:
                continue
            if self._check_collision_with(collider):
                return True
        return False

    def _check_collision_with(self, other: 'Collider') -> bool:
        vertices_self = self.get_vertices()
        vertices_other = other.get_vertices()

        axes = self._get_axes() + other._get_axes()

        for axis in axes:
            min_self, max_self = self._project(vertices_self, axis)
            min_other, max_other = self._project(vertices_other, axis)
            if max_self < min_other or max_other < min_self:
                return False
        return True

    def get_vertices(self) -> List[List[float]]:
        half_w = self.width / 2
        half_h = self.height / 2
        corners = [
            (half_w, half_h),
            (-half_w, half_h),
            (-half_w, -half_h),
            (half_w, -half_h)
        ]
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        cx, cy = self.center
        vertices = []
        for x, y in corners:
            rot_x = x * cos_a - y * sin_a
            rot_y = x * sin_a + y * cos_a
            vertices.append([cx + rot_x, cy + rot_y])
        return vertices

    def _get_axes(self) -> List[List[float]]:
        return [
            [math.cos(self.angle), math.sin(self.angle)],
            [-math.sin(self.angle), math.cos(self.angle)]
        ]

    def _project(self, vertices: List[List[float]], axis: List[float]) -> tuple:
        min_proj = float('inf')
        max_proj = -float('inf')
        for x, y in vertices:
            proj = x * axis[0] + y * axis[1]
            min_proj = min(min_proj, proj)
            max_proj = max(max_proj, proj)
        return min_proj, max_proj


class GameObject(pygame.sprite.Sprite):
    """Класс игровых объектов с поддержкой z-уровня"""

    def __init__(self, x: float, y: float, obj_type: str, z_order: int = 0):
        super().__init__()
        self.type = obj_type
        self.z_order = z_order  # Для сортировки при отрисовке
        self._load_sprite()
        match obj_type:
            case "rock":
                self.collider = Collider((x, y), 70, 70, 0)
            case "tree":
                self.collider = Collider((x, y+40), 22, 20, 0)
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        self.base_y = y  # Для сортировки по вертикали

    def _load_sprite(self):
        """Загрузка спрайтов с учетом типа объекта"""
        self.sprites = {
            'tree': self._load_image('assets/objects/tree.png', (70, 150+randint(-10, 10))),
            'rock': self._load_image('assets/objects/rock.png', (70, 70)),
            # 'building': self._load_image('assets/objects/building.png', (80, 100))
        }
        self.image = self.sprites.get(self.type, self._create_dummy_sprite())

    @staticmethod
    def _load_image(path: str, size: tuple) -> pygame.Surface:
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(img, size)
        except FileNotFoundError:
            return GameObject._create_dummy_sprite(size)

    @staticmethod
    def _create_dummy_sprite(size=(30, 30)) -> pygame.Surface:
        surf = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(surf, Config.MAGENTA, (0, 0, *size))
        return surf


class GameMap:
    """Класс для работы с картой высот"""

    def __init__(self, path: str, objects_path: Optional[str] = None):
        self.heightmap = self._load_heightmap(path)
        self.objects: List[GameObject] = []
        self.width, self.height = self.heightmap.shape
        self.last_camera_pos = (Config.SCREEN_WIDTH / 2, Config.SCREEN_HEIGHT / 2)
        self.cached_surface = pygame.Surface((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        if objects_path:
            self._load_objects_from_json(objects_path)

    def _load_objects_from_json(self, path: str):
        """Загрузка объектов из JSON файла"""
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
        """Возвращает отсортированный список видимых объектов"""
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
        # Сортировка сначала по z_order, затем по y-координате
        visible.sort(key=lambda o: (o.z_order, o.base_y))
        return visible

    @staticmethod
    def _load_heightmap(path: str) -> np.ndarray:
        """Загружает карту высот из изображения"""
        img = Image.open(path).convert('L')
        return np.array(img)

    def get_elevation(self, x: float, y: float) -> float:
        """Возвращает нормализованную высоту (0.0-1.0) в указанных координатах"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.heightmap[int(x), int(y)] / 255.0
        return 0.0

    def draw(self, surface: pygame.Surface, camera: Camera) -> None:
        """Отрисовывает карту с учетом позиции камеры"""
        if self._should_redraw(camera):
            self._redraw_map(camera)

        surface.blit(self.cached_surface, (0, 0))

    def _should_redraw(self, camera: Camera) -> bool:
        """Проверяет, нужно ли перерисовывать карту"""
        return (abs(camera.camera_rect.x - self.last_camera_pos[0]) > 0 or
                abs(camera.camera_rect.y - self.last_camera_pos[1]) > 0 or
                self.cached_surface is None)

    def _redraw_map(self, camera: Camera) -> None:
        """Перерисовывает видимую часть карты"""
        self.last_camera_pos = (camera.camera_rect.x, camera.camera_rect.y)
        self.cached_surface.fill(Config.BLACK)

        # Определяем видимую область
        start_x = max(0, -camera.camera_rect.x // 10 * 10)
        end_x = min(self.width, start_x + Config.SCREEN_WIDTH + 10)

        start_y = max(0, -camera.camera_rect.y // 10 * 10)
        end_y = min(self.height, start_y + Config.SCREEN_HEIGHT + 10)

        # Рисуем карту по чанкам 10x10 пикселей
        for x in range(int(start_x), int(end_x), 10):
            for y in range(int(start_y), int(end_y), 10):
                height = self.get_elevation(x, y)
                color = (int(240 * height), int(230 * height), int(140 * height))
                pygame.draw.rect(
                    self.cached_surface,
                    color,
                    (x + camera.camera_rect.x, y + camera.camera_rect.y, 10, 10)
                )


class Bus(pygame.sprite.Sprite):
    """Класс автобуса - основного управляемого объекта"""

    def __init__(self, x: float, y: float):
        super().__init__()
        self.z_order = 1  # Между фоновыми (0) и передними (2) объектами
        self.base_y = y  # Для сортировки с другими объектами
        self.x = x
        self.y = y
        self.angle = 0  # угол в градусах
        self.speed = 0
        self.max_speed = 5
        self.acceleration = 0.1
        self.deceleration = 0.05
        self.rotation_speed = 2
        self.sprites = self._load_sprites()
        self.current_sprite = 36
        self.image = self.sprites[self.current_sprite]
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.collider = Collider((x, y), 40, 110, 0)

    def _load_sprites(self) -> list[pygame.Surface]:
        """Загружает или создает спрайты автобуса"""
        sprites = []
        for i in range(48):
            sprite_num = f"{i:03d}"
            try:
                img = pygame.image.load(
                    f"assets/yellow_bus/Yellow_BUS_CLEAN_All_{sprite_num}.png"
                ).convert_alpha()
                sprites.append(img)
            except FileNotFoundError:
                print(f"Не удалось загрузить спрайт bus_{sprite_num}.png")
                sprites.append(self._create_dummy_sprite())
        return sprites

    @staticmethod
    def _create_dummy_sprite() -> pygame.Surface:
        """Создает временный спрайт, если основной не найден"""
        dummy_surf = pygame.Surface((40, 80), pygame.SRCALPHA)
        pygame.draw.rect(dummy_surf, Config.MAGENTA, (0, 0, 40, 80))
        pygame.draw.rect(dummy_surf, Config.BLUE, (5, 10, 30, 20))
        return dummy_surf

    def update(self, map_width: int, map_height: int, game_map: GameMap, colliders: List[Collider]) -> None:
        """Обновляет состояние автобуса"""
        self._handle_input()
        self._update_speed(game_map)

        old_x = self.x
        old_y = self.y
        old_angle = self.angle
        self._update_position(map_width, map_height)
        self.collider.update((self.x, self.y), math.radians(self.angle))

        if self.collider.check_intersections(colliders):
            self.x = old_x
            self.y = old_y
            self.angle = old_angle
            self.speed = 0
            self.collider.update((old_x, old_y), math.radians(old_angle))

        self._update_sprite()
        self.base_y = self.y

    def _handle_input(self) -> None:
        """Обрабатывает пользовательский ввод"""
        keys = pygame.key.get_pressed()

        if keys[pygame.K_UP]:
            self.speed += self.acceleration
        elif keys[pygame.K_DOWN]:
            self.speed -= self.acceleration
        else:
            # Плавное замедление при отсутствии ввода
            if self.speed > 0:
                self.speed = max(0, self.speed - self.deceleration)
            elif self.speed < 0:
                self.speed = min(0, self.speed + self.deceleration)

        self.speed = max(-self.max_speed / 2, min(self.speed, self.max_speed))

        # Поворот только при движении
        if self.speed:
            if keys[pygame.K_LEFT]:
                self.angle += self.rotation_speed * (abs(self.speed) / self.max_speed)
            if keys[pygame.K_RIGHT]:
                self.angle -= self.rotation_speed * (abs(self.speed) / self.max_speed)

        self.angle %= 360

    def _update_speed(self, game_map: GameMap) -> None:
        """Обновляет скорость с учетом рельефа"""
        rad_angle = math.radians(self.angle)
        slope = self._calculate_slope(game_map)

        # Проверка крутых подъемов/спусков
        front_height_diff = game_map.get_elevation(
            self.x - 55 * math.sin(rad_angle),
            self.y - 55 * math.cos(rad_angle)
        ) - game_map.get_elevation(
            self.x - 45 * math.sin(rad_angle),
            self.y - 45 * math.cos(rad_angle)
        )

        rear_height_diff = game_map.get_elevation(
            self.x + 55 * math.sin(rad_angle),
            self.y + 55 * math.cos(rad_angle)
        ) - game_map.get_elevation(
            self.x + 25 * math.sin(rad_angle),
            self.y + 25 * math.cos(rad_angle)
        )

        if front_height_diff > 0.3 and self.speed > 0:
            self.speed = 0
        elif rear_height_diff > 0.3 and self.speed < 0:
            self.speed = 0
        elif game_map.get_elevation(self.x + 25 * math.sin(rad_angle), self.y + 25 * math.cos(rad_angle)) > \
                game_map.get_elevation(self.x - 45 * math.sin(rad_angle), self.y - 45 * math.cos(rad_angle)):
            self.speed += 0.1 * slope
        else:
            self.speed -= 0.1 * slope

    def _update_position(self, map_width: int, map_height: int) -> None:
        """Обновляет позицию автобуса"""
        rad_angle = math.radians(self.angle)
        self.x -= self.speed * math.sin(rad_angle)
        self.y -= self.speed * math.cos(rad_angle)

        # Ограничение позиции границами карты
        self.x = max(0, min(self.x, map_width))
        self.y = max(0, min(self.y, map_height))

        self.rect.centerx = max(20, min(self.rect.centerx, map_width - 20))
        self.rect.centery = max(20, min(self.rect.centery, map_height - 20))

    def _update_sprite(self) -> None:
        """Обновляет текущий спрайт автобуса"""
        self.current_sprite = (int(-self.angle / 7.5) + 36) % 48
        self.image = self.sprites[self.current_sprite]
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def _calculate_slope(self, game_map: GameMap) -> float:
        """Вычисляет крутизну склона в текущей позиции"""
        dx = game_map.get_elevation(self.x + 25, self.y) - game_map.get_elevation(self.x - 45, self.y)
        dy = game_map.get_elevation(self.x, self.y + 25) - game_map.get_elevation(self.x, self.y - 45)
        return math.sqrt(dx * dx + dy * dy)

    def draw_debug(self, surface: pygame.Surface, camera: Camera) -> None:
        """Отрисовывает отладочную информацию"""
        rad_angle = math.radians(self.angle)
        points = [
            (self.x + 25 * math.sin(rad_angle), self.y + 25 * math.cos(rad_angle)),
            (self.x - 45 * math.sin(rad_angle), self.y - 45 * math.cos(rad_angle)),
            (self.x + 55 * math.sin(rad_angle), self.y + 55 * math.cos(rad_angle)),
            (self.x - 55 * math.sin(rad_angle), self.y - 55 * math.cos(rad_angle)),
            (self.x, self.y)
        ]

        for point in points:
            pygame.draw.circle(
                surface,
                Config.RED,
                (int(point[0] + camera.camera_rect.x),
                 int(point[1] + camera.camera_rect.y)),
                3
            )


class Game:
    """Основной класс игры"""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        pygame.display.set_caption("Симулятор вождения автобуса")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Monospace Regular', 30)

        # Инициализация игровых объектов
        self.game_map = GameMap("assets/heightmap.png", "map.json")
        self.bus = Bus(self.game_map.width // 2, self.game_map.height // 2)
        self.camera = Camera(
            Config.SCREEN_WIDTH,
            Config.SCREEN_HEIGHT,
            self.game_map.width,
            self.game_map.height
        )

    def run(self) -> None:
        """Основной игровой цикл"""
        running = True
        while running:
            running = self._handle_events()
            self._update()
            self._render()
            self.clock.tick(Config.FPS)

        pygame.quit()

    @staticmethod
    def _handle_events() -> bool:
        """Обрабатывает события игры"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        return True

    def _update(self) -> None:
        """Обновляет состояние игры"""
        all_entities = self.game_map.get_sorted_objects(self.camera.camera_rect)
        all_colliders = []
        for entity in all_entities:
            all_colliders.append(entity.collider)
        self.bus.update(self.game_map.width, self.game_map.height, self.game_map, all_colliders)
        self.camera.update(self.bus)

    def _render(self) -> None:
        """Отрисовывает игровые объекты"""
        self.game_map.draw(self.screen, self.camera)

        all_entities = self.game_map.get_sorted_objects(self.camera.camera_rect)
        all_entities.append(self.bus)
        all_entities.sort(key=lambda e: (e.z_order, e.base_y))

        for entity in all_entities:
            self.screen.blit(entity.image, self.camera.apply(entity))

        # self.screen.blit(self.bus.image, self.camera.apply(self.bus))
        self.bus.draw_debug(self.screen, self.camera)

        # Отображение FPS
        fps_text = self.font.render(str(int(self.clock.get_fps())), False, Config.WHITE)
        self.screen.blit(fps_text, (0, 0))

        pygame.display.flip()


if __name__ == "__main__":
    game = Game()
    game.run()
