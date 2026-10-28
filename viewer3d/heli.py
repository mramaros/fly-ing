"""Futuristic white-and-red helicopter used as the drone model."""

from __future__ import annotations

import OpenGL.GL as gl
import OpenGL.GLU as glu

from .gl_utils import (
    Color, draw_box, draw_cone_x, draw_cylinder, draw_prism, draw_sphere,
    quadric, set_lit,
)

PROFILE: list[tuple[float, float]] = [
    (-308, 60), (-68, 110), (92, 105), (292, -20), (367, -65), (272, -120),
    (232, -150), (52, -140), (-108, -150), (-218, -65), (-308, 0),
]
WHITE: Color = (0.92, 0.94, 0.96)
DARK: Color = (0.14, 0.16, 0.23)
RED: Color = (0.84, 0.16, 0.16)
GLASS: Color = (0.04, 0.26, 0.38)
SKID: Color = (0.08, 0.08, 0.1)


class HeliModel:
    """Static body compiled in a display list, plus animated rotors."""

    SCALE = 0.0022
    GROUND = 201.0

    def __init__(self) -> None:
        self._list = gl.glGenLists(1)
        gl.glNewList(self._list, gl.GL_COMPILE)
        self._build_body()
        gl.glEndList()

    def draw(
        self, rotor: float, tail: float, blink: bool, tilt: float
    ) -> None:
        """Draw the helicopter with its skids on the local origin."""
        gl.glPushMatrix()
        gl.glScalef(self.SCALE, self.SCALE, self.SCALE)
        gl.glTranslatef(0.0, self.GROUND, 0.0)
        gl.glRotatef(tilt, 0.0, 0.0, 1.0)
        gl.glCallList(self._list)
        self._draw_rotors(rotor, tail, blink)
        gl.glPopMatrix()

    def _build_body(self) -> None:
        draw_prism(PROFILE, -55.0, 55.0, WHITE)
        draw_cylinder((-190, 128, 0), 42, 200, WHITE, "x")
        draw_cone_x((-62, 128, 0), 42, 55, DARK)
        draw_box((-473, 28, 0), (330, 45, 50), WHITE)
        draw_box((-600, 100, 0), (36, 140, 10), WHITE)
        draw_cylinder((-40, 160, 0), 14, 70, DARK, "y")
        for side in (1.0, -1.0):
            draw_box((65, -196, 45 * side), (370, 12, 10), SKID)
            draw_box((-65, -172, 40 * side), (12, 50, 10), SKID)
            draw_box((140, -172, 40 * side), (12, 50, 10), SKID)
            draw_box((130, -92, 58 * side), (12, 60, 8), DARK)
        set_lit(False)
        draw_cylinder((-292, 128, 0), 45, 12, RED, "x")
        draw_box((-600, 172, 0), (38, 24, 12), RED)
        for side in (1.0, -1.0):
            draw_box((170, 20, 57 * side), (150, 80, 4), GLASS)
            draw_box((260, -84, 60 * side), (100, 10, 8), RED)
            gl.glPushMatrix()
            gl.glTranslatef(-140.0, -62.0, 58.0 * side)
            gl.glRotatef(23.0, 0.0, 0.0, 1.0)
            draw_box((0, 0, 0), (110, 10, 8), RED)
            gl.glPopMatrix()
        gl.glPushMatrix()
        gl.glTranslatef(194.0, 48.0, 0.0)
        gl.glRotatef(-32.0, 0.0, 0.0, 1.0)
        draw_box((0, 0, 0), (240, 6, 90), GLASS)
        gl.glPopMatrix()
        set_lit(True)

    def _draw_rotors(self, rotor: float, tail: float, blink: bool) -> None:
        gl.glPushMatrix()
        gl.glTranslatef(-40.0, 197.0, 0.0)
        gl.glRotatef(rotor, 0.0, 1.0, 0.0)
        draw_cylinder((0, 0, 0), 22, 14, DARK, "y")
        draw_box((0, 0, 0), (1000, 5, 28), (0.17, 0.18, 0.22))
        set_lit(False)
        draw_sphere((0, 7, 0), 18, RED)
        gl.glEnable(gl.GL_BLEND)
        gl.glDepthMask(gl.GL_FALSE)
        gl.glPushMatrix()
        gl.glTranslatef(0.0, -2.0, 0.0)
        gl.glRotatef(-90.0, 1.0, 0.0, 0.0)
        gl.glColor4f(1.0, 1.0, 1.0, 0.05)
        glu.gluDisk(quadric(), 0.0, 500.0, 32, 1)
        gl.glPopMatrix()
        gl.glDepthMask(gl.GL_TRUE)
        set_lit(True)
        gl.glPopMatrix()
        gl.glPushMatrix()
        gl.glTranslatef(-640.0, 95.0, 32.0)
        gl.glRotatef(tail, 0.0, 0.0, 1.0)
        draw_box((0, 0, 0), (8, 110, 6), DARK)
        gl.glPopMatrix()
        set_lit(False)
        light: Color = (1.0, 0.23, 0.23) if blink else (0.3, 0.07, 0.07)
        draw_sphere((-600, 182, 0), 11, light)
        set_lit(True)
