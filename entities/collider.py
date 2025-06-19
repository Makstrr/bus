import math
from typing import List, Tuple


class Collider:
    def __init__(self, center: Tuple[float, float], width: int, height: int, angle: float):
        self.center = center
        self.width = width
        self.height = height
        self.angle = angle  # В радианах

    def update(self, center: Tuple[float, float], angle: float) -> None:
        self.center = center
        self.angle = angle

    def check_intersections(self, colliders: List['Collider']) -> bool:
        for collider in colliders:
            if collider is self:
                continue
            if self._check_collision_with(collider):
                return True
        return False

    def _check_collision_with(self, other: 'Collider') -> bool:
        vertices_self = self.get_vertices()
        vertices_other = other.get_vertices()

        axes = self._get_axes() + other._get_axes()

        for axis in axes:
            min_self, max_self = self._project(vertices_self, axis)
            min_other, max_other = self._project(vertices_other, axis)
            if max_self < min_other or max_other < min_self:
                return False
        return True

    def get_vertices(self) -> List[List[float]]:
        half_w = self.width / 2
        half_h = self.height / 2
        corners = [
            (half_w, half_h),
            (-half_w, half_h),
            (-half_w, -half_h),
            (half_w, -half_h)
        ]
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)
        cx, cy = self.center
        vertices = []
        for x, y in corners:
            rot_x = x * cos_a - y * sin_a
            rot_y = x * sin_a + y * cos_a
            vertices.append([cx + rot_x, cy + rot_y])
        return vertices

    def _get_axes(self) -> List[List[float]]:
        return [
            [math.cos(self.angle), math.sin(self.angle)],
            [-math.sin(self.angle), math.cos(self.angle)]
        ]

    def _project(self, vertices: List[List[float]], axis: List[float]) -> tuple:
        min_proj = float('inf')
        max_proj = -float('inf')
        for x, y in vertices:
            proj = x * axis[0] + y * axis[1]
            min_proj = min(min_proj, proj)
            max_proj = max(max_proj, proj)
        return min_proj, max_proj
