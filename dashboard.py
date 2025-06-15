import pygame
import math
from config import Config


class Dashboard:
    """Класс для отображения приборной панели"""

    def __init__(self, bus):
        self.bus = bus
        self.font = pygame.font.SysFont('Monospace Regular', 24)
        self.small_font = pygame.font.SysFont('Monospace Regular', 18)
        self.padding = 20
        self.spacing = 80

        try:
            self.speedometer_icon = pygame.image.load('assets/dashboard/speedometer.png').convert_alpha()
            self.speedometer_icon = pygame.transform.scale(self.speedometer_icon, (40, 40))
        except:
            self.speedometer_icon = self._create_dummy_icon(Config.RED)

        try:
            self.fuel_icon = pygame.image.load('assets/dashboard/fuel.png').convert_alpha()
            self.fuel_icon = pygame.transform.scale(self.fuel_icon, (30, 30))
        except:
            self.fuel_icon = self._create_dummy_icon(Config.YELLOW)

        try:
            self.engine_icon = pygame.image.load('assets/dashboard/engine.png').convert_alpha()
            self.engine_icon = pygame.transform.scale(self.engine_icon, (80, 80))
        except:
            self.engine_icon = self._create_dummy_icon(Config.BLUE)

    @staticmethod
    def _create_dummy_icon(color):
        """Создает временную иконку, если основная не найдена"""
        icon = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(icon, color, (15, 15), 15)
        return icon

    def draw(self, surface):
        """Отрисовывает приборную панель"""
        # Фон панели
        dashboard_rect = pygame.Rect(0, Config.SCREEN_HEIGHT - 100, Config.SCREEN_WIDTH, 100)
        pygame.draw.rect(surface, (30, 30, 40), dashboard_rect)
        pygame.draw.line(surface, Config.GRAY,
                         (0, Config.SCREEN_HEIGHT - 100),
                         (Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT - 100), 2)

        # Скорость
        surface.blit(self.speedometer_icon, (self.padding, Config.SCREEN_HEIGHT - 93))
        speed_text = self.font.render(f"{abs(int(self.bus.speed * 12))} км/ч", True, Config.WHITE)
        surface.blit(speed_text, (self.padding + 40, Config.SCREEN_HEIGHT - 80))

        # Топливо
        fuel_x = self.padding + self.spacing * 2
        surface.blit(self.fuel_icon, (fuel_x, Config.SCREEN_HEIGHT - 90))

        # Полоска топлива
        fuel_width = 150
        fuel_height = 20
        fuel_rect = pygame.Rect(fuel_x + 40, Config.SCREEN_HEIGHT - 85, fuel_width, fuel_height)
        pygame.draw.rect(surface, Config.BLACK, fuel_rect, 2)  # Рамка

        fuel_level = max(0, min(1, self.bus.fuel / 100))
        fill_width = int(fuel_width * fuel_level)
        fill_color = Config.GREEN if fuel_level > 0.3 else Config.YELLOW if fuel_level > 0.1 else Config.RED
        pygame.draw.rect(surface, fill_color,
                         (fuel_x + 40, Config.SCREEN_HEIGHT - 85, fill_width, fuel_height))

        fuel_text = self.small_font.render(f"{int(fuel_level * 100)}%", True, Config.WHITE)
        surface.blit(fuel_text, (fuel_x + 40 + fuel_width + 10, Config.SCREEN_HEIGHT - 80))

        # Состояние двигателя
        engine_x = self.padding + self.spacing * 4.7
        if self.bus.condition <= 10:
            surface.blit(self.engine_icon, (engine_x, Config.SCREEN_HEIGHT - 100))

        # Счет
        score_x = self.padding + self.spacing * 6
        score_text = self.font.render(f"Счёт: {int(self.bus.score)}", True, Config.WHITE)
        surface.blit(score_text, (score_x, Config.SCREEN_HEIGHT - 80))

        # Направление
        direction_x = self.padding + self.spacing * 8
        direction = self._get_direction_name()
        direction_text = self.font.render(direction, True, Config.WHITE)
        surface.blit(direction_text, (direction_x, Config.SCREEN_HEIGHT - 80))

        # Компас
        compass_size = 30
        compass_rect = pygame.Rect(
            direction_x + 60,
            Config.SCREEN_HEIGHT - 85,
            compass_size, compass_size
        )
        pygame.draw.circle(surface, Config.BLACK, compass_rect.center, compass_size // 2, 2)

        # Стрелка компаса
        angle_rad = -self.bus.angle * (3.14159 / 180)
        end_x = compass_rect.centerx + (compass_size // 2 - 5) * math.sin(angle_rad)
        end_y = compass_rect.centery - (compass_size // 2 - 5) * math.cos(angle_rad)
        pygame.draw.line(surface, Config.RED, compass_rect.center, (end_x, end_y), 2)

    def _get_direction_name(self):
        """Возвращает название направления по углу"""
        angle = self.bus.angle % 360
        if 45 <= angle < 135:
            return "Восток"
        elif 135 <= angle < 225:
            return "Юг"
        elif 225 <= angle < 315:
            return "Запад"
        else:
            return "Север"