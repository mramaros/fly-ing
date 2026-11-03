"""Interactive pygame + OpenGL window."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

import OpenGL.GL as gl
import OpenGL.GLU as glu
import pygame

from .city import City, Rain
from .fleet import Fleet
from .gl_utils import (
    TextCache, Vec, draw_flat_disc, draw_screen_label, set_lit,
)
from .layout import Layout
from .model import DroneMap
from .replay import Replay
from .zones import ZoneRenderer

FOG_COLOR = (0.043, 0.035, 0.125, 1.0)
HINTS = "SPACE play/pause   LEFT/RIGHT step   R restart   A orbit   T top view"
HINTS_CENTER = (
    "RIGHT-CLICK new camera center   RIGHT-DRAG pan   C reset center"
    "   WHEEL zoom"
)
MARKER_TIME = 1.2
FOV = 50.0
PICK_HEIGHT = 0.25


@dataclass
class OrbitCamera:
    """Camera orbiting around a target point."""

    dist: float = 40.0
    az: float = -0.45
    el: float = 0.5
    el_goal: float = 0.5
    target: Vec = (0.0, 1.0, 0.0)
    goal: Vec = (0.0, 1.0, 0.0)
    home: Vec = (0.0, 1.0, 0.0)
    limit: tuple[float, float] = (1e9, 1e9)
    top_view: bool = False
    auto: bool = False
    dragging: bool = field(default=False)

    def update(self, dt: float) -> None:
        """Ease the elevation and centre, spin when auto-orbit is on."""
        self.el += (self.el_goal - self.el) * min(1.0, dt * 5.0)
        k = min(1.0, dt * 6.0)
        self.target = (
            self.target[0] + (self.goal[0] - self.target[0]) * k,
            self.target[1] + (self.goal[1] - self.target[1]) * k,
            self.target[2] + (self.goal[2] - self.target[2]) * k,
        )
        if self.auto and not self.dragging:
            self.az += dt * 0.15

    def toggle_top(self) -> None:
        """Switch between the 3/4 view and the top view."""
        self.top_view = not self.top_view
        self.el_goal = 1.4 if self.top_view else 0.5

    def apply(self) -> None:
        """Load the view matrix."""
        ce = math.cos(self.el)
        tx, ty, tz = self.target
        glu.gluLookAt(
            tx + self.dist * math.sin(self.az) * ce,
            ty + self.dist * math.sin(self.el),
            tz + self.dist * math.cos(self.az) * ce,
            tx, ty, tz, 0.0, 1.0, 0.0,
        )

    def recenter(self, x: float, z: float) -> None:
        """Smoothly move the orbit centre to the ground point (x, z)."""
        lim_x, lim_z = self.limit
        self.goal = (max(-lim_x, min(lim_x, x)), self.home[1],
                     max(-lim_z, min(lim_z, z)))

    def pan(self, grabbed: Vec, under: Vec) -> None:
        """Slide the centre so `grabbed` ends up where `under` was."""
        self.recenter(self.goal[0] + grabbed[0] - under[0],
                      self.goal[2] + grabbed[2] - under[2])
        self.target = self.goal

    def position(self) -> Vec:
        """World position of the camera."""
        ce = math.cos(self.el)
        return (
            self.target[0] + self.dist * math.sin(self.az) * ce,
            self.target[1] + self.dist * math.sin(self.el),
            self.target[2] + self.dist * math.cos(self.az) * ce,
        )

    def pick_ground(
        self, px: float, py: float, width: int, height: int
    ) -> Vec | None:
        """Ground point (y = PICK_HEIGHT) under the pixel (px, py)."""
        ce, se = math.cos(self.el), math.sin(self.el)
        fwd = (-math.sin(self.az) * ce, -se, -math.cos(self.az) * ce)
        right, up = self.right(), self.up()
        half = math.tan(math.radians(FOV / 2))
        nx = (2.0 * px / width - 1.0) * half * width / height
        ny = (1.0 - 2.0 * py / height) * half
        ray = tuple(f + r * nx + u * ny for f, r, u in zip(fwd, right, up))
        pos = self.position()
        if ray[1] >= -1e-6:
            return None
        t = (PICK_HEIGHT - pos[1]) / ray[1]
        return (pos[0] + ray[0] * t, PICK_HEIGHT, pos[2] + ray[2] * t)

    def right(self) -> Vec:
        """Unit vector pointing to the right of the screen."""
        return (math.cos(self.az), 0.0, -math.sin(self.az))

    def up(self) -> Vec:
        """Unit vector pointing to the top of the screen."""
        se, ce = math.sin(self.el), math.cos(self.el)
        return (-math.sin(self.az) * se, ce, -math.cos(self.az) * se)


class Playback:
    """Turn-by-turn playback state."""

    DURATION = 1.8
    PAUSE = 0.6

    def __init__(self, total: int) -> None:
        self.total = total
        self.cur = 0
        self.target = 0
        self.t = 1.0
        self.playing = False
        self._wait = 0.0

    @property
    def busy(self) -> bool:
        """True while a turn animation is running."""
        return self.t < 1.0

    @property
    def shown(self) -> int:
        """Turn number displayed in the HUD."""
        return self.target if self.busy else self.cur

    def ease(self) -> float:
        """Smoothed progress of the running animation."""
        t = min(self.t, 1.0)
        return 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2

    def step(self, delta: int) -> None:
        """Start moving to the next or previous turn."""
        goal = self.cur + delta
        if not self.busy and 0 <= goal <= self.total:
            self.target, self.t = goal, 0.0

    def restart(self) -> None:
        """Go back to the initial state."""
        self.cur = self.target = 0
        self.t = 1.0

    def toggle(self) -> None:
        """Play or pause the automatic playback."""
        if not self.playing and self.cur == self.total and not self.busy:
            self.restart()
        self.playing = not self.playing
        self._wait = 0.0

    def jump(self, position: float) -> None:
        """Freeze the playback at a (fractional) turn position."""
        position = max(0.0, min(float(self.total), position))
        self.cur = int(position)
        frac = position - self.cur
        self.target = min(self.total, self.cur + 1) if frac else self.cur
        self.t = frac if frac else 1.0

    def update(self, dt: float) -> None:
        """Advance the animation clock."""
        if self.busy:
            self.t += dt / self.DURATION
            if self.t >= 1.0:
                self.cur, self.t = self.target, 1.0
                self._wait = 0.0
        elif self.playing:
            self._wait += dt
            if self._wait >= self.PAUSE:
                if self.cur < self.total:
                    self.step(1)
                else:
                    self.playing = False


class Viewer:
    """Create the window and run the render loop."""

    def __init__(self, drone_map: DroneMap, replay: Replay,
                 size: tuple[int, int] = (1280, 720)) -> None:
        self.map, self.replay, self.size = drone_map, replay, size
        pygame.init()
        pygame.display.set_caption("Fly-in 3D - night city")
        pygame.display.set_mode(size, pygame.DOUBLEBUF | pygame.OPENGL)
        self._setup_gl()
        self.text = TextCache()
        self.layout = Layout(drone_map)
        self.city = City(self.layout)
        self.rain = Rain(self.layout)
        self.zones = ZoneRenderer(drone_map, self.layout, self.text)
        self.fleet = Fleet(self.layout, replay, self.text)
        self.play = Playback(replay.turns)
        self.cam = OrbitCamera(dist=self.layout.camera_distance)
        self.cam.limit = (self.layout.half_x + 25.0,
                          self.layout.half_z + 25.0)
        self._right_down: tuple[int, int] | None = None
        self._right_moved = False
        self._marker: tuple[float, float, float] | None = None

    def focus(self, zone: str, zoom: float) -> None:
        """Aim the camera at a zone and zoom in (for close-up shots)."""
        x, z = self.layout.pos[zone]
        self.cam.target = self.cam.goal = (x, 1.0, z)
        self.cam.dist /= zoom

    @staticmethod
    def _setup_gl() -> None:
        gl.glClearColor(*FOG_COLOR)
        for cap in (gl.GL_DEPTH_TEST, gl.GL_BLEND, gl.GL_FOG,
                    gl.GL_LIGHTING, gl.GL_LIGHT0, gl.GL_LIGHT1,
                    gl.GL_COLOR_MATERIAL, gl.GL_NORMALIZE):
            gl.glEnable(cap)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glColorMaterial(gl.GL_FRONT_AND_BACK, gl.GL_AMBIENT_AND_DIFFUSE)
        gl.glLightModelfv(gl.GL_LIGHT_MODEL_AMBIENT, (0.32, 0.27, 0.58, 1.0))
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_DIFFUSE, (1.0, 0.45, 0.75, 1.0))
        gl.glLightfv(gl.GL_LIGHT1, gl.GL_DIFFUSE, (0.3, 0.85, 1.0, 1.0))
        gl.glFogi(gl.GL_FOG_MODE, gl.GL_EXP2)
        gl.glFogfv(gl.GL_FOG_COLOR, FOG_COLOR)
        gl.glFogf(gl.GL_FOG_DENSITY, 0.009)

    def run(self) -> None:
        """Main loop: events, update, draw."""
        clock = pygame.time.Clock()
        start = time.time()
        running = True
        while running:
            dt = clock.tick(60) / 1000.0
            for event in pygame.event.get():
                running = self._handle(event) and running
            self.play.update(dt)
            self.render(dt, time.time() - start)
            pygame.display.flip()
        pygame.quit()

    def snapshot(self, path: str, position: float) -> None:
        """Render the scene frozen at a turn position and save a PNG."""
        self.play.jump(position)
        for i in range(40):
            self.render(0.05, i * 0.05)
        width, height = self.size
        data = gl.glReadPixels(0, 0, width, height, gl.GL_RGB,
                               gl.GL_UNSIGNED_BYTE)
        image = pygame.image.fromstring(bytes(data), self.size, "RGB", True)
        pygame.image.save(image, path)
        pygame.quit()

    def _handle(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN:
            return self._key(event.key)
        self._mouse(event)
        return True

    def _mouse(self, event: pygame.event.Event) -> None:
        cam = self.cam
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            cam.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            cam.dragging = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            self._right_down, self._right_moved = tuple(event.pos), False
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
            if self._right_down is not None and not self._right_moved:
                self._recenter_at(event.pos[0], event.pos[1])
            self._right_down = None
        elif event.type == pygame.MOUSEMOTION:
            self._motion(event)
        elif event.type == pygame.MOUSEWHEEL:
            closer = cam.dist - event.y * 2.0
            cam.dist = max(12.0, min(160.0, closer))

    def _motion(self, event: pygame.event.Event) -> None:
        cam = self.cam
        if cam.dragging:
            cam.az -= event.rel[0] * 0.006
            lifted = cam.el + event.rel[1] * 0.004
            cam.el = max(0.1, min(1.45, lifted))
            cam.el_goal = cam.el
        elif self._right_down is not None:
            ox, oy = self._right_down
            if math.hypot(event.pos[0] - ox, event.pos[1] - oy) > 5:
                self._right_moved = True
            if self._right_moved:
                self._pan(event.pos, event.rel)

    def _pan(self, pos: tuple[int, int], rel: tuple[int, int]) -> None:
        """Keep the grabbed ground point under the mouse."""
        cam = self.cam
        prev = (pos[0] - rel[0], pos[1] - rel[1])
        before = cam.pick_ground(prev[0], prev[1], *self.size)
        after = cam.pick_ground(pos[0], pos[1], *self.size)
        if before is None or after is None:
            return
        step = math.hypot(before[0] - after[0], before[2] - after[2])
        if step < cam.dist * 3:
            cam.pan(before, after)

    def _recenter_at(self, px: int, py: int) -> None:
        """Make the clicked ground point (or the clicked pad) the centre."""
        point = self.cam.pick_ground(px, py, *self.size)
        if point is None:
            return
        x, z = point[0], point[2]
        best = math.inf
        for name, (zx, zz) in self.layout.pos.items():
            gap = math.hypot(x - zx, z - zz)
            if gap <= self.layout.radius[name] + 0.5 and gap < best:
                best, target = gap, (zx, zz)
        if best < math.inf:
            x, z = target
        self.cam.recenter(x, z)
        self._marker = (self.cam.goal[0], self.cam.goal[2], MARKER_TIME)

    def _draw_marker(self, dt: float) -> None:
        """Expanding ring that shows where the new centre is."""
        if self._marker is None:
            return
        x, z, left = self._marker
        left -= dt
        if left <= 0.0:
            self._marker = None
            return
        self._marker = (x, z, left)
        k = left / MARKER_TIME
        set_lit(False)
        gl.glDepthMask(gl.GL_FALSE)
        for radius, alpha in ((0.5, k), (0.8 + (1.0 - k) * 2.2, k * 0.8)):
            draw_flat_disc((x, 0.34, z), radius - 0.09, radius,
                           (1.0, 1.0, 1.0), alpha)
        gl.glDepthMask(gl.GL_TRUE)
        set_lit(True)

    def _key(self, key: int) -> bool:
        if key == pygame.K_ESCAPE:
            return False
        if key == pygame.K_SPACE:
            self.play.toggle()
        elif key == pygame.K_RIGHT:
            self.play.playing = False
            self.play.step(1)
        elif key == pygame.K_LEFT:
            self.play.playing = False
            self.play.step(-1)
        elif key == pygame.K_r:
            self.play.restart()
        elif key == pygame.K_a:
            self.cam.auto = not self.cam.auto
        elif key == pygame.K_t:
            self.cam.toggle_top()
        elif key == pygame.K_c:
            self.cam.recenter(self.cam.home[0], self.cam.home[2])
            self._marker = None
        return True

    def render(self, dt: float, now: float) -> None:
        """Draw one complete frame."""
        width, height = self.size
        gl.glViewport(0, 0, width, height)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        glu.gluPerspective(50.0, width / height, 0.1,
                           self.cam.dist * 8.0 + 400.0)
        gl.glFogf(gl.GL_FOG_DENSITY, 0.36 / self.cam.dist)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()
        self.cam.update(dt)
        self.cam.apply()
        gl.glLightfv(gl.GL_LIGHT0, gl.GL_POSITION, (-0.5, 0.8, 0.4, 0.0))
        gl.glLightfv(gl.GL_LIGHT1, gl.GL_POSITION, (0.7, 0.6, -0.6, 0.0))
        right, up = self.cam.right(), self.cam.up()
        self.rain.update(dt)
        self.city.draw()
        self.zones.draw(right, up)
        pb = self.play
        busy = pb.busy
        self.fleet.draw(pb.cur, pb.target if busy else pb.cur,
                        pb.ease() if busy else 1.0, dt, now, right, up)
        self._draw_marker(dt)
        self.rain.draw()
        self._hud()

    def _hud(self) -> None:
        width, height = self.size
        shown = self.play.shown
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        gl.glOrtho(0, width, height, 0, -1, 1)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        gl.glLoadIdentity()
        for cap in (gl.GL_DEPTH_TEST, gl.GL_LIGHTING, gl.GL_FOG):
            gl.glDisable(cap)
        title = "Start"
        if shown:
            title = f"Turn {shown} / {self.replay.turns}"
        moves = "" if shown == 0 else self.replay.lines[shown - 1]
        count = self.replay.delivered(self.play.cur)
        done = f"Delivered {count} / {self.map.nb_drones}"
        for text, size, rgb, x, y in (
            (title, 44, (232, 228, 255), 18, 14),
            (moves[:96] or "all drones at start", 28, (185, 178, 224), 18, 48),
            (done, 34, (59, 255, 122), 18, 74),
            (HINTS, 24, (150, 144, 190), 18, height - 56),
            (HINTS_CENTER, 24, (150, 144, 190), 18, height - 30),
        ):
            draw_screen_label(self.text.get(text, size, rgb), x, y)
        for cap in (gl.GL_DEPTH_TEST, gl.GL_LIGHTING, gl.GL_FOG):
            gl.glEnable(cap)
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_MODELVIEW)


def run_viewer(drone_map: DroneMap, replay: Replay,
               size: tuple[int, int] = (1280, 720)) -> None:
    """Open the interactive 3D viewer."""
    Viewer(drone_map, replay, size).run()
