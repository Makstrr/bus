import numpy as np
from PIL import Image
from itertools import product
import matplotlib.pyplot as plt


def generate_perlin_noise_2d(shape, scale):
    if scale == 0:
        scale = 0.0001

    # Вычисляем размер сетки градиентов
    grad_shape0 = int(np.ceil(shape[0] / scale)) + 2  # +2 для защиты от выхода за границы
    grad_shape1 = int(np.ceil(shape[1] / scale)) + 2

    # Генерация градиентов с float32 для экономии памяти
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


def generate_perlin_noise_3d(shape, scale):
    """
    Генерация базового 3D шума Перлина (упрощенная версия)
    """
    if scale == 0:
        scale = 0.0001

    # Генерация случайных градиентов
    gradients = np.random.randn(int(np.ceil(shape[0] / scale) + 1,
                                    int(np.ceil(shape[1] / scale) + 1,
                                        int(np.ceil(shape[2] / scale) + 1, 3))))
    gradients /= np.linalg.norm(gradients, axis=3, keepdims=True)

    noise = np.zeros(shape)

    for i, j, k in product(*[range(s) for s in shape]):
    # Позиция в сетке градиентов
        x = i / scale
    y = j / scale
    z = k / scale
    x0, y0, z0 = int(x), int(y), int(z)
    x1, y1, z1 = x0 + 1, y0 + 1, z0 + 1

    # Дробные части
    dx, dy, dz = x - x0, y - y0, z - z0

    # Вектора от углов к точке
    v000 = gradients[x0, y0, z0]
    v001 = gradients[x0, y0, z1]
    v010 = gradients[x0, y1, z0]
    v011 = gradients[x0, y1, z1]
    v100 = gradients[x1, y0, z0]
    v101 = gradients[x1, y0, z1]
    v110 = gradients[x1, y1, z0]
    v111 = gradients[x1, y1, z1]

    # Скалярные произведения
    n000 = np.dot(v000, [dx, dy, dz])
    n001 = np.dot(v001, [dx, dy, dz - 1])
    n010 = np.dot(v010, [dx, dy - 1, dz])
    n011 = np.dot(v011, [dx, dy - 1, dz - 1])
    n100 = np.dot(v100, [dx - 1, dy, dz])
    n101 = np.dot(v101, [dx - 1, dy, dz - 1])
    n110 = np.dot(v110, [dx - 1, dy - 1, dz])
    n111 = np.dot(v111, [dx - 1, dy - 1, dz - 1])

    # Веса для интерполяции
    sx = smoothstep(dx)
    sy = smoothstep(dy)
    sz = smoothstep(dz)

    # Интерполяция
    nx00 = lerp(n000, n100, sx)
    nx01 = lerp(n001, n101, sx)
    nx10 = lerp(n010, n110, sx)
    nx11 = lerp(n011, n111, sx)

    nxy0 = lerp(nx00, nx10, sy)
    nxy1 = lerp(nx01, nx11, sy)

    noise[i, j, k] = lerp(nxy0, nxy1, sz)

    return noise


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
    if not isinstance(shape, tuple) or len(shape) not in (2, 3):
        raise ValueError("Shape must be 2D or 3D tuple")

    # Инициализация массивов
    noise = np.zeros(shape)
    frequency = 1.0
    amplitude = 1.0

    for _ in range(octaves):
        # Генерируем шум для текущей октавы
        noise += amplitude * generate_perlin_noise_3d(shape, scale * frequency) if len(shape) == 3 \
            else amplitude * generate_perlin_noise_2d(shape, scale * frequency)

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


def generate_random_heightmap(width: int, height: int):
    """Генерирует случайную карту высот (пример)"""
    # Используем шум Перлина для реалистичности

    scale = 1000
    octaves = 2
    persistence = 0.5
    lacunarity = 2.0

    world = perlin_noise((width, height), scale, octaves)

    # Масштабируем и сохраняем
    world_min = world.min()
    world_max = world.max()
    heightmap = ((world - world_min) / (world_max - world_min) * 65535
                 ).astype(np.uint16)

    plt.imshow(heightmap, cmap='terrain')
    plt.show()

    np.savez_compressed("assets/heightmap.npz", heightmap)


generate_random_heightmap(width=4000, height=5000)
