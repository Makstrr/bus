import pygame
from typing import List, Dict, Optional, Callable
from config import Config
from bus import Bus
from game_object import Stop
import math


class GameEvent:
    """Базовый класс для игровых событий"""

    def __init__(self, name: str, duration: float = 0):
        self.name = name
        self.duration = duration
        self.elapsed = 0
        self.completed = False
        self.callback: Optional[Callable] = None
        self.font = pygame.font.SysFont('Monospace Regular', 24)

    def start(self, callback: Optional[Callable] = None):
        """Начинает выполнение события"""
        self.callback = callback
        self.elapsed = 0
        self.completed = False

    def update(self, dt: float) -> bool:
        """Обновляет состояние события"""
        if self.completed:
            return True

        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.complete()
            return True

        return False

    def complete(self):
        """Завершает событие"""
        self.completed = True
        if self.callback:
            self.callback()

    def draw(self, surface: pygame.Surface):
        """Отрисовывает визуальное представление события"""
        pass


class PassengerBoardingEvent(GameEvent):
    """Событие посадки пассажиров, в качестве колбэка должно быть передано событие OnRouteEvent"""
    def __init__(self, stop: 'Stop', bus: 'Bus', target: 'Stop'):
        super().__init__("passenger_boarding_event", 3.0)  # Длительность 3 секунды
        self.target_stop = target
        self.stop = stop
        self.bus = bus
        self.passengers = min(
            stop.passengers,
            bus.capacity - bus.passengers
        )
        self.progress = 0

    def update(self, dt: float) -> bool:
        if self.completed:
            return True

        self.elapsed += dt
        self.progress = min(1.0, self.elapsed / self.duration)

        if self.progress >= 1.0:
            accepted = min(
                self.passengers,
                self.stop.passengers,
                self.bus.capacity - self.bus.passengers
            )
            self.bus.passengers += accepted
            self.stop.passengers -= accepted
            self.complete()
            return True

        return False

    def draw(self, surface: pygame.Surface):
        # Отрисовываем прогресс бар
        bar_width = 200
        bar_height = 30
        bar_x = Config.SCREEN_WIDTH // 2 - bar_width // 2
        bar_y = Config.SCREEN_HEIGHT - 150

        # Фон
        pygame.draw.rect(surface, (50, 50, 60), (bar_x, bar_y, bar_width, bar_height))

        # Заполнение
        fill_width = int(bar_width * self.progress)
        pygame.draw.rect(surface, Config.GREEN, (bar_x, bar_y, fill_width, bar_height))

        # Текст
        text = self.font.render(f"Посадка пассажиров: {self.stop.name}", True, Config.WHITE)
        text_rect = text.get_rect(center=(Config.SCREEN_WIDTH // 2, bar_y - 20))
        surface.blit(text, text_rect)

        # Количество пассажиров
        count_text = self.font.render(f"{int(self.progress * self.passengers)}/{self.passengers}", True, Config.WHITE)
        count_rect = count_text.get_rect(center=(Config.SCREEN_WIDTH // 2, bar_y + bar_height // 2))
        surface.blit(count_text, count_rect)


class PassengerDisboardingEvent(GameEvent):
    """Событие высадки пассажиров"""
    def __init__(self, stop: 'Stop', bus: 'Bus'):
        super().__init__("passenger_disboarding_event", 3.0)  # Длительность 3 секунды
        self.stop = stop
        self.bus = bus
        self.progress = 0

    def update(self, dt: float) -> bool:
        if self.completed:
            return True

        self.elapsed += dt
        self.progress = min(1.0, self.elapsed / self.duration)

        if self.progress >= 1.0:
            self.bus.score += self.bus.passengers * 5
            self.bus.passengers = 0
            self.complete()
            return True

        return False

    def draw(self, surface: pygame.Surface):
        # Отрисовываем прогресс бар
        bar_width = 200
        bar_height = 30
        bar_x = Config.SCREEN_WIDTH // 2 - bar_width // 2
        bar_y = Config.SCREEN_HEIGHT - 150

        # Фон
        pygame.draw.rect(surface, (50, 50, 60), (bar_x, bar_y, bar_width, bar_height))

        # Заполнение
        fill_width = int(bar_width * self.progress)
        pygame.draw.rect(surface, Config.GREEN, (bar_x, bar_y, fill_width, bar_height))

        # Текст
        text = self.font.render(f"Высадка пассажиров: {self.stop.name}", True, Config.WHITE)
        text_rect = text.get_rect(center=(Config.SCREEN_WIDTH // 2, bar_y - 20))
        surface.blit(text, text_rect)


class OnRouteEvent(GameEvent):
    """Событие рейса, в качестве колбэка должно быть передано событие PassengerDisboardingEvent"""
    def __init__(self, bus: 'Bus', target: 'Stop'):
        super().__init__("on_route_event", 300.0)  # Продолжительность - 5 минут
        self.bus = bus
        self.target_stop = target
        self.distance = 0

    def update(self, dt: float) -> bool:
        if self.completed:
            return True

        self.distance = math.hypot(
                        self.target_stop.rect.centerx - self.bus.x,
                        self.target_stop.rect.centery - self.bus.y)

        if self.distance < 200:
            self._complete(True)
            return True

        self.elapsed += dt

        if self.elapsed >= self.duration:
            self.bus.passengers = 0
            self._complete(False)
            return True

        return False

    def _complete(self, achieved: bool):
        """Завершает событие"""
        self.completed = True
        if achieved:
            if self.callback:
                self.callback()

    def draw(self, surface: pygame.Surface):
        text = self.font.render(f"Оставшееся время: {int((self.duration - self.elapsed) // 60)}:{int((self.duration - self.elapsed) % 60)}", True, Config.WHITE)
        text_rect = text.get_rect(center=(110, Config.SCREEN_HEIGHT - 30))
        surface.blit(text, text_rect)

        text = self.font.render(f"Цель: {self.target_stop.name}", True, Config.WHITE)
        text_rect = text.get_rect(center=(350, Config.SCREEN_HEIGHT - 30))
        surface.blit(text, text_rect)

        # Компас направления к цели
        compass_size = 30
        compass_rect = pygame.Rect(
            450,
            Config.SCREEN_HEIGHT - 45,
            compass_size, compass_size
        )
        pygame.draw.circle(surface, Config.BLACK, compass_rect.center, compass_size // 2, 2)

        dx = self.target_stop.rect.centerx - self.bus.x
        dy = self.target_stop.rect.centery - self.bus.y

        angle_rad = math.atan2(dy, dx)
        end_x = compass_rect.centerx + (compass_size // 2 - 5) * math.cos(angle_rad)
        end_y = compass_rect.centery + (compass_size // 2 - 5) * math.sin(angle_rad)
        pygame.draw.line(surface, Config.RED, compass_rect.center, (end_x, end_y), 2)

        text = self.font.render(f"{int(self.distance/10)} м", True, Config.YELLOW)
        text_rect = text.get_rect(center=(510, Config.SCREEN_HEIGHT - 30))
        surface.blit(text, text_rect)


class EventSystem:
    """Управление игровыми событиями"""

    def __init__(self):
        self.active_events: List[GameEvent] = []
        self.font = pygame.font.SysFont('Monospace Regular', 24)

    def has_active_event(self):
        """Проверяет наличие активных событий"""
        return True if self.active_events else False

    def add_event(self, event: GameEvent, callback: Optional[Callable] = None):
        """Добавляет новое событие"""
        event.start(callback)
        self.active_events.append(event)

    def update(self, dt: float):
        """Обновляет все активные события"""
        for event in self.active_events[:]:
            if event.update(dt):
                self.active_events.remove(event)

    def draw(self, surface: pygame.Surface):
        """Отрисовывает все активные события"""
        for event in self.active_events:
            event.draw(surface)

    def draw_debug(self, surface: pygame.Surface):
        text = self.font.render(
            f"Статус событий: {self.has_active_event()}",
            True, Config.WHITE)
        text_rect = text.get_rect(center=(200, 21))
        surface.blit(text, text_rect)
