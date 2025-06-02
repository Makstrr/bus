import pygame


class Camera:
    def __init__(self, width: int, height: int, map_width: int, map_height: int):
        self.camera_rect = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height
        self.map_width = map_width
        self.map_height = map_height

    def apply(self, entity: pygame.sprite.Sprite) -> pygame.Rect:
        return entity.rect.move(self.camera_rect.x, self.camera_rect.y)

    def update(self, target: pygame.sprite.Sprite) -> None:
        x = -target.rect.centerx + self.width // 2
        y = -target.rect.centery + self.height // 2

        # Ограничение камеры границами карты
        x = min(0, x)
        y = min(0, y)
        x = max(-(self.map_width - self.width), x)
        y = max(-(self.map_height - self.height), y)

        self.camera_rect = pygame.Rect(x, y, self.width, self.height)