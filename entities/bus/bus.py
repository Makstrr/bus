import math
import pygame
from system_modules.config import Config
from system_modules.game_map import GameMap
from entities.objects.game_object import RadioactiveZone
from typing import List
from entities.collider import Collider


class Bus(pygame.sprite.Sprite):
    def __init__(self, x: float, y: float):
        super().__init__()
        self.z_order = 1
        self.base_y = y

        self.x = x
        self.y = y
        self.angle = 0
        self.speed = 0
        self.max_speed = 5
        self.absolute_max_speed = 5
        self.acceleration = 0.1
        self.absolute_max_acceleration = 0.1
        self.deceleration = 0.05
        self.fuel = 100
        self.max_fuel = 100
        self.refueling = False
        self.rotation_speed = 2

        self.sprites = self._load_sprites()
        self.current_sprite = 36
        self.image = self.sprites[self.current_sprite]
        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.collider = Collider((x, y), 40, 110, 0)
        self.collision_flag = False

        self.condition = 100
        self.passengers_condition = 100
        self.radiation_level = 0.0  # Текущий уровень радиации
        self.max_radiation = 100.0
        self.radiation_accumulation_rate = 5
        self.radiation_damage_factor = 0.1

        self.score = 0
        self.capacity = 30
        self.passengers = 0

    def _load_sprites(self) -> list[pygame.Surface]:
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
        dummy_surf = pygame.Surface((40, 80), pygame.SRCALPHA)
        pygame.draw.rect(dummy_surf, Config.MAGENTA, (0, 0, 40, 80))
        pygame.draw.rect(dummy_surf, Config.BLUE, (5, 10, 30, 20))
        return dummy_surf

    def update(self, map_width: int, map_height: int, game_map, dt: float, colliders: List[Collider]) -> None:
        self._handle_input()

        self.collision_flag = False

        if self.fuel == 0:
            self.acceleration = 0

        old_x = self.x
        old_y = self.y
        old_angle = self.angle
        self._update_position(map_width, map_height)
        self.collider.update((self.x, self.y), math.radians(-self.angle))

        if self.collider.check_intersections(colliders):
            self.collision_flag = True
            self.x = old_x
            self.y = old_y
            self.angle = old_angle
            self.speed = 0
            self.collider.update((self.x, self.y), math.radians(-old_angle))

        self._update_speed(game_map)

        fuel_consumption = 0.001 * abs(self.speed)
        self.fuel = max(0, self.fuel - fuel_consumption)

        self.refueling = False
        self._update_sprite()

        self._update_radiation(game_map, dt)
        self._apply_radiation_effects(dt)
        self.base_y = self.y

    def _handle_input(self) -> None:
        keys = pygame.key.get_pressed()

        if keys[pygame.K_UP] and self.speed < self.max_speed and not self.collision_flag:
            self.speed += self.acceleration
        elif keys[pygame.K_DOWN] and self.speed > -self.max_speed / 2 and not self.collision_flag:
            self.speed -= self.acceleration
        else:
            if self.speed > 0 and not self.collision_flag:
                self.speed = max(0.0, self.speed - self.deceleration)
            elif self.speed < 0 and not self.collision_flag:
                self.speed = min(0.0, self.speed + self.deceleration)

        if self.speed and not self.collision_flag:
            if keys[pygame.K_LEFT] and abs(self.speed) > 0.1:
                self.angle += self.rotation_speed * (abs(self.speed) / self.max_speed)
            if keys[pygame.K_RIGHT] and abs(self.speed) > 0.1:
                self.angle -= self.rotation_speed * (abs(self.speed) / self.max_speed)

        self.angle %= 360

    def _update_speed(self, game_map) -> None:
        rad_angle = math.radians(self.angle)
        slope = self._calculate_slope(game_map)

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

        if front_height_diff > 0.15 and self.speed > 0:
            self.speed = 0
        elif rear_height_diff > 0.15 and self.speed < 0:
            self.speed = 0
        elif game_map.get_elevation(self.x + 25 * math.sin(rad_angle), self.y + 25 * math.cos(rad_angle)) > \
                game_map.get_elevation(self.x - 45 * math.sin(rad_angle), self.y - 45 * math.cos(rad_angle)) and \
                not self.collision_flag:
            self.speed += 0.3 * slope
        else:
            self.speed -= 0.3 * slope

    def _update_position(self, map_width: int, map_height: int) -> None:
        rad_angle = math.radians(self.angle)
        self.x -= self.speed * math.sin(rad_angle)
        self.y -= self.speed * math.cos(rad_angle)

        self.x = max(0, min(self.x, map_width))
        self.y = max(0, min(self.y, map_height))

        self.rect.centerx = max(20, min(self.rect.centerx, map_width - 20))
        self.rect.centery = max(20, min(self.rect.centery, map_height - 20))

    def _update_sprite(self) -> None:
        self.current_sprite = (int(-self.angle / 7.5) + 36) % 48
        self.image = self.sprites[self.current_sprite]
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def _calculate_slope(self, game_map) -> float:
        dx = game_map.get_elevation(self.x + 25, self.y) - game_map.get_elevation(self.x - 45, self.y)
        dy = game_map.get_elevation(self.x, self.y + 25) - game_map.get_elevation(self.x, self.y - 45)
        return math.sqrt(dx * dx + dy * dy)

    def draw_debug(self, surface: pygame.Surface, camera) -> None:
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

    def _update_radiation(self, game_map: GameMap, dt: float):
        """Обновляет уровень радиации автобуса"""
        # Сбрасываем уровень радиации в зоне
        current_radiation_level = 0.0

        # Проверяем все радиоактивные зоны
        for obj in game_map.objects:
            if isinstance(obj, RadioactiveZone):
                radiation = obj.get_radiation_level(self.x, self.y)
                if radiation > current_radiation_level:
                    current_radiation_level = radiation

        # Накопление радиации
        if current_radiation_level > 0:
            self.radiation_level = min(
                self.max_radiation,
                self.radiation_level + current_radiation_level * self.radiation_accumulation_rate * dt
            )

    def _apply_radiation_effects(self, dt: float):
        """Применяет эффекты радиации"""
        if self.radiation_level <= 1:
            return

        self.condition = min(self.condition, self.max_radiation - self.radiation_level)
        self.passengers_condition = max(0.0, self.passengers_condition - self.radiation_level * self.radiation_damage_factor * 5 * dt)

        # Эффекты при разных уровнях радиации
        # radiation_factor = self.radiation_level / self.max_radiation

        # 1. Снижение максимальной скорости
        # speed_reduction = 0.5 * radiation_factor
        self.max_speed = self.absolute_max_speed * self.condition / 100
        self.acceleration = self.absolute_max_acceleration * self.condition / 100
        # self.effective_max_speed = self.max_speed * (1 - speed_reduction)
        # if self.speed > 0:
        #     self.speed = min(self.speed, self.effective_max_speed)
        # elif self.speed < 0:
        #     self.speed = max(self.speed, -self.effective_max_speed/2)

        # if radiation_factor > 0.7:
        #     if random.random() < 0.01:
        #         self.fuel_display_error = True
