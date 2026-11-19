"""The helicopters: where they are, how they fly between two turns."""

from __future__ import annotations

import math
from dataclasses import dataclass

import OpenGL.GL as gl

from .gl_utils import TextCache, Vec, draw_billboard
from .heli import HeliModel
from .layout import Layout, grid_slots
from .replay import Location, Replay

HOVER = 1.6
Point = tuple[float, float, float]


@dataclass
class Pose:
    """Where a drone is drawn, how hard its rotors work, where it looks."""

    x: float
    y: float
    z: float
    act: float
    heading: float | None


def _ease(t: float) -> float:
    return 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2


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
        self._states = replay.states
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

    def draw(self, src: int, dst: int, u: float, dt: float, now: float,
             right: Vec, up: Vec) -> None:
        """Draw all drones at linear progress u between state src and dst."""
        blink = int(now * 2) % 2 == 0
        follow = 1.0 - math.exp(-8.0 * dt)
        when = src + (dst - src) * u
        for drone, tag in self._tags.items():
            pose = self._pose(drone, when)
            if pose.heading is not None:
                self._turn(drone, pose.heading, follow)
            self._spin[drone] += (240.0 + 1500.0 * pose.act) * dt
            gl.glPushMatrix()
            gl.glTranslatef(pose.x, pose.y, pose.z)
            gl.glRotatef(self._yaw[drone], 0.0, 1.0, 0.0)
            self._model.draw(self._spin[drone], self._spin[drone] * 1.6,
                             blink, -10.0 * pose.act)
            gl.glPopMatrix()
            draw_billboard(tag, (pose.x, pose.y + 1.3, pose.z), 0.5,
                           right, up)

    def _is_link(self, index: int, drone: int) -> bool:
        return self._states[index][drone].link is not None

    def _pose(self, drone: int, when: float) -> Pose:
        """Position of a drone at the replay time `when` (in turns).

        A move toward a restricted zone lasts two turns: the drone is on
        the connection at the end of the first one. Both turns are flown as
        ONE trip, eased only at its two ends, so the drone passes over the
        middle of the connection at full speed instead of stopping there.
        """
        last = len(self._points) - 1
        if last == 0:
            a = self._points[0][drone]
            return Pose(a[0], a[1], a[2], 0.0, None)
        i = min(int(when), last - 1)
        f = min(max(when - i, 0.0), 1.0)
        pa, pb = self._points[i][drone], self._points[i + 1][drone]
        la, lb = self._is_link(i, drone), self._is_link(i + 1, drone)
        if pa == pb and la == lb:
            return Pose(pa[0], pa[1], pa[2], 0.0, None)
        if lb and i + 2 <= last and not self._is_link(i + 2, drone):
            return self._trip(pa, pb, self._points[i + 2][drone], f / 2.0)
        if la and i >= 1 and not self._is_link(i - 1, drone):
            return self._trip(self._points[i - 1][drone], pa, pb,
                              0.5 + f / 2.0)
        e = _ease(f)
        x = pa[0] + (pb[0] - pa[0]) * e
        z = pa[2] + (pb[2] - pa[2]) * e
        height = 2.4 if pa[1] == pb[1] == 0.0 else 0.9
        y = pa[1] + (pb[1] - pa[1]) * e + math.sin(math.pi * e) * height
        return Pose(x, y, z, math.sin(math.pi * e),
                    math.atan2(-(pb[2] - pa[2]), pb[0] - pa[0]))

    @staticmethod
    def _trip(start: Point, mid: Point, end: Point, s: float) -> Pose:
        """Two-turn flight start -> mid (over the link) -> end, s in 0..1."""
        e = _ease(s)
        p, q, k = (start, mid, e * 2) if e < 0.5 else (mid, end, e * 2 - 1)
        x = p[0] + (q[0] - p[0]) * k
        z = p[2] + (q[2] - p[2]) * k
        return Pose(x, HOVER * math.sin(math.pi * e), z,
                    math.sin(math.pi * e),
                    math.atan2(-(q[2] - p[2]), q[0] - p[0]))

    def _turn(self, drone: int, target_rad: float, follow: float) -> None:
        target = math.degrees(target_rad)
        diff = (target - self._yaw[drone] + 180.0) % 360.0 - 180.0
        self._yaw[drone] += diff * follow
