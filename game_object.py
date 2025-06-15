import pygame
from config import Config
from random import randint
from collider import Collider
from bus import Bus


class GameObject(pygame.sprite.Sprite):
    def __init__(self, x: float, y: float, obj_type: str, z_order: int = 0):
        super().__init__()
        self.type = obj_type
        self.z_order = z_order
        self._load_sprite()
        match obj_type:
            case "rock":
                self.collider = Collider((x, y), 70, 70, 0)
            case "tree":
                self.collider = Collider((x, y+45), 22, 20, 0)
        self.rect = self.image.get_rect(center=(x, y))
        self.mask = pygame.mask.from_surface(self.image)
        self.base_y = y

    def _load_sprite(self):
        self.sprites = {
            'tree': self._load_image('assets/objects/tree.png', (70, 150+randint(-10, 10))),
            'rock': self._load_image('assets/objects/rock.png', (70, 70)),
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
        self.collider = Collider((x, y), 80, 80, 0)
        self.active = True
        self.waiting_time = 0
        self.spawn_timer = 0

        # Загрузка специального спрайта
        try:
            self.image = pygame.image.load('assets/objects/bus_stop.png').convert_alpha()
            self.image = pygame.transform.scale(self.image, (80, 80))
        except:
            self.image = self._create_dummy_sprite((80, 80))
            pygame.draw.circle(self.image, Config.YELLOW, (40, 40), 30)

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

    def interact(self, bus: 'Bus') -> int:
        """Взаимодействие с автобусом, возвращает количество принятых пассажиров"""
        if not self.active:
            return 0

        available_seats = bus.capacity - bus.passengers
        accepted = min(available_seats, self.passengers)

        if accepted > 0:
            bus.passengers += accepted
            self.passengers -= accepted
            return accepted

        return 0
