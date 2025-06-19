import pygame
import math
import random
from system_modules.config import Config
from random import randint
from entities.collider import Collider


class GameObject(pygame.sprite.Sprite):
    def __init__(self, x: float, y: float, obj_type: str, z_order: int = 0):
        super().__init__()
        self.type = obj_type
        self.z_order = z_order
        self._load_sprite()
        self.font = pygame.font.SysFont('monospace', 16)
        match obj_type:
            case "rock":
                self.collider = Collider((x, y), 70, 70, 0)
            case "tree":
                self.collider = Collider((x, y+45), 22, 20, 0)
            case "stop":
                self.collider = Collider((x, y + 31), 100, 62, 0)
            case "gas_station":
                self.collider = Collider((x, y + 30), 75, 25, 0)
            case "ruins":
                self.collider = Collider((x, y + 75), 300, 50, 0)
            case "building":
                self.collider = Collider((x, y), 150, 40, 0)
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        if obj_type != "radioactive_zone":
            self.base_y = self.collider.center[1]
        else:
            self.base_y = y

    def _load_sprite(self):
        self.sprites = {
            'tree': self._load_image('./assets/objects/tree.png', (70, 150 + randint(-10, 10))),
            'rock': self._load_image('./assets/objects/rock.png', (70, 70)),
            'ruins': self._load_image('./assets/objects/ruins.png', (300, 200)),
            'building': self._load_image('./assets/objects/building.png', (200, 200)),
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


class Stop(GameObject):
    """Остановка для посадки/высадки пассажиров"""
    def __init__(self, x: float, y: float, name: str, capacity: int = 20):
        super().__init__(x, y, "stop", z_order=1)
        self.name = name
        self.capacity = capacity
        self.passengers = randint(5, capacity)
        self.active = True
        self.waiting_time = 0
        self.spawn_timer = 0

        # Загрузка специального спрайта
        try:
            self.image = pygame.image.load('./assets/objects/bus_stop.png').convert_alpha()
            self.image = pygame.transform.scale(self.image, (125, 125))
        except:
            self.image = self._create_dummy_sprite((125, 125))

        self.rect = self.image.get_rect(center=(x, y))

    def update(self, dt: float):
        """Обновление состояния остановки"""
        if not self.active:
            return

        # Регенерация пассажиров
        self.spawn_timer += dt
        if self.spawn_timer > 5:  # Каждые 5 секунд

            self.spawn_timer = 0
            if self.passengers < self.capacity:
                self.passengers = min(self.capacity, self.passengers + randint(1, 3))


class RadioactiveZone(GameObject):
    """Класс для радиоактивных зон"""

    def __init__(self, x: float, y: float, radius: float, intensity: float = 1.0):
        super().__init__(x, y, "radioactive_zone", z_order=2)
        self.radius = radius
        self.intensity = intensity  # Уровень радиации (1.0 - стандартный)

        # Создаем поверхность для визуализации
        self.image = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        self._draw_zone()
        self.rect = self.image.get_rect(center=(x, y))

        # Для анимации
        self.pulse_timer = 0
        self.particles = []

    def _draw_zone(self):
        """Отрисовывает радиоактивную зону"""
        # Основной круг
        pygame.draw.circle(self.image, (0, 255, 0, 50), (self.radius, self.radius), self.radius)

    def update(self, dt: float):
        """Обновляет анимацию зоны"""
        self.pulse_timer += dt / 10

        # Пульсация зоны
        pulse_value = (abs(math.sin(self.pulse_timer * 3)) + 0.5) / 1.5
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)

        pygame.draw.circle(
            self.image,
            (int(110 * pulse_value), int(143 * pulse_value), int(48 * pulse_value), int(100 * pulse_value)),
            (self.radius, self.radius),
            self.radius
        )

        # Генерация частиц
        if random.random() < 0.5:
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, self.radius)
            speed = random.uniform(0.5, 2.0)
            deceleration = random.uniform(0.1, 0.5)
            size = random.randint(1, 3)
            lifetime = random.uniform(1.0, 3.0)

            self.particles.append({
                'x': self.radius + math.cos(angle) * distance,
                'y': self.radius + math.sin(angle) * distance,
                'dx': math.cos(angle) * speed,
                'dy': math.sin(angle) * speed,
                'deceleration': deceleration,
                'size': size,
                'lifetime': lifetime,
                'max_lifetime': lifetime
            })

        # Обновление частиц
        for particle in self.particles[:]:
            particle['x'] += particle['dx'] - dt * particle['deceleration']
            particle['y'] += particle['dy'] - dt * particle['deceleration']
            particle['lifetime'] -= dt

            if particle['lifetime'] <= 0:
                self.particles.remove(particle)

        self.draw_particles()

    def draw_particles(self):
        """Отрисовывает частицы радиации"""
        for particle in self.particles:
            alpha = int(255 * max(0.4, (particle['lifetime'] / particle['max_lifetime'])))
            color = (92, 141, 0, alpha)
            pygame.draw.circle(
                self.image,
                color,
                (int(particle['x']), int(particle['y'])),
                particle['size']
            )

    def get_radiation_level(self, x: float, y: float) -> float:
        """Возвращает уровень радиации в указанной точке"""
        distance = math.hypot(x - self.rect.centerx, y - self.rect.centery)

        if distance > self.radius:
            return 0.0

        # Уровень радиации уменьшается по мере удаления от центра
        return self.intensity * (1 - distance / self.radius)


class GasStation(GameObject):
    """Класс для заправочных станций"""

    def __init__(self, x: float, y: float, fuel_capacity: float = 5000.0):
        super().__init__(x, y, "gas_station", z_order=1)
        self.fuel_capacity = fuel_capacity  # Максимальное количество топлива
        self.current_fuel = fuel_capacity  # Текущий запас топлива
        self.refuel_speed = 5.0  # Скорость заправки (ед./сек)

        # Загрузка спрайта
        try:
            self.image = pygame.image.load('./assets/objects/gas_station.png').convert_alpha()
            self.image = pygame.transform.scale(self.image, (75, 100))
        except FileNotFoundError:
            self.image = self._create_dummy_sprite((75, 100))

        self.rect = self.image.get_rect(center=(x, y))

        # Для анимации
        self.pulse_timer = 0
        self.refueling = False

    def update(self, dt: float):
        """Обновляет анимацию"""
        self.pulse_timer += dt

        # Пульсация при заправке
        if self.refueling:
            pulse_value = abs(math.sin(self.pulse_timer * 5)) * 0.3 + 0.7
            self.image.set_alpha(int(255 * pulse_value))

    def refuel(self, bus: 'Bus', dt: float) -> bool:
        """Заправляет автобус, возвращает True, если заправка возможна и идет"""
        if self.current_fuel <= 0 or bus.fuel >= bus.max_fuel:
            self.refueling = False
            return False

        # Проверяем, что автобус остановился
        if abs(bus.speed) > 0.1:
            self.refueling = False
            return False

        # Проверяем, что автобус рядом
        distance = math.hypot(bus.x - self.rect.centerx, bus.y - self.rect.centery)
        if distance > 150:
            self.refueling = False
            return False

        # Заправка
        fuel_needed = bus.max_fuel - bus.fuel
        fuel_to_transfer = min(self.refuel_speed * dt, fuel_needed, self.current_fuel)

        bus.refueling = True
        bus.fuel += fuel_to_transfer
        self.current_fuel -= fuel_to_transfer * 10
        self.refueling = True

        return True
