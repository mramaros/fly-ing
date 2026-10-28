"""Cyberpunk night city: ground, towers, decoration and rain."""

from __future__ import annotations

import math
import random

import OpenGL.GL as gl

from .gl_utils import Color, draw_box, set_lit
from .layout import Layout

NEON: list[Color] = [
    (1.0, 0.18, 0.53), (0.0, 0.9, 1.0), (0.7, 0.53, 1.0),
    (1.0, 0.82, 0.4), (0.23, 1.0, 0.48),
]
WINDOWS: list[Color] = [
    (1.0, 0.82, 0.4), (0.0, 0.9, 1.0), (1.0, 0.18, 0.53),
    (0.7, 0.53, 1.0), (1.0, 0.91, 0.66),
]
FACES = ((0, 1.0), (0, -1.0), (1, 1.0), (1, -1.0))


class City:
    """Static scenery compiled into one display list."""

    def __init__(self, layout: Layout, seed: int = 7) -> None:
        self._rng = random.Random(seed)
        self._layout = layout
        self._list = gl.glGenLists(1)
        gl.glNewList(self._list, gl.GL_COMPILE)
        self._ground()
        self._platform()
        self._small_buildings()
        area = layout.half_x * layout.half_z
        self._towers(min(400, 80 + int(area / 12)))
        gl.glEndList()

    def draw(self) -> None:
        """Draw the whole static scenery."""
        gl.glCallList(self._list)

    def _ground(self) -> None:
        reach = max(self._layout.half_x, self._layout.half_z) + 260.0
        draw_box((0, -0.55, 0), (2 * reach, 0.5, 2 * reach),
                 (0.03, 0.025, 0.08))
        set_lit(False)
        gl.glColor3f(0.12, 0.07, 0.25)
        gl.glBegin(gl.GL_LINES)
        for i in range(-int(reach / 4), int(reach / 4) + 1):
            gl.glVertex3f(i * 4.0, -0.29, -reach)
            gl.glVertex3f(i * 4.0, -0.29, reach)
            gl.glVertex3f(-reach, -0.29, i * 4.0)
            gl.glVertex3f(reach, -0.29, i * 4.0)
        gl.glEnd()
        set_lit(True)

    def _platform(self) -> None:
        hx, hz = self._layout.half_x, self._layout.half_z
        draw_box((0, -0.15, 0), (2 * hx, 0.3, 2 * hz), (0.04, 0.03, 0.1))
        set_lit(False)
        gl.glLineWidth(2.0)
        gl.glColor3f(1.0, 0.18, 0.53)
        gl.glBegin(gl.GL_LINE_LOOP)
        for x, z in ((-hx, -hz), (hx, -hz), (hx, hz), (-hx, hz)):
            gl.glVertex3f(x, 0.01, z)
        gl.glEnd()
        if self._layout.grid is not None:
            self._terrain_grid(*self._layout.grid)
        set_lit(True)

    def _terrain_grid(
        self, x_lo: int, x_hi: int, y_lo: int, y_hi: int
    ) -> None:
        """Faint lines at every integer coordinate of the terrain."""
        to_world = self._layout.to_world
        gl.glLineWidth(1.0)
        gl.glColor3f(0.1, 0.2, 0.38)
        gl.glBegin(gl.GL_LINES)
        for gx in range(x_lo, x_hi + 1):
            gl.glVertex3f(to_world(gx, y_lo)[0], 0.015, to_world(gx, y_lo)[1])
            gl.glVertex3f(to_world(gx, y_hi)[0], 0.015, to_world(gx, y_hi)[1])
        for gy in range(y_lo, y_hi + 1):
            gl.glVertex3f(to_world(x_lo, gy)[0], 0.015, to_world(x_lo, gy)[1])
            gl.glVertex3f(to_world(x_hi, gy)[0], 0.015, to_world(x_hi, gy)[1])
        gl.glEnd()

    def _small_buildings(self) -> None:
        hx, hz = self._layout.half_x - 1.2, self._layout.half_z - 1.2
        spots: list[tuple[float, float]] = []
        x = -hx
        while x <= hx:
            spots += [(x, -hz), (x, hz)]
            x += 3.2
        z = -hz + 3.2
        while z < hz - 1.0:
            spots += [(-hx, z), (hx, z)]
            z += 3.2
        for sx, sz in spots:
            h = 1.0 + self._rng.random() * 2.4
            w = 0.9 + self._rng.random() * 0.7
            draw_box((sx, h / 2, sz), (w, h, w), (0.08, 0.07, 0.18))
            set_lit(False)
            draw_box((sx, h + 0.03, sz), (w + 0.1, 0.07, w + 0.1),
                     self._rng.choice(NEON))
            set_lit(True)

    def _towers(self, count: int) -> None:
        hx = self._layout.half_x + 6.0
        hz = self._layout.half_z + 6.0
        ring = max(self._layout.camera_distance * 0.88 + 6.0,
                   math.hypot(hx, hz) + 8.0)
        made = tries = 0
        while made < count and tries < 2000:
            tries += 1
            x = self._rng.uniform(-hx - 55, hx + 55)
            z = self._rng.uniform(-hz - 55, hz + 55)
            if abs(x) < hx and abs(z) < hz:
                continue
            w = self._rng.uniform(2.5, 6.0)
            d = self._rng.uniform(2.5, 6.0)
            roll = self._rng.random()
            if roll < 0.55:
                h = self._rng.uniform(4, 13)
            elif roll < 0.88:
                h = self._rng.uniform(12, 26)
            else:
                h = self._rng.uniform(26, 46)
            if math.hypot(x, z) < ring:
                h = self._rng.uniform(3.0, 6.5)
            self._tower(x, z, w, d, h)
            made += 1

    def _tower(self, x: float, z: float, w: float, d: float, h: float) -> None:
        shade = self._rng.uniform(0.05, 0.1)
        draw_box((x, h / 2, z), (w, h, d), (shade, shade, shade * 1.8))
        set_lit(False)
        self._windows(x, z, w, d, h)
        if self._rng.random() < 0.55:
            draw_box((x + w / 2, h / 2, z + d / 2), (0.16, h * 0.95, 0.16),
                     self._rng.choice(NEON))
        if h > 26:
            draw_box((x, h + 0.1, z), (0.3, 0.3, 0.3), (1.0, 0.23, 0.23))
        set_lit(True)

    def _windows(
        self, x: float, z: float, w: float, d: float, h: float
    ) -> None:
        gl.glBegin(gl.GL_QUADS)
        for axis, sign in FACES:
            length = d if axis == 0 else w
            cols = max(2, int(length / 1.1))
            rows = max(2, int(h / 1.6))
            cw, ch = length / cols, h / rows
            for r in range(rows):
                for c in range(cols):
                    if self._rng.random() < 0.45:
                        continue
                    gl.glColor3f(*self._rng.choice(WINDOWS))
                    u0 = -length / 2 + c * cw + cw * 0.2
                    u1 = u0 + cw * 0.6
                    v0 = r * ch + ch * 0.25
                    v1 = r * ch + ch * 0.7
                    for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1)):
                        if axis == 1:
                            gl.glVertex3f(x + u, v, z + sign * (d / 2 + 0.02))
                        else:
                            gl.glVertex3f(x + sign * (w / 2 + 0.02), v, z + u)
        gl.glEnd()


