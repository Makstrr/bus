from enum import Enum, auto


class GameState(Enum):
    MAIN_MENU = auto()
    SETTINGS = auto()
    GAME = auto()
    PAUSE = auto()
    EVENT = auto()
    GAME_OVER = auto()
    QUIT = auto()
    STORY = auto()
