"""The helicopters: where they are, how they fly between two turns."""

from __future__ import annotations

import math

import OpenGL.GL as gl

from .gl_utils import TextCache, Vec, draw_billboard
from .heli import HeliModel
from .layout import Layout, grid_slots
from .replay import Location, Replay

HOVER = 1.6
Point = tuple[float, float, float]


class Fleet:
    """Interpolate and draw every drone between two replay states."""

    def __init__(
        self, layout: Layout, replay: Replay, text: TextCache
    ) -> None:
        self._layout = layout
        self._model = HeliModel()
        self._tags = {
            d: text.get(f"D{d}", 44, (255, 255, 255))
            for d in replay.states[0]
        }
        self._points = [self._state_points(s) for s in replay.states]
        yaw0 = 0.0
        if replay.map.start in layout.pos and replay.map.end in layout.pos:
            sx, sz = layout.pos[replay.map.start]
            ex, ez = layout.pos[replay.map.end]
            yaw0 = math.degrees(math.atan2(-(ez - sz), ex - sx))
        self._yaw = {d: yaw0 for d in self._tags}
        self._spin = {d: 0.0 for d in self._tags}

    def _state_points(self, state: dict[int, Location]) -> dict[int, Point]:
        zones: dict[str, list[int]] = {}
        links: dict[tuple[str, str], list[int]] = {}
        for drone in sorted(state):
            loc = state[drone]
            if loc.zone is not None:
                zones.setdefault(loc.zone, []).append(drone)
            elif loc.link is not None:
                links.setdefault(loc.link, []).append(drone)
        out: dict[int, Point] = {}
        for name, ids in zones.items():
            px, pz = self._layout.pos[name]
            for drone, (dx, dz) in zip(ids, grid_slots(len(ids))):
                out[drone] = (px + dx, 0.0, pz + dz)
        for (a, b), ids in links.items():
            ax, az = self._layout.pos[a]
            bx, bz = self._layout.pos[b]
            length = math.hypot(bx - ax, bz - az) or 1.0
            nx, nz = -(bz - az) / length, (bx - ax) / length
            for i, drone in enumerate(ids):
                off = (i - (len(ids) - 1) / 2) * 0.9
                out[drone] = ((ax + bx) / 2 + nx * off, HOVER,
                              (az + bz) / 2 + nz * off)
        return out

    def draw(self, src: int, dst: int, e: float, dt: float, now: float,
             right: Vec, up: Vec) -> None:
        """Draw all drones at fraction e between state src and dst."""
        blink = int(now * 2) % 2 == 0
        follow = 1.0 - math.exp(-8.0 * dt)
        for drone, tag in self._tags.items():
            a = self._points[src][drone]
            b = self._points[dst][drone]
            moved = a != b
            x = a[0] + (b[0] - a[0]) * e
            z = a[2] + (b[2] - a[2]) * e
            y = a[1] + (b[1] - a[1]) * e
            act = math.sin(math.pi * e) if moved else 0.0
            if moved:
                y += act * (2.4 if a[1] == b[1] == 0.0 else 0.9)
                self._turn(drone, math.atan2(-(b[2] - a[2]), b[0] - a[0]),
                           follow)
            self._spin[drone] += (240.0 + 1500.0 * act) * dt
            gl.glPushMatrix()
            gl.glTranslatef(x, y, z)
            gl.glRotatef(self._yaw[drone], 0.0, 1.0, 0.0)
            self._model.draw(self._spin[drone], self._spin[drone] * 1.6,
                             blink, -10.0 * act)
            gl.glPopMatrix()
            draw_billboard(tag, (x, y + 1.3, z), 0.5, right, up)

    def _turn(self, drone: int, target_rad: float, follow: float) -> None:
        target = math.degrees(target_rad)
        diff = (target - self._yaw[drone] + 180.0) % 360.0 - 180.0
        self._yaw[drone] += diff * follow
