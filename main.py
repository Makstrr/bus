import pygame
from system_modules.game_state import GameState
from system_modules.config import Config
from system_modules.game_map import GameMap
from system_modules.sound_manager import SoundManager
from typing import Optional
from entities.bus.bus import Bus
from screens.main_menu_screen import MainMenuScreen
from screens.settings_screen import SettingsScreen
from screens.game_screen import GameScreen
from screens.pause_screen import PauseScreen
from screens.event_screen import EventScreen
from screens.game_over_screen import GameOverScreen
from screens.story_screen import StoryScreen
from screens.map_editor_screen import MapEditorScreen


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        pygame.display.set_caption("Икарус-235")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Monospace Regular', 30)
        self.assets = {}
        self.last_frame = None
        self.story_file = None

        self.sound_manager = SoundManager()
        self._load_audio()

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
            GameState.MAP_EDITOR: MapEditorScreen,
        }

        self.current_state: Optional[GameState] = None
        self.current_screen: Optional[GameScreen] = None
        self.screens = {}  # Кэширование созданных экранов
        self.running = False

        self.change_state(GameState.MAIN_MENU)

    def _load_audio(self):
        """Загружает аудиоресурсы"""
        self.sound_manager.load_sounds("assets/sounds")
        self.sound_manager.load_music("assets/music")

        # Настройка громкости по умолчанию
        self.sound_manager.set_music_volume(Config.MUSIC_VOLUME)
        self.sound_manager.set_sound_volume(Config.SFX_VOLUME)

        # Запуск фоновой музыки
        self.sound_manager.play_music("main_theme", loop=-1)

    def reset_game(self):
        self.game_map = GameMap("assets/heightmap.npz", "assets/map.json")
        self.bus = Bus(self.game_map.width // 2 + 300, self.game_map.height // 2 + 300)
        if GameState.GAME in self.screens:
            self.screens[GameState.GAME] = self.state_handlers[GameState.GAME](self)
        if GameState.STORY in self.screens:
            self.screens[GameState.STORY] = self.state_handlers[GameState.STORY](self)

    def change_state(self, new_state: GameState, **kwargs) -> None:
        if self.current_screen:
            self.current_screen.on_exit()

        if new_state == GameState.MAIN_MENU and self.current_state not in [GameState.SETTINGS, GameState.MAP_EDITOR]:
            self.sound_manager.play_music("main_theme")

        if new_state == GameState.MAP_EDITOR:
            self.reset_game()

        if new_state == GameState.GAME:
            self.sound_manager.stop_music()
            self.sound_manager.play_music("ambient")
            if self.current_state in [GameState.MAIN_MENU, GameState.GAME_OVER, GameState.STORY, None]:
                self.reset_game()

        if new_state == GameState.PAUSE:
            self.sound_manager.stop_music()
            self.last_frame = self.screen.copy()

        if new_state == GameState.STORY:
            self.sound_manager.stop_music()
            self.sound_manager.play_music("story_theme")
            self.story_file = kwargs.get('story_file', 'story.json')

        self.current_state = new_state

        if new_state == GameState.QUIT:
            self.running = False
            return

        if new_state not in self.screens:
            self.screens[new_state] = self.state_handlers[new_state](self)
        self.current_screen = self.screens[new_state]

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
