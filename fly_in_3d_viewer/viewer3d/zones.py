"""Landing pads (zones) and neon connections."""

from __future__ import annotations

import math

import OpenGL.GL as gl
import OpenGL.GLU as glu

from .gl_utils import (
    Color, Label, TextCache, Vec, draw_billboard, draw_box, draw_flat_arc,
    draw_flat_disc, quadric, set_lit,
)
from .layout import Layout, zone_color
from .model import DroneMap, Zone

LINK_COLOR: Color = (0.0, 0.9, 1.0)


def _rgb255(color: Color) -> tuple[int, int, int]:
    return (int(color[0] * 255), int(color[1] * 255), int(color[2] * 255))


class ZoneRenderer:
    """Draw pads and links; labels are drawn each frame as billboards."""

    def __init__(self, drone_map: DroneMap, layout: Layout,
                 text: TextCache) -> None:
        self._map = drone_map
        self._layout = layout
        self._labels: list[tuple[Label, Vec, float]] = []
        for zone in drone_map.zones.values():
            self._add_labels(zone, text)
        self._list = gl.glGenLists(1)
        gl.glNewList(self._list, gl.GL_COMPILE)
        for link in drone_map.links:
            self._draw_link(link.a, link.b, link.capacity)
        for zone in drone_map.zones.values():
            self._draw_pad(zone)
        gl.glEndList()

    def draw(self, right: Vec, up: Vec) -> None:
        """Draw pads, links and their labels."""
        gl.glCallList(self._list)
        for label, pos, height in self._labels:
            draw_billboard(label, pos, height, right, up)

    def _add_labels(self, zone: Zone, text: TextCache) -> None:
        x, z = self._layout.pos[zone.name]
        col = _rgb255(zone_color(zone))
        if zone.kind == "hub":
            sub = f"{zone.zone_type} - max {zone.max_drones}"
        else:
            sub = f"{zone.kind} - no limit"
        self._labels.append((text.get(zone.name, 56, col),
                             (x, 5.6, z), 1.1))
        self._labels.append((text.get(sub, 40, (185, 178, 224)),
                             (x, 4.6, z), 0.7))
        for link in self._map.links:
            if link.capacity > 1 and zone.name == link.a:
                bx, bz = self._layout.pos[link.b]
                mid = ((x + bx) / 2, 1.4, (z + bz) / 2)
                caption = f"link max {link.capacity}"
                label = text.get(caption, 40, (0, 229, 255))
                self._labels.append((label, mid, 0.7))

    def _draw_link(self, a: str, b: str, capacity: int) -> None:
        ax, az = self._layout.pos[a]
        bx, bz = self._layout.pos[b]
        dx, dz = bx - ax, bz - az
        length = math.hypot(dx, dz)
        angle = math.degrees(math.atan2(-dz, dx))
        px, pz = -dz / length, dx / length
        offsets = (-0.35, 0.35) if capacity > 1 else (0.0,)
        set_lit(False)
        for off in offsets:
            mx, mz = (ax + bx) / 2 + px * off, (az + bz) / 2 + pz * off
            self._strip(mx, 0.08, mz, length, 0.2, angle, 1.0)
        gl.glEnable(gl.GL_BLEND)
        gl.glDepthMask(gl.GL_FALSE)
        self._strip((ax + bx) / 2, 0.06, (az + bz) / 2, length,
                    1.3 if capacity > 1 else 0.8, angle, 0.16)
        gl.glDepthMask(gl.GL_TRUE)
        set_lit(True)

    @staticmethod
    def _strip(x: float, y: float, z: float, length: float, width: float,
               angle: float, alpha: float) -> None:
        gl.glPushMatrix()
        gl.glTranslatef(x, y, z)
        gl.glRotatef(angle, 0.0, 1.0, 0.0)
        gl.glColor4f(LINK_COLOR[0], LINK_COLOR[1], LINK_COLOR[2], alpha)
        gl.glBegin(gl.GL_QUADS)
        for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            gl.glVertex3f(sx * length / 2, 0.0, sz * width / 2)
        gl.glEnd()
        gl.glPopMatrix()

    def _draw_pad(self, zone: Zone) -> None:
        x, z = self._layout.pos[zone.name]
        r = self._layout.radius[zone.name]
        col = zone_color(zone)
        blocked = zone.zone_type == "blocked"
        gl.glPushMatrix()
        gl.glTranslatef(x, 0.0, z)
        base = (0.2, 0.04, 0.06) if blocked else (0.05, 0.04, 0.13)
        gl.glColor3f(*base)
        gl.glPushMatrix()
        gl.glRotatef(-90.0, 1.0, 0.0, 0.0)
        glu.gluCylinder(quadric(), r, r, 0.25, 40, 1)
        gl.glTranslatef(0.0, 0.0, 0.25)
        glu.gluDisk(quadric(), 0.0, r, 40, 1)
        gl.glPopMatrix()
        set_lit(False)
        gl.glEnable(gl.GL_BLEND)
        if blocked:
            self._draw_cross(r)
        elif zone.zone_type == "restricted":
            gl.glColor3f(1.0, 0.35, 0.1)
            for k in range(8):
                draw_flat_arc((0, 0.27, 0), r - 0.14, r, k * 45.0, 28.0)
        else:
            draw_flat_disc((0, 0.27, 0), r - 0.1, r, col)
        if zone.zone_type == "priority":
            draw_flat_disc((0, 0.27, 0), r - 0.5, r - 0.42, (1.0, 1.0, 1.0))
        if not blocked:
            draw_flat_disc((0, 0.28, 0), 0.0, r - 0.1, col, 0.16)
        self._draw_beam(r, col)
        set_lit(True)
        gl.glPopMatrix()

    @staticmethod
    def _draw_cross(r: float) -> None:
        for angle in (45.0, -45.0):
            gl.glPushMatrix()
            gl.glRotatef(angle, 0.0, 1.0, 0.0)
            draw_box((0, 0.3, 0), (2 * r * 0.8, 0.05, 0.3), (1.0, 0.2, 0.25))
            gl.glPopMatrix()
        draw_flat_disc((0, 0.27, 0), r - 0.1, r, (1.0, 0.2, 0.25))

    @staticmethod
    def _draw_beam(r: float, col: Color) -> None:
        gl.glDepthMask(gl.GL_FALSE)
        gl.glDisable(gl.GL_CULL_FACE)
        gl.glColor4f(col[0], col[1], col[2], 0.06)
        gl.glPushMatrix()
        gl.glRotatef(-90.0, 1.0, 0.0, 0.0)
        glu.gluCylinder(quadric(), r - 0.1, r - 0.1, 7.0, 32, 1)
        gl.glPopMatrix()
        gl.glDepthMask(gl.GL_TRUE)
