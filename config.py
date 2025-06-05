import json


class Config:
    # Цвета
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GRAY = (100, 100, 100)
    GREEN = (0, 128, 0)
    BLUE = (0, 0, 255)
    RED = (255, 0, 0)
    YELLOW = (255, 255, 0)
    BROWN = (139, 69, 19)
    PURPLE = (128, 0, 128)
    MAGENTA = (255, 0, 255)
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    FPS = 60

    # TODO: реализовать чтение конфига из json-файла, для этого нужно переделать логику использования конфига в
    #  остальном коде с атрибутов класса на атрибуты экземпляра, создаваемого в инициализации мэйна
    def __init__(self):
        self._extract_data_from_config_file()

    def _extract_data_from_config_file(self):
        self.SCREEN_WIDTH = 800
        self.SCREEN_HEIGHT = 600
        self.FPS = 60

    @staticmethod
    def _load_config_file():
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print("Файл конфигурации не найден!")
            exit(0)


