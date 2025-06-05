import pygame
from game_state import GameState
from config import Config
from game_map import GameMap
from typing import Optional
from bus import Bus
from screens.main_menu_screen import MainMenuScreen
from screens.settings_screen import SettingsScreen
from screens.game_screen import GameScreen
from screens.pause_screen import PauseScreen
from screens.event_screen import EventScreen
from screens.game_over_screen import GameOverScreen
from screens.story_screen import StoryScreen


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        pygame.display.set_caption("Симулятор вождения автобуса")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Monospace Regular', 30)
        self.assets = {}
        self.last_frame = None
        self.story_file = None

        self.game_map: Optional[GameMap] = None
        self.bus: Optional[Bus] = None

        self.state_handlers = {
            GameState.MAIN_MENU: MainMenuScreen,
            GameState.SETTINGS: SettingsScreen,
            GameState.GAME: GameScreen,
            GameState.PAUSE: PauseScreen,
            GameState.EVENT: EventScreen,
            GameState.GAME_OVER: GameOverScreen,
            GameState.STORY: StoryScreen,
        }

        self.current_state: Optional[GameState] = None
        self.current_screen: Optional[GameScreen] = None
        self.running = False

        self.change_state(GameState.MAIN_MENU)

    def reset_game(self):
        self.game_map = GameMap("assets/heightmap.npy", "map.json")
        self.bus = Bus(self.game_map.width // 2, self.game_map.height // 2)

    def change_state(self, new_state: GameState, **kwargs) -> None:
        if self.current_screen:
            self.current_screen.on_exit()

        if new_state == GameState.GAME:
            if self.current_state in [GameState.MAIN_MENU, GameState.GAME_OVER, GameState.STORY, None]:
                self.reset_game()

        if new_state == GameState.PAUSE:
            self.last_frame = self.screen.copy()

        if new_state == GameState.STORY:
            self.story_file = kwargs.get('story_file', 'story.json')

        self.current_state = new_state

        if new_state == GameState.QUIT:
            self.running = False
            return

        self.current_screen = self.state_handlers[new_state](self)
        if new_state == GameState.STORY:
            self.current_screen.on_enter(story_file=self.story_file)
        else:
            self.current_screen.on_enter(**kwargs)

    def run(self) -> None:
        self.running = True
        while self.running:
            dt = self.clock.tick(Config.FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if self.current_screen:
                    self.current_screen.handle_events(event)

            if self.current_screen:
                if self.current_screen != GameState.PAUSE:
                    self.current_screen.update(dt)
                self.current_screen.render()

            pygame.display.flip()

        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()
