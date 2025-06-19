import pygame
from system_modules.game_state import GameState
from entities.objects.game_object import GameObject, Stop, RadioactiveZone, GasStation
import pygame_gui
import numpy as np
import json
import math
import os
from enum import Enum, auto
from system_modules.config import Config


class EditorMode(Enum):
    TERRAIN = auto()
    OBJECTS = auto()
    NAVIGATION = auto()


class TerrainTool(Enum):
    RAISE = auto()
    LOWER = auto()
    SMOOTH = auto()
    FLATTEN = auto()
    NOISE = auto()


class ObjectType(Enum):
    TREE = "tree"
    ROCK = "rock"
    STOP = "stop"


class MapEditor:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.width = game.game_map.width
        self.height = game.game_map.height
        self.heightmap = game.game_map.heightmap.copy()
        self.max_height = self.heightmap.max()
        self.objects = game.game_map.objects.copy()

        # Настройки редактора
        self.mode = EditorMode.TERRAIN
        self.terrain_tool = TerrainTool.RAISE
        self.object_type = ObjectType.TREE
        self.brush_size = 30
        self.brush_intensity = 1.0
        self.selected_object = None

        # Настройки камеры
        self.camera_x = 0
        self.camera_y = 0
        self.camera_speed = 5
        self.zoom = 1.0
        self.min_zoom = 0.5
        self.max_zoom = 3.0

        # Создание UI
        self.gui_manager = pygame_gui.UIManager((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        self._create_ui()

        # Создание мини-карты
        self.minimap_size = 200
        self.minimap_surface = pygame.Surface((self.minimap_size, self.minimap_size))

        # Создание превью объектов
        self.object_previews = self._create_object_previews()

        # Состояние редактора
        self.dragging = False
        self.start_drag = (0, 0)
        self.show_minimap = True
        self.show_help = False

    def _create_ui(self):
        # Панель инструментов
        panel_rect = pygame.Rect(10, 10, 250, Config.SCREEN_HEIGHT - 20)
        self.panel = pygame_gui.elements.UIPanel(
            relative_rect=panel_rect,
            manager=self.gui_manager
        )

        # Кнопки режимов
        y_pos = 10
        self.mode_buttons = []
        for mode in EditorMode:
            btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(10, y_pos, 230, 40),
                text=mode.name.capitalize(),
                manager=self.gui_manager,
                container=self.panel
            )
            self.mode_buttons.append(btn)
            y_pos += 45

        # Разделитель
        y_pos += 10
        y_pos1 = y_pos  # Сохранение позиции

        self.tool_buttons = []
        for tool in TerrainTool:
            btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(10, y_pos, 230, 30),
                text=tool.name.capitalize(),
                manager=self.gui_manager,
                container=self.panel
            )
            self.tool_buttons.append(btn)
            y_pos += 30

        # Слайдер размера кисти
        self.brush_size_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_pos, 230, 30),
            text=f"Brush Size: {self.brush_size}",
            manager=self.gui_manager,
            container=self.panel
        )
        y_pos += 30

        self.brush_size_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(10, y_pos, 230, 30),
            start_value=self.brush_size,
            value_range=(5, 100),
            manager=self.gui_manager,
            container=self.panel
        )
        y_pos += 30

        # Слайдер интенсивности
        self.intensity_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_pos, 230, 30),
            text=f"Intensity: {self.brush_intensity:.1f}",
            manager=self.gui_manager,
            container=self.panel
        )
        y_pos += 30

        self.intensity_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(10, y_pos, 230, 30),
            start_value=self.brush_intensity,
            value_range=(0.1, 5.0),
            manager=self.gui_manager,
            container=self.panel
        )
        y_pos += 20

        # Настройки для режима OBJECTS
        self.object_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, y_pos, 230, 30),
            text="Objects",
            manager=self.gui_manager,
            container=self.panel
        )
        y_pos += 35
        y_pos2 = y_pos  # Сохранение позиции

        self.object_buttons = []
        y_pos = y_pos1
        for obj_type in ObjectType:
            btn = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(10, y_pos, 230, 30),
                text=obj_type.name.capitalize(),
                manager=self.gui_manager,
                container=self.panel
            )
            self.object_buttons.append(btn)
            y_pos += 35


        # Кнопки управления
        y_pos = y_pos2
        self.save_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, y_pos, 110, 40),
            text="Save",
            manager=self.gui_manager,
            container=self.panel
        )

        self.load_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(130, y_pos, 110, 40),
            text="Load",
            manager=self.gui_manager,
            container=self.panel
        )
        y_pos += 50

        self.exit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(10, y_pos, 230, 40),
            text="Exit Editor",
            manager=self.gui_manager,
            container=self.panel
        )

        # Скрыть объектные элементы по умолчанию
        self._update_ui_visibility()

    def _create_object_previews(self):
        """Создает превью объектов для панели инструментов"""
        previews = {}
        size = (80, 80)

        # Дерево
        tree = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(tree, (0, 100, 0), (30, 10, 20, 60))
        pygame.draw.circle(tree, (0, 150, 0), (40, 20), 25)
        previews[ObjectType.TREE] = tree

        # Камень
        rock = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.ellipse(rock, (100, 100, 100), (20, 20, 40, 40))
        pygame.draw.ellipse(rock, (80, 80, 80), (25, 15, 30, 30))
        previews[ObjectType.ROCK] = rock

        # Остановка
        stop = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(stop, (150, 150, 150), (20, 20, 40, 40))
        pygame.draw.rect(stop, (200, 200, 0), (25, 25, 30, 30))
        pygame.draw.line(stop, (0, 0, 0), (20, 40), (60, 40), 3)
        previews[ObjectType.STOP] = stop

        return previews

    def _update_ui_visibility(self):
        """Обновляет видимость элементов UI в зависимости от режима"""
        # Показать/скрыть инструменты рельефа
        for tool in self.tool_buttons:
            tool.visible = (self.mode == EditorMode.TERRAIN)
        self.brush_size_label.visible = (self.mode == EditorMode.TERRAIN)
        self.brush_size_slider.visible = (self.mode == EditorMode.TERRAIN)
        self.intensity_label.visible = (self.mode == EditorMode.TERRAIN)
        self.intensity_slider.visible = (self.mode == EditorMode.TERRAIN)

        # Показать/скрыть инструменты объектов
        for obj_btn in self.object_buttons:
            obj_btn.visible = (self.mode == EditorMode.OBJECTS)
        self.object_label.visible = (self.mode == EditorMode.OBJECTS)

        # Обновить текст кнопок режимов
        for i, btn in enumerate(self.mode_buttons):
            btn.text = EditorMode(i + 1).name.capitalize()
            if self.mode == EditorMode(i + 1):
                btn.colours['normal_bg'] = pygame.Color(100, 150, 200)
                btn.colours['hovered_bg'] = pygame.Color(80, 130, 180)
                btn.colours['active_bg'] = pygame.Color(60, 110, 160)
            else:
                btn.colours['normal_bg'] = pygame.Color(70, 70, 70)
                btn.colours['hovered_bg'] = pygame.Color(90, 90, 90)
                btn.colours['active_bg'] = pygame.Color(50, 50, 50)
            btn.rebuild()

        # Обновить кнопки инструментов
        if self.mode == EditorMode.TERRAIN:
            for i, btn in enumerate(self.tool_buttons):
                if self.terrain_tool == TerrainTool(i + 1):
                    btn.colours['normal_bg'] = pygame.Color(120, 180, 120)
                    btn.colours['hovered_bg'] = pygame.Color(100, 160, 100)
                    btn.colours['active_bg'] = pygame.Color(80, 140, 80)
                else:
                    btn.colours['normal_bg'] = pygame.Color(70, 70, 70)
                    btn.colours['hovered_bg'] = pygame.Color(90, 90, 90)
                    btn.colours['active_bg'] = pygame.Color(50, 50, 50)
                btn.rebuild()

        # Обновить кнопки объектов
        if self.mode == EditorMode.OBJECTS:
            object_types = list(ObjectType)  # Получаем все значения перечисления в виде списка
            for i, btn in enumerate(self.object_buttons):
                if self.object_type == object_types[i]:  # Сравниваем с элементом перечисления по индексу
                    btn.colours['normal_bg'] = pygame.Color(180, 120, 120)
                    btn.colours['hovered_bg'] = pygame.Color(160, 100, 100)
                    btn.colours['active_bg'] = pygame.Color(140, 80, 80)
                else:
                    btn.colours['normal_bg'] = pygame.Color(70, 70, 70)
                    btn.colours['hovered_bg'] = pygame.Color(90, 90, 90)
                    btn.colours['active_bg'] = pygame.Color(50, 50, 50)
                btn.rebuild()

    def handle_events(self, event):
        self.gui_manager.process_events(event)
        keys = pygame.key.get_pressed()

        if event.type == pygame.KEYDOWN:
            # Управление камерой
            if keys[pygame.K_w]:
                self.camera_y += self.camera_speed * 5
            elif keys[pygame.K_s]:
                self.camera_y -= self.camera_speed * 5
            elif keys[pygame.K_a]:
                self.camera_x += self.camera_speed * 5
            elif keys[pygame.K_d]:
                self.camera_x -= self.camera_speed * 5
            elif keys[pygame.K_EQUALS] or keys[pygame.K_PLUS]:
                self.zoom = min(self.max_zoom, self.zoom + 0.1)
            elif keys[pygame.K_MINUS]:
                self.zoom = max(self.min_zoom, self.zoom - 0.1)
            elif event.key == pygame.K_h:
                self.show_help = not self.show_help
            elif event.key == pygame.K_ESCAPE:
                self.exit_editor()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Левая кнопка мыши
                mouse_x, mouse_y = pygame.mouse.get_pos()

                # Проверить, не нажата ли UI панель
                if not self.panel.rect.collidepoint(mouse_x, mouse_y):
                    if self.mode == EditorMode.TERRAIN:
                        self.dragging = True
                        self.start_drag = (mouse_x, mouse_y)
                        self.apply_terrain_tool(mouse_x, mouse_y)
                    elif self.mode == EditorMode.OBJECTS and self.selected_object:
                        world_x, world_y = self.screen_to_world(mouse_x, mouse_y)
                        self.selected_object.rect.center = (world_x, world_y)
                    elif self.mode == EditorMode.OBJECTS:
                        self.add_object(mouse_x, mouse_y)
                    elif self.mode == EditorMode.NAVIGATION:
                        self.start_drag = (mouse_x, mouse_y)
                        self.dragging = True

            elif event.button == 3:  # Правая кнопка мыши
                if self.mode == EditorMode.OBJECTS:
                    self.select_object(pygame.mouse.get_pos())
                elif self.mode == EditorMode.NAVIGATION:
                    self.zoom_to_point(pygame.mouse.get_pos(), 1.1)

            elif event.button == 4:  # Колесико вверх
                self.zoom_to_point(pygame.mouse.get_pos(), 1.1)

            elif event.button == 5:  # Колесико вниз
                self.zoom_to_point(pygame.mouse.get_pos(), 0.9)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
                self.selected_object = None

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                if self.mode == EditorMode.TERRAIN:
                    self.apply_terrain_tool(*pygame.mouse.get_pos())
                elif self.mode == EditorMode.NAVIGATION:
                    dx = event.rel[0]
                    dy = event.rel[1]
                    self.camera_x += dx / self.zoom
                    self.camera_y += dy / self.zoom

        elif event.type == pygame_gui.UI_BUTTON_PRESSED:
            # Обработка кнопок режимов
            if event.ui_element in self.mode_buttons:
                self.mode = EditorMode(self.mode_buttons.index(event.ui_element) + 1)
                self._update_ui_visibility()

            # Обработка инструментов рельефа
            elif event.ui_element in self.tool_buttons:
                self.terrain_tool = TerrainTool(self.tool_buttons.index(event.ui_element) + 1)
                self._update_ui_visibility()

            # Обработка выбора объектов
            elif event.ui_element in self.object_buttons:
                index = self.object_buttons.index(event.ui_element)
                object_types = list(ObjectType)
                if index < len(object_types):
                    self.object_type = object_types[index]
                self._update_ui_visibility()

            # Другие кнопки
            elif event.ui_element == self.save_button:
                self.save_map()
            elif event.ui_element == self.load_button:
                self.load_map()
            elif event.ui_element == self.exit_button:
                self.exit_editor()

        elif event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            if event.ui_element == self.brush_size_slider:
                self.brush_size = int(event.value)
                self.brush_size_label.text = f"Brush Size: {self.brush_size}"
                self.brush_size_label.rebuild()
            elif event.ui_element == self.intensity_slider:
                self.brush_intensity = event.value
                self.intensity_label.text = f"Intensity: {self.brush_intensity:.1f}"
                self.intensity_label.rebuild()

    def screen_to_world(self, screen_x, screen_y):
        """Преобразует экранные координаты в мировые"""
        world_x = (screen_x - self.camera_x) / self.zoom
        world_y = (screen_y - self.camera_y) / self.zoom
        return world_x, world_y

    def world_to_screen(self, world_x, world_y):
        """Преобразует мировые координаты в экранные"""
        screen_x = world_x * self.zoom + self.camera_x
        screen_y = world_y * self.zoom + self.camera_y
        return screen_x, screen_y

    def zoom_to_point(self, screen_point, factor):
        """Увеличивает/уменьшает масштаб с центром в указанной точке"""
        world_x, world_y = self.screen_to_world(*screen_point)
        self.zoom *= factor
        self.zoom = max(self.min_zoom, min(self.max_zoom, self.zoom))
        new_screen_x, new_screen_y = self.world_to_screen(world_x, world_y)
        self.camera_x += screen_point[0] - new_screen_x
        self.camera_y += screen_point[1] - new_screen_y

    def apply_terrain_tool(self, screen_x, screen_y):
        """Применяет текущий инструмент к карте высот"""
        world_x, world_y = self.screen_to_world(screen_x, screen_y)

        # Определяем область влияния кисти
        brush_radius = self.brush_size / self.zoom
        left = max(0, int(world_x - brush_radius))
        right = min(self.width, int(world_x + brush_radius))
        top = max(0, int(world_y - brush_radius))
        bottom = min(self.height, int(world_y + brush_radius))

        # Применяем инструмент к каждому пикселю в области
        for y in range(top, bottom):
            for x in range(left, right):
                # Рассчитываем расстояние до центра кисти
                distance = math.sqrt((x - world_x) ** 2 + (y - world_y) ** 2)

                if distance <= brush_radius:
                    # Рассчитываем силу влияния (1 в центре, 0 на краю)
                    strength = (1 - distance / brush_radius) * self.brush_intensity

                    # Применяем выбранный инструмент
                    if self.terrain_tool == TerrainTool.RAISE:
                        self.heightmap[x, y] = min(self.heightmap[x, y] + strength * 1000, 65535)
                    elif self.terrain_tool == TerrainTool.LOWER:
                        self.heightmap[x, y] = max(self.heightmap[x, y] - strength * 1000, 0)
                    elif self.terrain_tool == TerrainTool.SMOOTH:
                        # Усредняем высоту с соседями
                        neighbors = []
                        for dy in range(-1, 2):
                            for dx in range(-1, 2):
                                nx, ny = x + dx, y + dy
                                if 0 <= nx < self.width and 0 <= ny < self.height:
                                    neighbors.append(self.heightmap[nx, ny])

                        if neighbors:
                            avg = sum(neighbors) / len(neighbors)
                            self.heightmap[x, y] += (avg - self.heightmap[x, y]) * strength
                    elif self.terrain_tool == TerrainTool.FLATTEN:
                        # Приводим к высоте центра кисти
                        target = self.heightmap[int(world_x), int(world_y)]
                        self.heightmap[x, y] += (target - self.heightmap[x, y]) * strength
                    elif self.terrain_tool == TerrainTool.NOISE:
                        # Добавляем шум
                        noise = (np.random.random() - 0.5) * 2 * strength
                        self.heightmap[x, y] += noise

    def add_object(self, screen_x, screen_y):
        """Добавляет объект на карту"""
        if self.panel.rect.collidepoint(screen_x, screen_y):
            return  # Не добавлять объекты на панель UI

        world_x, world_y = self.screen_to_world(screen_x, screen_y)

        # Создаем объект в зависимости от выбранного типа
        if self.object_type == ObjectType.TREE:
            from entities.objects.game_object import GameObject
            new_obj = GameObject(world_x, world_y, "tree", 1)
        elif self.object_type == ObjectType.ROCK:
            from entities.objects.game_object import GameObject
            new_obj = GameObject(world_x, world_y, "rock", 1)
        elif self.object_type == ObjectType.STOP:
            from entities.objects.game_object import Stop
            new_obj = Stop(world_x, world_y, "stop")

        self.objects.append(new_obj)
        self.selected_object = new_obj

    def select_object(self, screen_pos):
        """Выбирает объект по клику"""
        world_x, world_y = self.screen_to_world(*screen_pos)

        # Ищем ближайший объект
        closest = None
        min_dist = float('inf')

        for obj in self.objects:
            dist = math.hypot(obj.rect.centerx - world_x, obj.rect.centery - world_y)
            if dist < min_dist and dist < 50:  # Максимальное расстояние для выбора
                min_dist = dist
                closest = obj

        self.selected_object = closest

    def draw(self):
        """Отрисовывает карту и интерфейс редактора"""
        self.screen.fill(Config.BLACK)

        # Отрисовка карты высот
        self.draw_terrain()

        # Отрисовка объектов
        self.draw_objects()

        # Отрисовка UI
        self.gui_manager.draw_ui(self.screen)

        # Отрисовка курсора
        self.draw_cursor()

        # Отрисовка выбранного объекта
        if self.selected_object:
            self.draw_selected_object()

        # Отрисовка справки
        if self.show_help:
            self.draw_help()

    def get_elevation(self, x: float, y: float) -> float:
        return self.heightmap[int(max(0, min(x, self.width-1))), int(max(0, min(y, self.height-1)))] / self.max_height

    def draw_terrain(self):
        """Отрисовывает карту высот"""
        # Рассчитываем видимую область в мировых координатах
        min_x = max(0, int((-self.camera_x) / self.zoom))
        max_x = min(self.width, int((Config.SCREEN_WIDTH - self.camera_x) / self.zoom) + 1)
        min_y = max(0, int((-self.camera_y) / self.zoom))
        max_y = min(self.height, int((Config.SCREEN_HEIGHT - self.camera_y) / self.zoom) + 1)

        # Используем фиксированный шаг 10 в мировых координатах
        for x in range(int(min_x), int(max_x), 10):
            for y in range(int(min_y), int(max_y), 10):
                height = self.get_elevation(x, y)
                color = (int(240 * height), int(230 * height), int(140 * height))

                # Рассчитываем экранные координаты и размер
                screen_x = x * self.zoom + self.camera_x
                screen_y = y * self.zoom + self.camera_y
                tile_size = int(10 * self.zoom)

                pygame.draw.rect(
                    self.screen,
                    color,
                    (screen_x, screen_y, tile_size, tile_size)
                )

    def draw_objects(self):
        """Отрисовывает объекты на карте"""
        for obj in self.objects:
            # Преобразуем мировые координаты в экранные
            screen_x = int(obj.rect.centerx * self.zoom + self.camera_x)
            screen_y = int(obj.rect.centery * self.zoom + self.camera_y)

            # Масштабируем спрайт
            scaled_size = (int(obj.image.get_width() * self.zoom),
                           int(obj.image.get_height() * self.zoom))
            if scaled_size[0] > 0 and scaled_size[1] > 0:
                scaled_img = pygame.transform.scale(obj.image, scaled_size)
                self.screen.blit(scaled_img,
                                 (screen_x - scaled_size[0] // 2,
                                  screen_y - scaled_size[1] // 2))

    def draw_cursor(self):
        """Отрисовывает курсор в зависимости от режима"""
        mouse_x, mouse_y = pygame.mouse.get_pos()

        if self.mode == EditorMode.TERRAIN:
            # Рисуем круг для кисти
            radius = int(self.brush_size * self.zoom)
            pygame.draw.circle(self.screen, (255, 255, 255), (mouse_x, mouse_y), radius, 2)

            # Текст с размером кисти
            font = pygame.font.SysFont(None, 24)
            text = font.render(f"Size: {self.brush_size}", True, (255, 255, 255))
            self.screen.blit(text, (mouse_x + radius + 10, mouse_y - 10))

        elif self.mode == EditorMode.OBJECTS and not self.selected_object:
            # Рисуем превью объекта
            preview = self.object_previews[self.object_type]
            scaled = pygame.transform.scale(preview,
                                            (int(preview.get_width() * self.zoom),
                                             (int(preview.get_height() * self.zoom))))
            self.screen.blit(scaled, (mouse_x, mouse_y))

    def draw_selected_object(self):
        """Выделяет выбранный объект"""
        # Преобразуем мировые координаты в экранные
        screen_x = int(self.selected_object.rect.centerx * self.zoom + self.camera_x)
        screen_y = int(self.selected_object.rect.centery * self.zoom + self.camera_y)

        # Рисуем рамку вокруг объекта
        scaled_width = int(self.selected_object.rect.width * self.zoom)
        scaled_height = int(self.selected_object.rect.height * self.zoom)

        pygame.draw.rect(self.screen, (255, 255, 0),
                         (screen_x - scaled_width // 2,
                          screen_y - scaled_height // 2,
                          scaled_width, scaled_height), 2)

    def draw_help(self):
        """Отображает справку по управлению"""
        help_text = [
            "Map Editor Controls:",
            "WASD - Move camera",
            "Mouse Wheel, +/- - Zoom",
            "Left Click - Apply tool / Add object",
            "Right Click - Select object",
            "H - Toggle help",
            "ESC - Exit editor",
            "",
            "Terrain Tools:",
            "Raise - Increase height",
            "Lower - Decrease height",
            "Smooth - Average height with neighbors",
            "Flatten - Set to center height",
            "Noise - Add random noise",
        ]

        # Создаем полупрозрачный фон
        overlay = pygame.Surface((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        # Отрисовываем текст
        font = pygame.font.SysFont(None, 30)
        y_pos = 50

        for line in help_text:
            text_surf = font.render(line, True, (255, 255, 255))
            self.screen.blit(text_surf, (Config.SCREEN_WIDTH // 2 - text_surf.get_width() // 2, y_pos))
            y_pos += 35

    def save_map(self):
        """Сохраняет карту высот и объекты в файлы"""
        # Сохраняем карту высот
        np.savez_compressed("./assets/heightmap.npz", self.heightmap)

        # Сохраняем объекты
        objects_data = []
        for obj in self.objects:
            obj_data = {
                'x': obj.rect.centerx,
                'y': obj.rect.centery,
                'type': obj.type,
                'z_order': obj.z_order
            }

            # Специальные данные для определенных объектов
            if isinstance(obj, Stop):
                obj_data['name'] = obj.name
                obj_data['capacity'] = obj.capacity
            elif isinstance(obj, RadioactiveZone):
                obj_data['radius'] = obj.radius
                obj_data['intensity'] = obj.intensity
            elif isinstance(obj, GasStation):
                obj_data['fuel_capacity'] = obj.fuel_capacity

            objects_data.append(obj_data)

        with open("./assets/map.json", "w") as f:
            json.dump(objects_data, f, indent=2)

        print("Map saved successfully!")

    def load_map(self):
        """Загружает карту высот и объекты из файлов"""
        # Загружаем карту высот
        if os.path.exists("./assets/heightmap.npz"):
            self.heightmap = np.load("./assets/heightmap.npz")['arr_0']

        # Загружаем объекты
        if os.path.exists("./assets/map.json"):
            self.objects = []
            with open("./assets/map.json", "r") as f:
                objects_data = json.load(f)

            for obj_data in objects_data:

                if obj_data['type'] == "stop":
                    self.objects.append(Stop(
                        obj_data['x'], obj_data['y'],
                        obj_data.get('name'),
                        obj_data.get('capacity', 20)
                    ))
                elif obj_data['type'] == "radioactive_zone":
                    self.objects.append(RadioactiveZone(
                        obj_data['x'], obj_data['y'],
                        obj_data.get('radius'),
                        obj_data.get('intensity')
                    ))
                elif obj_data['type'] == "gas_station":
                    self.objects.append(GasStation(
                        obj_data['x'], obj_data['y'],
                        obj_data.get('fuel_capacity', 5000)
                    ))
                else:
                    self.objects.append(GameObject(
                        obj_data['x'], obj_data['y'], obj_data['type'], obj_data.get('z_order', 0)
                    ))

        print("Map loaded successfully!")

    def exit_editor(self):
        """Выходит из редактора и возвращается в меню"""
        # Обновляем карту в игре
        self.save_map()

        # Возвращаемся в меню
        self.game.change_state(GameState.MAIN_MENU)

    def update(self, dt):
        """Обновляет состояние редактора"""
        self.gui_manager.update(dt)
