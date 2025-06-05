import numpy as np
from PIL import Image
from itertools import product
import matplotlib.pyplot as plt


def generate_perlin_noise_2d(shape, scale):
    if scale == 0:
        scale = 0.0001

    # Генерация случайных градиентов (исправленная версия)
    angles = 2 * np.pi * np.random.rand(int(np.ceil(shape[0] / scale)) + 1,
                                        int(np.ceil(shape[1] / scale)) + 1)
    gradients = np.dstack((np.cos(angles), np.sin(angles)))

    noise = np.zeros(shape)

    for i, j in product(*[range(s) for s in shape]):
        x = i / scale
        y = j / scale
        x0, y0 = int(x), int(y)
        x1, y1 = x0 + 1, y0 + 1

        dx, dy = x - x0, y - y0

        # Корректное получение градиентов
        try:
            v00 = gradients[x0, y0]
            v01 = gradients[x0, y1]
            v10 = gradients[x1, y0]
            v11 = gradients[x1, y1]
        except IndexError:
            continue

        n00 = np.dot(v00, [dx, dy])
        n01 = np.dot(v01, [dx, dy - 1])
        n10 = np.dot(v10, [dx - 1, dy])
        n11 = np.dot(v11, [dx - 1, dy - 1])

        sx = smoothstep(dx)
        sy = smoothstep(dy)

        nx0 = lerp(n00, n10, sx)
        nx1 = lerp(n01, n11, sx)
        noise[i, j] = lerp(nx0, nx1, sy)

    return noise


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
    heightmap = (world - np.min(world)) / (np.max(world) - np.min(world)) * 100
    plt.imshow(heightmap)
    plt.show()
    np.save("assets/heightmap.npy", heightmap)


# heightmap = perlin_noise((2000, 3000), scale=90, octaves=1)
# # print(heightmap)
# heightmap = ((heightmap - heightmap.min()) / (heightmap.max() - heightmap.min()) * 255).astype(np.uint8)
# # heightmap = heightmap.astype(np.uint8)
# Image.fromarray(heightmap).save('assets/heightmap.png')
generate_random_heightmap(width=4000, height=5000)

# def generate_perlin_noise(width, height, scale=0.1):
#     noise = np.zeros((width, height))
#     for i in range(width):
#         for j in range(height):
#             noise[i][j] = pnoise2(i*scale, j*scale, octaves=6)
#     return (noise - noise.min()) / (noise.max() - noise.min())


