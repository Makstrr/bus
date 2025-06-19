import numpy as np
from typing import Optional
import matplotlib.pyplot as plt


def generate_perlin_noise_2d(shape, scale):
    if scale == 0:
        scale = 0.0001

    # Вычисляем размер сетки градиентов
    grad_shape0 = int(np.ceil(shape[0] / scale)) + 2  # +2 для защиты от выхода за границы
    grad_shape1 = int(np.ceil(shape[1] / scale)) + 2

    # Генерация градиентов
    angles = 2 * np.pi * np.random.rand(grad_shape0, grad_shape1).astype(np.float32)
    gradients = np.dstack((np.cos(angles), np.sin(angles)))

    # Создаем координатную сетку
    x = np.arange(shape[0]) / scale
    y = np.arange(shape[1]) / scale
    X, Y = np.meshgrid(x, y, indexing='ij')

    # Целочисленные координаты
    x0 = np.floor(X).astype(int)
    y0 = np.floor(Y).astype(int)
    x1 = x0 + 1
    y1 = y0 + 1

    # Дробные части координат
    dx = X - x0
    dy = Y - y0

    # Получаем градиенты для всех точек одновременно
    v00 = gradients[x0, y0]
    v01 = gradients[x0, y1]
    v10 = gradients[x1, y0]
    v11 = gradients[x1, y1]

    # Скалярные произведения
    n00 = np.sum(v00 * np.dstack((dx, dy)), axis=2)
    n01 = np.sum(v01 * np.dstack((dx, dy - 1)), axis=2)
    n10 = np.sum(v10 * np.dstack((dx - 1, dy)), axis=2)
    n11 = np.sum(v11 * np.dstack((dx - 1, dy - 1)), axis=2)

    # Весовые коэффициенты
    sx = smoothstep(dx)
    sy = smoothstep(dy)

    # Интерполяция
    nx0 = lerp(n00, n10, sx)
    nx1 = lerp(n01, n11, sx)
    return lerp(nx0, nx1, sy)


def perlin_noise(shape, scale=10, octaves=6, persistence=0.5, lacunarity=2.0):
    """
    Генерация шума Перлина

    Параметры:
    shape - размер выходного массива (ширина, высота) или (ширина, высота, глубина)
    scale - масштаб шума (чем больше, тем более "крупнозернистый" шум)
    octaves - количество октав (увеличивает детализацию)
    persistence - влияние каждой последующей октавы (обычно 0-1)
    lacunarity - увеличение частоты с каждой октавой (обычно >1)

    Возвращает:
    Массив NumPy с нормализованными значениями шума (-1 до 1)
    """
    if not isinstance(shape, tuple) or len(shape) != 2:
        raise ValueError("Shape must be 2D tuple")

    # Инициализация массивов
    noise = np.zeros(shape)
    frequency = 1.0
    amplitude = 1.0

    for _ in range(octaves):
        amplitude * generate_perlin_noise_2d(shape, scale * frequency)

        # Увеличиваем частоту и уменьшаем амплитуду для следующей октавы
        frequency *= lacunarity
        amplitude *= persistence

    return noise


def smoothstep(t):
    """Функция сглаживания для интерполяции"""
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    """Линейная интерполяция"""
    return a + t * (b - a)


def generate_random_heightmap(width: int, height: int, persistence: Optional[float], lacunarity: Optional[float]):
    """Генерирует случайную карту высот"""

    scale = 1000
    octaves = 2

    world = perlin_noise((width, height), scale, octaves, persistence, lacunarity)

    # Масштабируем и сохраняем в uint16 для уменьшения размера итогового файла
    world_min = world.min()
    world_max = world.max()
    heightmap = ((world - world_min) / (world_max - world_min) * 65535
                 ).astype(np.uint16)

    plt.imshow(heightmap, cmap='terrain')
    plt.show()

    np.savez_compressed("../assets/heightmap.npz", heightmap)
