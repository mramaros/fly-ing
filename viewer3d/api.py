"""Programmatic API: build the 3D scene point by point.

Typical use::

    import viewer3d

    viewer3d.init(3, 2)
    viewer3d.place_point("start", 0, 1, kind="start")
    viewer3d.place_point("goal", 3, 1, kind="end")
    viewer3d.place_connect([["start", "goal"]])
    viewer3d.show()
"""

from __future__ import annotations

import re

from .app import Viewer
from .model import ZONE_TYPES, DroneMap, Link, Zone
from .replay import Replay

KINDS = ("hub", "start", "end")


class SceneBuilder:
    """Collect terrain, points and connections, then open the viewer."""

    def __init__(self) -> None:
        self._bounds: tuple[int, int] | None = None
        self._zones: dict[str, Zone] = {}
        self._links: list[Link] = []

    def init(self, max_x: int, max_y: int) -> None:
        """Create an empty terrain covering coordinates 0..max_x, 0..max_y.

        The terrain grows by itself if a point is placed outside of it.
        Calling init again clears every point and connection.
        """
        if max_x < 0 or max_y < 0:
            raise ValueError("max_x and max_y must be >= 0")
        self._bounds = (max_x, max_y)
        self._zones = {}
        self._links = []

    def place_point(
        self, name: str, x: int, y: int, *, kind: str = "hub",
        zone_type: str = "normal", color: str | None = None,
        max_drones: int = 1,
    ) -> None:
        """Place the point `name` at integer coordinates (x, y)."""
        if self._bounds is None:
            raise RuntimeError("call init(max_x, max_y) first")
        if not name or re.search(r"[\s-]", name):
            raise ValueError(f"invalid name '{name}': no dash, no space")
        if name in self._zones:
            raise ValueError(f"duplicate point '{name}'")
        if kind not in KINDS:
            raise ValueError(f"kind must be one of {KINDS}")
        if zone_type not in ZONE_TYPES:
            raise ValueError(f"zone_type must be one of {ZONE_TYPES}")
        if max_drones < 1:
            raise ValueError("max_drones must be positive")
        if kind != "hub" and any(z.kind == kind for z in self._zones.values()):
            raise ValueError(f"there is already a '{kind}' point")
        self._zones[name] = Zone(
            name, x, y, kind, zone_type, color, max_drones
        )

    def place_connect(self, list_connection: list[list[str]]) -> None:
        """Place connections: [[name1, name2], ...].

        An item may carry a third element, the link capacity: [a, b, "2"].
        """
        for item in list_connection:
            if len(item) not in (2, 3):
                raise ValueError(f"bad connection {item}: need [a, b]")
            a, b = item[0], item[1]
            for name in (a, b):
                if name not in self._zones:
                    raise ValueError(f"unknown point '{name}'")
            if a == b:
                raise ValueError(f"connection {a}-{b} links a point to itself")
            if any({lk.a, lk.b} == {a, b} for lk in self._links):
                raise ValueError(f"duplicate connection {a}-{b}")
            cap = 1
            if len(item) == 3:
                if not item[2].isdigit() or int(item[2]) < 1:
                    raise ValueError("link capacity must be positive")
                cap = int(item[2])
            self._links.append(Link(a, b, cap))

    def build(
        self, moves: list[str] | None = None, nb_drones: int = 0
    ) -> tuple[DroneMap, Replay]:
        """Return the map and the replay for what was placed so far."""
        if self._bounds is None:
            raise RuntimeError("call init(max_x, max_y) first")
        lines = moves or []
        count = nb_drones or self._count_drones(lines)
        start = self._find("start")
        end = self._find("end")
        if count and not (start and end):
            raise ValueError("drones need a 'start' and an 'end' point")
        drone_map = DroneMap(count, dict(self._zones), list(self._links),
                             start, end, self._bounds)
        return drone_map, Replay(drone_map, lines)

    def show(
        self, moves: list[str] | None = None, nb_drones: int = 0,
        size: tuple[int, int] = (1280, 720),
    ) -> None:
        """Open the 3D window (optionally replaying the given moves)."""
        drone_map, replay = self.build(moves, nb_drones)
        Viewer(drone_map, replay, size).run()

    def _find(self, kind: str) -> str:
        for zone in self._zones.values():
            if zone.kind == kind:
                return zone.name
        return ""

    @staticmethod
    def _count_drones(lines: list[str]) -> int:
        ids = [int(m) for line in lines for m in re.findall(r"D(\d+)-", line)]
        return max(ids, default=0)


_scene = SceneBuilder()


def init(max_x: int, max_y: int) -> None:
    """Initialise the terrain (coordinates 0..max_x, 0..max_y)."""
    _scene.init(max_x, max_y)


def place_point(
    name: str, x: int, y: int, *, kind: str = "hub",
    zone_type: str = "normal", color: str | None = None,
    max_drones: int = 1,
) -> None:
    """Place a point on the 3D terrain."""
    _scene.place_point(name, x, y, kind=kind, zone_type=zone_type,
                       color=color, max_drones=max_drones)


def place_connect(list_connection: list[list[str]]) -> None:
    """Place every requested connection."""
    _scene.place_connect(list_connection)


def show(
    moves: list[str] | None = None, nb_drones: int = 0,
    size: tuple[int, int] = (1280, 720),
) -> None:
    """Open the 3D window for the scene built so far."""
    _scene.show(moves, nb_drones, size)
