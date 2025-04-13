import json
import numpy as np
from PIL import Image
import pygame
import math
from random import randint

pygame.init()

# Настройки экрана
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Симулятор вождения автобуса")

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
GREEN = (0, 128, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BROWN = (139, 69, 19)

clock = pygame.time.Clock()
FPS = 60


class Camera:
    def __init__(self, width, height, map_width, map_height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.map_width = map_width
        self.map_height = map_height

    def apply(self, entity):
        return entity.rect.move(self.camera.x, self.camera.y)

    def update(self, target):
        # Плавное слежение за целью
        x = -target.rect.centerx + int(self.width / 2)
        y = -target.rect.centery + int(self.height / 2)

        # Ограничение камеры границами карты
        x = min(0, x)  # Левая граница
        y = min(0, y)  # Верхняя граница
        x = max(-(self.map_width - self.width), x)  # Правая граница
        y = max(-(self.map_height - self.height), y)  # Нижняя граница

        self.camera = pygame.Rect(x, y, self.width, self.height)


class Map:
    def __init__(self, path):
        self.heightmap = self.load_heightmap(path)
        self.width, self.height = self.heightmap.shape
        self.last_camera_pos = (SCREEN_WIDTH/2, SCREEN_HEIGHT/2)
        self.cached_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    def load_heightmap(self, path):
        img = Image.open(path).convert('L')  # Загружаем как grayscale
        return np.array(img)  # Преобразуем в numpy-массив

    def get_elevation(self, x, y):
        """Возвращает высоту в координатах (x,y) нормализованную от 0.0 до 1.0"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.heightmap[int(x), int(y)] / 255.0
        return 0.0

    def draw(self, surface, camera):
        # Проверяем, нужно ли перерисовывать (если камера сильно сместилась)
        if (abs(camera.camera.x - self.last_camera_pos[0]) > 0 or
                abs(camera.camera.y - self.last_camera_pos[1]) > 0 or
                self.cached_surface is None):

            self.last_camera_pos = (camera.camera.x, camera.camera.y)


            # Рисуем только видимую часть
            start_x = max(0, -camera.camera.x // 10 * 10)
            end_x = min(self.width, start_x + SCREEN_WIDTH + 10)

            start_y = max(0, -camera.camera.y // 10 * 10)
            end_y = min(self.height, start_y + SCREEN_HEIGHT + 10)

            for x in range(start_x, end_x, 10):
                for y in range(start_y, end_y, 10):
                    height = self.get_elevation(x, y)
                    color = (240 * height, 230 * height, 140 * height)
                    pygame.draw.rect(
                        self.cached_surface,
                        color,
                        (x + camera.camera.x, y + camera.camera.y, 10, 10)
                    )

        surface.blit(self.cached_surface, (0, 0))


class Bus:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 80
        self.angle = 0  # угол поворота в градусах
        self.speed = 0
        self.max_speed = 5
        self.acceleration = 0.1
        self.deceleration = 0.05
        self.rotation_speed = 2
        self.sprites = []
        for i in range(48):
            sprite_num = f"{i:03d}"
            try:
                img = pygame.image.load(f"assets/yellow_bus/Yellow_BUS_CLEAN_All_{sprite_num}.png").convert_alpha()
                self.sprites.append(img)
            except:
                print(f"Не удалось загрузить спрайт bus_{sprite_num}.png")
                dummy_surf = pygame.Surface((40, 80), pygame.SRCALPHA)
                pygame.draw.rect(dummy_surf, (255, 255, 0), (0, 0, 40, 80))
                pygame.draw.rect(dummy_surf, (100, 100, 255), (5, 10, 30, 20))
                self.sprites.append(dummy_surf)

        # Текущий спрайт
        self.current_sprite = 36
        self.image = self.sprites[self.current_sprite]
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def update(self, map_width, map_height, game_map):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.speed += self.acceleration
        elif keys[pygame.K_DOWN]:
            self.speed -= self.acceleration
        else:
            if self.speed > 0:
                self.speed = max(0, self.speed - self.deceleration)
            elif self.speed < 0:
                self.speed = min(0, self.speed + self.deceleration)

        self.speed = max(-self.max_speed / 2, min(self.speed, self.max_speed))
        slope = self.calculate_slope(game_map)

        self.current_sprite = (int(-self.angle / 7.5) + 36) % 48
        self.image = self.sprites[self.current_sprite]
        self.rect = self.image.get_rect(center=(self.x, self.y))

        if keys[pygame.K_LEFT] and self.speed:
            self.angle += self.rotation_speed * (self.speed / self.max_speed if self.speed != 0 else 1)
        if keys[pygame.K_RIGHT] and self.speed:
            self.angle -= self.rotation_speed * (self.speed / self.max_speed if self.speed != 0 else 1)
        self.angle %= 360

        rad_angle = math.radians(self.angle)
        if (game_map.get_elevation(self.x-55*math.sin(rad_angle), self.y-55*math.cos(rad_angle)) - game_map.get_elevation(self.x-45*math.sin(rad_angle), self.y-45*math.cos(rad_angle))) > 0.3:
            if self.speed > 0:
                self.speed = 0
        elif (game_map.get_elevation(self.x+55*math.sin(rad_angle), self.y+55*math.cos(rad_angle)) - game_map.get_elevation(self.x+25*math.sin(rad_angle), self.y+25*math.cos(rad_angle))) > 0.3:
            if self.speed < 0:
                self.speed = 0
        elif game_map.get_elevation(self.x+25*math.sin(rad_angle), self.y+25*math.cos(rad_angle)) > game_map.get_elevation(self.x-45*math.sin(rad_angle), self.y-45*math.cos(rad_angle)):
            self.speed += (0.1 * slope)
        else:
            self.speed -= (0.1 * slope)
        self.x -= self.speed * math.sin(rad_angle)
        self.y -= self.speed * math.cos(rad_angle)

        self.x = max(0, min(self.x, map_width))
        self.y = max(0, min(self.y, map_height))

        self.rect.centerx = max(20, min(self.rect.centerx, map_width - 20))
        self.rect.centery = max(20, min(self.rect.centery, map_height - 20))

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        pygame.draw.circle(surface, RED, (int(self.x), int(self.y)), 3)

    def calculate_slope(self, game_map):
        """Вычисляет крутизну склона в текущей позиции"""
        dx = game_map.get_elevation(self.x + 25, self.y) - game_map.get_elevation(self.x - 45, self.y)
        dy = game_map.get_elevation(self.x, self.y + 25) - game_map.get_elevation(self.x, self.y - 45)
        return math.sqrt(dx * dx + dy * dy)


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    # Загрузка карты
    game_map = Map("assets/heightmap.png")

    # Создание автобуса
    bus = Bus(game_map.width // 2, game_map.height // 2)

    # Создание камеры
    camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT, game_map.width, game_map.height)

    running = True
    while running:
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Обновление
        bus.update(game_map.width, game_map.height, game_map)
        camera.update(bus)

        # Отрисовка
        game_map.draw(screen, camera)
        screen.blit(bus.image, camera.apply(bus))
        pygame.draw.circle(screen, RED, (bus.x+25*math.sin(math.radians(bus.angle)) + camera.camera.x, bus.y+25*math.cos(math.radians(bus.angle)) + camera.camera.y), 3)
        pygame.draw.circle(screen, RED, (bus.x - 45 * math.sin(math.radians(bus.angle)) + camera.camera.x, bus.y - 45 * math.cos(math.radians(bus.angle)) + camera.camera.y), 3)
        pygame.draw.circle(screen, RED, (bus.x + 55 * math.sin(math.radians(bus.angle)) + camera.camera.x,
                                         bus.y + 55 * math.cos(math.radians(bus.angle)) + camera.camera.y), 3)
        pygame.draw.circle(screen, RED, (bus.x - 55 * math.sin(math.radians(bus.angle)) + camera.camera.x,
                                         bus.y - 55 * math.cos(math.radians(bus.angle)) + camera.camera.y), 3)
        pygame.draw.circle(screen, RED, (bus.x + camera.camera.x, bus.y + camera.camera.y), 3)
        # bus.draw(screen)

        # Обновление экрана
        clock.tick(FPS)
        fps = str(int(clock.get_fps()))
        font = pygame.font.SysFont('Monospace Regular', 30)
        textsurface = font.render(fps, False, (255, 255, 255))
        screen.blit(textsurface, (0, 0))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
