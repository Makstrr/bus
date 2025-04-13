import math
import numpy as np
import pygame
from PIL import Image
from typing import Tuple, Optional


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


class GameMap:
    """Класс для работы с картой высот"""

    def __init__(self, path: str):
        self.heightmap = self._load_heightmap(path)
        self.width, self.height = self.heightmap.shape
        self.last_camera_pos = (Config.SCREEN_WIDTH / 2, Config.SCREEN_HEIGHT / 2)
        self.cached_surface = pygame.Surface((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))

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
                color = (240 * height, 230 * height, 140 * height)
                pygame.draw.rect(
                    self.cached_surface,
                    color,
                    (x + camera.camera_rect.x, y + camera.camera_rect.y, 10, 10)
                )


class Bus(pygame.sprite.Sprite):
    """Класс автобуса - основного управляемого объекта"""

    def __init__(self, x: float, y: float):
        super().__init__()
        self.x = x
        self.y = y
        self.width = 40
        self.height = 80
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

    def _load_sprites(self) -> list[pygame.Surface]:
        """Загружает или создает спрайты автобуса"""
        sprites = []
        for i in range(48):
            try:
                sprite_num = f"{i:03d}"
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
        pygame.draw.rect(dummy_surf, Config.YELLOW, (0, 0, 40, 80))
        pygame.draw.rect(dummy_surf, Config.BLUE, (5, 10, 30, 20))
        return dummy_surf

    def update(self, map_width: int, map_height: int, game_map: GameMap) -> None:
        """Обновляет состояние автобуса"""
        self._handle_input()
        self._update_speed(game_map)
        self._update_position(map_width, map_height)
        self._update_sprite()

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
        self.game_map = GameMap("assets/heightmap.png")
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

    def _handle_events(self) -> bool:
        """Обрабатывает события игры"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        return True

    def _update(self) -> None:
        """Обновляет состояние игры"""
        self.bus.update(self.game_map.width, self.game_map.height, self.game_map)
        self.camera.update(self.bus)

    def _render(self) -> None:
        """Отрисовывает игровые объекты"""
        self.game_map.draw(self.screen, self.camera)
        self.screen.blit(self.bus.image, self.camera.apply(self.bus))
        self.bus.draw_debug(self.screen, self.camera)

        # Отображение FPS
        fps_text = self.font.render(str(int(self.clock.get_fps())), False, Config.WHITE)
        self.screen.blit(fps_text, (0, 0))

        pygame.display.flip()


if __name__ == "__main__":
    game = Game()
    game.run()