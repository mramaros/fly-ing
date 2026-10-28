"""Small immediate-mode OpenGL helpers used by the 3D viewer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import OpenGL.GL as gl
import OpenGL.GLU as glu
import pygame

Vec = tuple[float, float, float]
Color = tuple[float, float, float]

_quadric: Any = None


def quadric() -> Any:
    """Return the shared GLU quadric object."""
    global _quadric
    if _quadric is None:
        _quadric = glu.gluNewQuadric()
        glu.gluQuadricNormals(_quadric, glu.GLU_SMOOTH)
    return _quadric


def set_lit(on: bool) -> None:
    """Enable or disable lighting (neon parts are drawn unlit)."""
    if on:
        gl.glEnable(gl.GL_LIGHTING)
    else:
        gl.glDisable(gl.GL_LIGHTING)


def draw_box(pos: Vec, size: Vec, color: Color) -> None:
    """Draw a lit box centred on pos."""
    x1, x2 = pos[0] - size[0] / 2, pos[0] + size[0] / 2
    y1, y2 = pos[1] - size[1] / 2, pos[1] + size[1] / 2
    z1, z2 = pos[2] - size[2] / 2, pos[2] + size[2] / 2
    gl.glColor3f(*color)
    gl.glBegin(gl.GL_QUADS)
    faces = (
        ((0, 0, 1), ((x1, y1, z2), (x2, y1, z2), (x2, y2, z2), (x1, y2, z2))),
        ((0, 0, -1), ((x2, y1, z1), (x1, y1, z1), (x1, y2, z1), (x2, y2, z1))),
        ((1, 0, 0), ((x2, y1, z2), (x2, y1, z1), (x2, y2, z1), (x2, y2, z2))),
        ((-1, 0, 0), ((x1, y1, z1), (x1, y1, z2), (x1, y2, z2), (x1, y2, z1))),
        ((0, 1, 0), ((x1, y2, z2), (x2, y2, z2), (x2, y2, z1), (x1, y2, z1))),
        ((0, -1, 0), ((x1, y1, z1), (x2, y1, z1), (x2, y1, z2), (x1, y1, z2))),
    )
    for normal, verts in faces:
        gl.glNormal3f(*normal)
        for vert in verts:
            gl.glVertex3f(*vert)
    gl.glEnd()


def draw_prism(
    profile: list[tuple[float, float]], z0: float, z1: float, color: Color
) -> None:
    """Extrude a clockwise (x, y) profile along z between z0 and z1."""
    count = len(profile)
    gl.glColor3f(*color)
    cx = sum(p[0] for p in profile) / count
    cy = sum(p[1] for p in profile) / count
    for z, nz, order in ((z1, 1.0, 1), (z0, -1.0, -1)):
        gl.glBegin(gl.GL_TRIANGLE_FAN)
        gl.glNormal3f(0.0, 0.0, nz)
        gl.glVertex3f(cx, cy, z)
        for px, py in profile[::order] + profile[:1]:
            gl.glVertex3f(px, py, z)
        gl.glEnd()
    gl.glBegin(gl.GL_QUADS)
    for i in range(count):
        ax, ay = profile[i]
        bx, by = profile[(i + 1) % count]
        gl.glNormal3f(-(by - ay), bx - ax, 0.0)
        gl.glVertex3f(ax, ay, z1)
        gl.glVertex3f(bx, by, z1)
        gl.glVertex3f(bx, by, z0)
        gl.glVertex3f(ax, ay, z0)
    gl.glEnd()


def draw_cylinder(
    pos: Vec, radius: float, length: float, color: Color, axis: str
) -> None:
    """Draw a capped cylinder centred on pos, along axis 'x' or 'y'."""
    gl.glPushMatrix()
    gl.glTranslatef(*pos)
    if axis == "x":
        gl.glRotatef(90.0, 0.0, 1.0, 0.0)
    else:
        gl.glRotatef(-90.0, 1.0, 0.0, 0.0)
    gl.glTranslatef(0.0, 0.0, -length / 2)
    gl.glColor3f(*color)
    glu.gluCylinder(quadric(), radius, radius, length, 16, 1)
    glu.gluDisk(quadric(), 0.0, radius, 16, 1)
    gl.glTranslatef(0.0, 0.0, length)
    glu.gluDisk(quadric(), 0.0, radius, 16, 1)
    gl.glPopMatrix()


def draw_cone_x(pos: Vec, radius: float, length: float, color: Color) -> None:
    """Draw a cone along x whose tip points toward +x."""
    gl.glPushMatrix()
    gl.glTranslatef(*pos)
    gl.glRotatef(90.0, 0.0, 1.0, 0.0)
    gl.glTranslatef(0.0, 0.0, -length / 2)
    gl.glColor3f(*color)
    glu.gluCylinder(quadric(), radius, 0.0, length, 16, 1)
    gl.glPopMatrix()


def draw_sphere(pos: Vec, radius: float, color: Color) -> None:
    """Draw a sphere centred on pos."""
    gl.glPushMatrix()
    gl.glTranslatef(*pos)
    gl.glColor3f(*color)
    glu.gluSphere(quadric(), radius, 10, 8)
    gl.glPopMatrix()


def draw_flat_disc(
    pos: Vec, inner: float, outer: float, color: Color, alpha: float = 1.0
) -> None:
    """Draw a flat horizontal ring (or disc when inner is 0)."""
    gl.glPushMatrix()
    gl.glTranslatef(*pos)
    gl.glRotatef(-90.0, 1.0, 0.0, 0.0)
    gl.glColor4f(color[0], color[1], color[2], alpha)
    glu.gluDisk(quadric(), inner, outer, 48, 1)
    gl.glPopMatrix()


def draw_flat_arc(
    pos: Vec, inner: float, outer: float, start: float, sweep: float
) -> None:
    """Draw an annular sector on the ground (angles in degrees)."""
    gl.glPushMatrix()
    gl.glTranslatef(*pos)
    gl.glRotatef(-90.0, 1.0, 0.0, 0.0)
    glu.gluPartialDisk(quadric(), inner, outer, 8, 1, start, sweep)
    gl.glPopMatrix()


@dataclass
class Label:
    """A text rendered into an OpenGL texture."""

    texture: int
    width: int
    height: int


class TextCache:
    """Create and cache text textures."""

    def __init__(self) -> None:
        self._labels: dict[tuple[str, int, tuple[int, int, int]], Label] = {}
        self._fonts: dict[int, pygame.font.Font] = {}

    def get(self, text: str, size: int, rgb: tuple[int, int, int]) -> Label:
        """Return the label for text, rendering it on first use."""
        key = (text, size, rgb)
        if key not in self._labels:
            self._labels[key] = self._render(text, size, rgb)
        return self._labels[key]

    def _render(
        self, text: str, size: int, rgb: tuple[int, int, int]
    ) -> Label:
        if size not in self._fonts:
            self._fonts[size] = pygame.font.Font(None, size)
        surface = self._fonts[size].render(text, True, rgb)
        width, height = surface.get_size()
        data = pygame.image.tostring(surface, "RGBA", True)
        tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
        for param, value in (
            (gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR),
            (gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR),
            (gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE),
            (gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE),
        ):
            gl.glTexParameteri(gl.GL_TEXTURE_2D, param, value)
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, width, height, 0,
            gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, data,
        )
        return Label(int(tex), width, height)


def draw_billboard(
    label: Label, center: Vec, height: float, right: Vec, up: Vec
) -> None:
    """Draw a label as a camera-facing quad in world space."""
    hw = height * label.width / label.height / 2
    hh = height / 2
    corners = ((-hw, -hh, 0.0, 0.0), (hw, -hh, 1.0, 0.0),
               (hw, hh, 1.0, 1.0), (-hw, hh, 0.0, 1.0))
    gl.glEnable(gl.GL_TEXTURE_2D)
    gl.glBindTexture(gl.GL_TEXTURE_2D, label.texture)
    set_lit(False)
    gl.glDisable(gl.GL_FOG)
    gl.glDepthMask(gl.GL_FALSE)
    gl.glColor4f(1.0, 1.0, 1.0, 1.0)
    gl.glBegin(gl.GL_QUADS)
    for u, v, s, t in corners:
        gl.glTexCoord2f(s, t)
        gl.glVertex3f(
            center[0] + right[0] * u + up[0] * v,
            center[1] + right[1] * u + up[1] * v,
            center[2] + right[2] * u + up[2] * v,
        )
    gl.glEnd()
    gl.glDepthMask(gl.GL_TRUE)
    gl.glEnable(gl.GL_FOG)
    gl.glDisable(gl.GL_TEXTURE_2D)


def draw_screen_label(label: Label, x: float, y: float) -> None:
    """Draw a label at pixel (x, y) from the top-left (2D mode)."""
    gl.glEnable(gl.GL_TEXTURE_2D)
    gl.glBindTexture(gl.GL_TEXTURE_2D, label.texture)
    gl.glColor4f(1.0, 1.0, 1.0, 1.0)
    gl.glBegin(gl.GL_QUADS)
    gl.glTexCoord2f(0, 1)
    gl.glVertex2f(x, y)
    gl.glTexCoord2f(1, 1)
    gl.glVertex2f(x + label.width, y)
    gl.glTexCoord2f(1, 0)
    gl.glVertex2f(x + label.width, y + label.height)
    gl.glTexCoord2f(0, 0)
    gl.glVertex2f(x, y + label.height)
    gl.glEnd()
    gl.glDisable(gl.GL_TEXTURE_2D)
