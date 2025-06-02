import math
from enum import Enum, auto
from random import randint
from typing import Optional

ratios = {
    'NEUTRAL': 0,
    'FIRST': 6.67,
    'SECOND': 4,
    'THIRD': 2.42,
    'FOURTH': 1.52,
    'REVERSE': -6.13
}


class GearState(Enum):
    """Состояния коробки передач."""
    NEUTRAL = auto()
    FIRST = auto()
    SECOND = auto()
    THIRD = auto()
    FOURTH = auto()
    REVERSE = auto()

    def get_ratio(self) -> float:
        return ratios[self.name]

    @classmethod
    def get_available_gears(cls) -> list:
        return [gear for gear in cls]


class Transmission:
    def __init__(self):
        self.speed = 0  # km/h
        self.engine = self.Engine()
        self.clutch = self.Clutch()
        self.gearbox = self.Gearbox()
        self.gear_shift_threshold = 0.3  # Максимальная нагрузка на сцепление для переключения

    def update(self, throttle_position: float, clutch_pedal_position: float, target_gear: Optional[GearState] = None):
        """
        Обновляет состояние трансмиссии.

        Args:
            throttle_position: Положение педали газа (0-1)
            clutch_pedal_position: Положение педали сцепления (0-1)
            target_gear: Целевая передача для переключения
        """
        # Обновляем сцепление
        self.clutch.update_realisation(clutch_pedal_position)

        # Управляем двигателем
        if throttle_position > 0:
            self.engine.accelerate(throttle_position)
        else:
            self.engine.decelerate()

        # Пытаемся переключить передачу если требуется
        if target_gear is not None and target_gear != self.gearbox.current_gear:
            self._attempt_gear_shift(target_gear)

        # Обновляем состояние коробки передач
        self._update_gearbox()

        # Обновляем скорость
        self._update_speed()

        # Обновляем состояние компонентов
        self.engine.update_condition()
        self._update_wear()

    def _update_gearbox(self):
        """Обновляет состояние коробки передач."""
        effective_rpm = self.engine.rpm * (1 - self.clutch.realisation) + \
                        self.gearbox.input_rpm * self.clutch.realisation

        self.gearbox.input_rpm = effective_rpm
        self.gearbox.update()
        self.clutch.update_strain(self.engine.rpm, self.gearbox.input_rpm)

    def _update_speed(self):
        """Обновляет скорость автобуса."""
        if self.gearbox.current_gear != GearState.NEUTRAL:
            wheel_rpm = self.gearbox.output_rpm / 3.5  # Примерное передаточное число главной передачи
            self.speed = wheel_rpm * 2.5 * 60 / 1000  # Преобразование в км/ч

    def _attempt_gear_shift(self, target_gear: GearState):
        """Пытается переключить передачу с проверкой условий."""
        # Проверка на нейтраль перед включением задней передачи
        if (target_gear == GearState.REVERSE and
                self.gearbox.current_gear != GearState.NEUTRAL):
            return

        # Проверка сцепления - должно быть достаточно выжато
        if self.clutch.realisation < 0.7:
            return

        # Проверка нагрузки на сцепление
        if self.clutch.strain > self.gear_shift_threshold:
            return

        # Расчет ожидаемых RPM после переключения
        if self.gearbox.current_gear != GearState.NEUTRAL:
            expected_rpm = self.gearbox.output_rpm * target_gear.get_ratio()

            # Проверка чтобы RPM не вышли за допустимые пределы
            if expected_rpm > self.engine.max_rpm * 1.1:
                self.engine.stall()
                self.gearbox.shift(target_gear)
                return
            if expected_rpm < self.engine.idle_rpm * 0.8 and target_gear != GearState.REVERSE:
                self.engine.stall()
                self.gearbox.shift(target_gear)
                return

        # Переключение передачи
        self.gearbox.shift(target_gear)

        # Корректировка RPM двигателя после переключения
        if self.gearbox.current_gear != GearState.NEUTRAL:
            self.gearbox.input_rpm = (self.gearbox.input_rpm * 1.8 + self.engine.rpm * 0.2) / 2
            self.engine.rpm = self.gearbox.input_rpm

    def _update_wear(self):
        """Обновляет износ компонентов."""
        # Износ сцепления при большой нагрузке
        if self.clutch.strain > 1.0:
            wear_factor = math.log10(self.clutch.strain + 1)
            self.clutch.durability -= 0.02 * wear_factor

        # Износ двигателя при высоких оборотах
        if self.engine.rpm > self.engine.max_rpm * 0.9:
            self.engine.durability -= 0.005 * (self.engine.rpm / self.engine.max_rpm)

        # Ограничение износа
        self.clutch.durability = max(0, min(100, self.clutch.durability))
        self.engine.durability = max(0, min(100, self.engine.durability))

    class Engine:
        def __init__(self):
            self.is_started = True
            self.rpm = 750
            self.durability = 100
            self.temperature = 50
            self.max_rpm = 3000
            self.idle_rpm = 750
            self.throttle_response = 0.5  # Скорость реакции на педаль газа

        def accelerate(self, throttle_position: float):
            if self.is_started:
                target_rpm = self.idle_rpm + (self.max_rpm - self.idle_rpm) * throttle_position
                self.rpm += (target_rpm - self.rpm) * self.throttle_response
                self.rpm = min(self.rpm, self.max_rpm * (self.durability / 100))

        def decelerate(self):
            if self.is_started:
                self.rpm = max(self.idle_rpm, self.rpm - 50)

        def start(self):
            self.is_started = True
            self.rpm = self.idle_rpm

        def stall(self):
            self.is_started = False
            self.rpm = 0
            self.durability -= 0.1

        def update_condition(self):
            heating_factor = math.e ** ((self.rpm - self.idle_rpm) / 1000)
            cooling_factor = 1
            self.temperature = (self.temperature + heating_factor - cooling_factor)

            if self.temperature > (110 + randint(-20, 20) / 10):
                self.stall()

    class Clutch:
        def __init__(self):
            self.durability = 100
            self.realisation = 1.0
            self.strain = 0.0
            self.max_strain = 5.0  # Максимальная нагрузка перед пробуксовкой

        def update_realisation(self, pedal_position: float):
            self.realisation = (math.e ** pedal_position - 1) / (math.e - 1)

        def update_strain(self, current_engine_rpm: float, current_gearbox_rpm: float):
            rpm_diff = abs(current_gearbox_rpm - current_engine_rpm)
            self.strain = rpm_diff / 100 * (1 - self.realisation)

            # Пробуксовка сцепления при слишком большой нагрузке
            if self.strain > self.max_strain * (self.durability / 100):
                self.realisation = min(1.0, self.realisation + 0.1)

    class Gearbox:
        def __init__(self):
            self.current_gear = GearState.NEUTRAL
            self.input_rpm = 0
            self.output_rpm = 0
            self.ratio = self.current_gear.get_ratio()

        def update(self):
            self.ratio = self.current_gear.get_ratio()
            if self.ratio != 0:
                self.output_rpm = self.input_rpm / self.ratio
            else:
                self.output_rpm -= 20

        def shift(self, new_gear: GearState):
            self.current_gear = new_gear
            self.ratio = new_gear.get_ratio()
