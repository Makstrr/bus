import pygame
import json
from screens.base_screen import BaseScreen
from game_state import GameState
from config import Config


class StoryScreen(BaseScreen):
    def __init__(self, game):
        super().__init__(game)
        self.story_data = self._load_story_data()
        self.current_slide = 0
        self.background = None
        self.character_img = None
        self.text = ""
        self.character_position = "left"
        self.text_surface = None
        self.text_rect = None
        self._load_current_slide()

    def _load_story_data(self):
        try:
            with open("assets/story/story.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print("Файл сюжета не найден!")
            return {
                "slides": [{"background": None, "character": None, "text": "Сюжет поврежден", "position": "center"}]
            }

    def _load_current_slide(self):
        if self.current_slide < len(self.story_data["slides"]):
            slide = self.story_data["slides"][self.current_slide]

            # Загрузка фона
            if slide["background"]:
                try:
                    self.background = pygame.image.load(slide["background"]).convert()
                    self.background = pygame.transform.scale(
                        self.background,
                        (Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
                except:
                    self.background = None

            # Загрузка персонажа
            if slide["character"]:
                try:
                    self.character_img = pygame.image.load(slide["character"]).convert_alpha()
                    # Масштабируем изображение персонажа
                    scale_factor = 0.7
                    orig_width, orig_height = self.character_img.get_size()
                    new_height = int(Config.SCREEN_HEIGHT * scale_factor)
                    new_width = int(orig_width * new_height / orig_height)
                    self.character_img = pygame.transform.scale(
                        self.character_img,
                        (new_width, new_height)
                    )
                except:
                    self.character_img = None
            else:
                self.character_img = None

            self.text = slide["text"]
            self.character_position = slide["position"]

            # Создаем поверхность для текста
            self._create_text_surface()

    def _create_text_surface(self):
        # Рассчитываем размеры текстового блока
        max_width = Config.SCREEN_WIDTH
        font = pygame.font.SysFont('Monospace Regular', 28)

        # Разбиваем текст на строки
        words = self.text.split(' ')
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] <= max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        # Создаем поверхность для текста
        line_height = font.get_linesize()
        text_height = max(len(lines) * line_height + 20, 100)
        self.text_surface = pygame.Surface((max_width, text_height), pygame.SRCALPHA)
        self.text_surface.fill((0, 0, 0, 255))  # Полупрозрачный черный фон

        # Рендерим текст
        for i, line in enumerate(lines):
            text_render = font.render(line, True, Config.WHITE)
            self.text_surface.blit(text_render, (10, 10 + i * line_height))

        self.text_rect = self.text_surface.get_rect(
            center=(Config.SCREEN_WIDTH // 2,
                    Config.SCREEN_HEIGHT - text_height // 2)
        )

    def handle_events(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_RIGHT):
                self.current_slide += 1
                if self.current_slide < len(self.story_data["slides"]):
                    self._load_current_slide()
                else:
                    self.game.change_state(GameState.GAME)
            elif event.key == pygame.K_LEFT and self.current_slide > 0:
                self.current_slide -= 1
                self._load_current_slide()
            elif event.key == pygame.K_SPACE:
                self.game.change_state(GameState.GAME)

        if event.type == pygame.MOUSEBUTTONDOWN:
            self.current_slide += 1
            if self.current_slide < len(self.story_data["slides"]):
                self._load_current_slide()
            else:
                self.game.change_state(GameState.GAME)

    def render(self) -> None:
        # Отрисовка фона
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(Config.BLACK)

        # Отрисовка персонажа
        if self.character_img:
            char_rect = self.character_img.get_rect()

            if self.character_position == "left":
                char_rect.midleft = (50, Config.SCREEN_HEIGHT // 2)
            elif self.character_position == "right":
                char_rect.midright = (Config.SCREEN_WIDTH - 50, Config.SCREEN_HEIGHT // 2)
            else:  # center
                char_rect.center = (Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT // 2)

            self.screen.blit(self.character_img, char_rect)

        # Отрисовка текста
        if self.text_surface:
            self.screen.blit(self.text_surface, self.text_rect)

        # Индикатор прогресса
        progress = f"{self.current_slide + 1}/{len(self.story_data['slides'])}"
        progress_text = self.font.render(progress, True, Config.WHITE)
        progress_rect = progress_text.get_rect(bottomright=(Config.SCREEN_WIDTH - 20, Config.SCREEN_HEIGHT - 20))
        self.screen.blit(progress_text, progress_rect)

        # Подсказка управления
        hint = self.font.render("ЛКМ, ВПРАВО, ВВОД - дальше, ПРОБЕЛ - пропустить сюжет", True, Config.YELLOW)
        hint_rect = hint.get_rect(center=(Config.SCREEN_WIDTH // 2, 20))
        self.screen.blit(hint, hint_rect)

    def on_exit(self) -> None:
        # Освобождаем ресурсы
        self.background = None
        self.character_img = None
        self.text_surface = None