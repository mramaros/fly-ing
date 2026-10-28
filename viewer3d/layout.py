"""World layout: where each zone sits in the 3D scene."""

from __future__ import annotations

import math

from .gl_utils import Color
from .model import DroneMap, Zone

COLOR_NAMES: dict[str, Color] = {
    "red": (1.0, 0.23, 0.29), "green": (0.23, 1.0, 0.48),
    "blue": (0.24, 0.55, 1.0), "yellow": (1.0, 0.82, 0.4),
    "orange": (1.0, 0.6, 0.15), "gray": (0.6, 0.6, 0.7),
    "grey": (0.6, 0.6, 0.7), "purple": (0.7, 0.4, 1.0),
    "violet": (0.7, 0.4, 1.0), "cyan": (0.0, 0.9, 1.0),
    "pink": (1.0, 0.3, 0.7), "magenta": (1.0, 0.2, 0.8),
    "white": (1.0, 1.0, 1.0), "black": (0.2, 0.2, 0.28),
    "brown": (0.65, 0.42, 0.25), "lime": (0.6, 1.0, 0.2),
    "gold": (1.0, 0.84, 0.0), "maroon": (0.7, 0.12, 0.25),
    "crimson": (0.86, 0.08, 0.24), "teal": (0.0, 0.7, 0.7),
}
SLOT_X = 2.2
SLOT_Z = 1.4


def zone_color(zone: Zone) -> Color:
    """Return the neon colour used to draw a zone."""
    if zone.color and zone.color.lower() in COLOR_NAMES:
        return COLOR_NAMES[zone.color.lower()]
    defaults = {"start": (0.23, 1.0, 0.48), "end": (1.0, 0.23, 0.29)}
    return defaults.get(zone.kind, (0.0, 0.9, 1.0))


def grid_slots(count: int) -> list[tuple[float, float]]:
    """Offsets (x, z) of count drones parked on one pad."""
    cols = max(1, math.ceil(math.sqrt(count)))
    rows = max(1, math.ceil(count / cols))
    out = []
    for i in range(count):
        col, row = i % cols, i // cols
        out.append(((col - (cols - 1) / 2) * SLOT_X,
                    (row - (rows - 1) / 2) * SLOT_Z))
    return out


class Layout:
    """Compute pad radii and world positions from the map."""

    def __init__(self, drone_map: DroneMap) -> None:
        self.map = drone_map
        self.radius: dict[str, float] = {}
        for name, zone in drone_map.zones.items():
            cap = zone.max_drones
            if zone.kind != "hub":
                cap = drone_map.nb_drones
            self.radius[name] = self._pad_radius(cap)
        self.scale = self._spacing()
        xs = [z.x for z in drone_map.zones.values()] or [0]
        ys = [z.y for z in drone_map.zones.values()] or [0]
        x_lo, x_hi, y_lo, y_hi = min(xs), max(xs), min(ys), max(ys)
        self.grid: tuple[int, int, int, int] | None = None
        if drone_map.bounds is not None:
            bx, by = drone_map.bounds
            x_lo, x_hi = min(x_lo, 0), max(x_hi, bx)
            y_lo, y_hi = min(y_lo, 0), max(y_hi, by)
            self.grid = (x_lo, x_hi, y_lo, y_hi)
        self._cx, self._cy = (x_lo + x_hi) / 2, (y_lo + y_hi) / 2
        self.pos: dict[str, tuple[float, float]] = {
            n: self.to_world(z.x, z.y) for n, z in drone_map.zones.items()
        }
        margin = 4.0
        half_x = max((abs(self.pos[n][0]) + self.radius[n]
                      for n in self.pos), default=0.0)
        half_z = max((abs(self.pos[n][1]) + self.radius[n]
                      for n in self.pos), default=0.0)
        if self.grid is not None:
            half_x = max(half_x, (x_hi - x_lo) * self.scale / 2)
            half_z = max(half_z, (y_hi - y_lo) * self.scale / 2)
        self.half_x = max(half_x + margin, 8.0)
        self.half_z = max(half_z + margin, 8.0)

    def to_world(self, x: float, y: float) -> tuple[float, float]:
        """Convert map coordinates to world (x, z) coordinates."""
        return ((x - self._cx) * self.scale, -(y - self._cy) * self.scale)

    def _spacing(self) -> float:
        """World units per map unit so linked pads never overlap."""
        zones = self.map.zones
        need = 8.0
        for link in self.map.links:
            za, zb = zones[link.a], zones[link.b]
            gap = math.hypot(za.x - zb.x, za.y - zb.y) or 1.0
            reach = self.radius[link.a] + self.radius[link.b] + 3.0
            need = max(need, reach / gap)
        return need

    @property
    def camera_distance(self) -> float:
        """Default orbit distance of the camera."""
        return max(30.0, max(self.half_x, self.half_z) * 1.7 + 6.0)

    @staticmethod
    def _pad_radius(capacity: int) -> float:
        cols = max(1, math.ceil(math.sqrt(capacity)))
        rows = max(1, math.ceil(capacity / cols))
        reach = math.hypot((cols - 1) / 2 * SLOT_X + 0.95,
                           (rows - 1) / 2 * SLOT_Z + 0.35)
        return max(2.4, reach + 0.4)
