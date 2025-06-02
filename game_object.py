import pygame
from config import Config
from random import randint
from collider import Collider


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
