from enum import Enum, auto
import math
from random import randint

ratios = {'NEUTRAL': 0,
          'FIRST': 6.67,
          'SECOND': 4,
          'THIRD': 2.42,
          'FOURTH': 1.52,
          'REVERSE': -6.13}


class GearState(Enum):
    """Состояния коробки передач."""
    NEUTRAL = auto()  # Нейтральная передача
    FIRST = auto()  # 1-я передача
    SECOND = auto()  # 2-я передача
    THIRD = auto()  # 3-я передача
    FOURTH = auto()  # 4-я передача
    REVERSE = auto()  # Задняя передача

    def get_ratio(self):
        return ratios[self.name]


class Transmission:
    def __init__(self):
        self.speed = 0  # kmh
        self.engine = self.Engine
        self.clutch = self.Clutch
        self.gearbox = self.Gearbox

    class Engine:
        def __init__(self):
            self.is_started = True
            self.rpm = 750
            self.durability = 100
            self.temperature = 50  # celsius degree

        def accelerate(self):
            if self.is_started:
                self.rpm = max(self.rpm + 10 * (self.durability / 100), 3000)

        def decelerate(self):
            if self.is_started:
                self.rpm = min(750, self.rpm - 5)

        def stall(self):
            self.is_started = False
            self.rpm = 0
            self.durability -= 0.1

        def update_condition(self):
            heating_factor = math.e ** ((self.rpm - 750) / 1000)
            cooling_factor = 1
            self.temperature = (self.temperature + heating_factor - cooling_factor)
            if self.temperature > (110 + randint(-20, 20) / 10):
                self.stall()

    class Clutch:
        def __init__(self):
            self.durability = 100
            self.realisation = 1.0
            self.strain = 0.0

        def update_realisation(self, pedal_position):
            self.realisation = (math.e ** pedal_position - 1) / (math.e - 1)

        def update_strain(self, current_engine_rpm, current_gearbox_rpm):
            self.strain = abs(current_gearbox_rpm - current_engine_rpm) / 100

    class Gearbox:
        def __init__(self):
            self.current_gear = GearState.NEUTRAL
            self.input_rpm = 0
            self.output_rpm = 0
            self.ratio = self.current_gear.get_ratio()

        def update(self):
            self.output_rpm = self.input_rpm / self.ratio

        def shift(self, new_shift: GearState):
            self.current_gear = new_shift