class Rain:
    """Thin rain streaks falling over the city."""

    def __init__(self, layout: Layout, count: int = 800) -> None:
        self._rng = random.Random(3)
        self._hx = layout.half_x + 50.0
        self._hz = layout.half_z + 50.0
        self._drops = [
            [self._rng.uniform(-self._hx, self._hx),
             self._rng.uniform(0, 40),
             self._rng.uniform(-self._hz, self._hz),
             self._rng.uniform(18, 28)]
            for _ in range(count)
        ]

    def update(self, dt: float) -> None:
        """Move the drops down and recycle them at the top."""
        for drop in self._drops:
            drop[1] -= drop[3] * dt
            if drop[1] < 0.0:
                drop[1] = self._rng.uniform(30, 42)

    def draw(self) -> None:
        """Draw the rain as short translucent lines."""
        set_lit(False)
        gl.glDepthMask(gl.GL_FALSE)
        gl.glColor4f(0.62, 0.72, 1.0, 0.35)
        gl.glBegin(gl.GL_LINES)
        for x, y, z, _ in self._drops:
            gl.glVertex3f(x, y, z)
            gl.glVertex3f(x, y + 0.9, z)
        gl.glEnd()
        gl.glDepthMask(gl.GL_TRUE)
        set_lit(True)
