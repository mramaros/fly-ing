"""Pygame interface for the 2D fly-in map viewer."""

import colorsys

import pygame

from viewer2d import MapData, Point, Replay

Position = tuple[float, float]
Color = tuple[int, int, int]

WINDOW_PADDING = 60
BACKGROUND = (0, 0, 0)
LINE_COLOR = (150, 150, 150)
TEXT_COLOR = (242, 242, 242)
HELP_COLOR = (197, 212, 224)
WHITE = (242, 242, 242)
START_COLOR = (40, 170, 90)
END_COLOR = (220, 70, 70)
DEFAULT_POINT_COLOR = (60, 120, 220)
DRONE_COLORS: list[Color] = [
    (35, 115, 220),
    (235, 135, 35),
    (145, 75, 190),
    (25, 155, 125),
    (220, 75, 95),
]


class View:
    """Convert map coordinates into screen pixels (with zoom and pan)."""

    def __init__(self, map_data: MapData, size: tuple[int, int]) -> None:
        """Fit the whole map inside a window of the given size."""
        self.width = size[0]
        self.height = size[1]
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.min_x = 0
        self.min_y = 0
        self.scale = 1.0
        self.left = 0.0
        self.top = 0.0
        self._fit(map_data)

    def _fit(self, map_data: MapData) -> None:
        """Compute the scale and the margins so the map is centered."""
        if len(map_data.points) == 0:
            return
        x_values = []
        y_values = []
        for point in map_data.points.values():
            x_values.append(point.x)
            y_values.append(point.y)
        self.min_x = min(x_values)
        self.min_y = min(y_values)
        map_width = max(max(x_values) - self.min_x, 1)
        map_height = max(max(y_values) - self.min_y, 1)
        self.scale = min(
            (self.width - 2 * WINDOW_PADDING) / map_width,
            (self.height - 2 * WINDOW_PADDING) / map_height,
        )
        self.left = (self.width - map_width * self.scale) / 2
        self.top = (self.height - map_height * self.scale) / 2

    def to_screen(self, x: float, y: float) -> tuple[int, int]:
        """Return the pixel of a map coordinate."""
        base_x = self.left + (x - self.min_x) * self.scale
        base_y = self.height - self.top - (y - self.min_y) * self.scale
        center_x = self.width / 2
        center_y = self.height / 2
        screen_x = center_x + self.pan_x + (base_x - center_x) * self.zoom
        screen_y = center_y + self.pan_y + (base_y - center_y) * self.zoom
        return (round(screen_x), round(screen_y))

    def zoom_in(self) -> None:
        """Zoom in (maximum x5)."""
        self.zoom = min(5.0, self.zoom * 1.2)

    def zoom_out(self) -> None:
        """Zoom out (minimum x0.25)."""
        self.zoom = max(0.25, self.zoom / 1.2)

    def move(self, move_x: int, move_y: int) -> None:
        """Slide the map by some pixels."""
        self.pan_x += move_x
        self.pan_y += move_y


class Viewer:
    """The Pygame window: events, timing and drawing."""

    def __init__(
        self, map_data: MapData, replay: Replay, size: tuple[int, int]
    ) -> None:
        """Open the window and prepare the texts."""
        pygame.init()
        self.size = size
        self.screen = pygame.display.set_mode(size)
        pygame.display.set_caption("Fly-in - map")
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.clock = pygame.time.Clock()
        self.map_data = map_data
        self.replay = replay
        self.view = View(map_data, size)
        self.last_turn = len(replay.states) - 1
        self.turn_index = 0
        self.paused = False
        self.step_delay = 650
        self.time_since_step = 0
        self.dragging = False
        self.running = True
        self.point_labels: dict[str, pygame.Surface] = {}
        self.drone_labels: dict[str, pygame.Surface] = {}
        self._prepare_labels()

    def _prepare_labels(self) -> None:
        """Render each name once (faster than at every frame)."""
        for name in self.map_data.points:
            self.point_labels[name] = self.font.render(name, True, TEXT_COLOR)
        for name in self.replay.states[0]:
            self.drone_labels[name] = self.small_font.render(
                name, True, WHITE
            )

    def run(self) -> None:
        """Run the main loop for events, timing, and drawing."""
        try:
            while self.running:
                self._handle_events()
                self._update_turn()
                self._draw()
        finally:
            pygame.quit()

    def _handle_events(self) -> None:
        """Handle the mouse (right button drag) and the keyboard."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                self.dragging = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
                self.dragging = False
            elif event.type == pygame.MOUSEMOTION and self.dragging:
                self.view.move(event.rel[0], event.rel[1])
            elif event.type == pygame.KEYDOWN:
                self._on_key(event.key)

    def _on_key(self, key: int) -> None:
        """Handle the keys that control the replay."""
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_SPACE:
            self.paused = not self.paused
            self.time_since_step = 0
        elif key == pygame.K_r:
            self.turn_index = 0
            self.paused = False
            self.time_since_step = 0
        elif key == pygame.K_LEFT:
            self._go_to_turn(self.turn_index - 1)
        elif key == pygame.K_RIGHT:
            self._go_to_turn(self.turn_index + 1)
        else:
            self._on_view_key(key)

    def _on_view_key(self, key: int) -> None:
        """Handle the keys for the zoom and the speed."""
        if key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
            self.view.zoom_in()
        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.view.zoom_out()
        elif key == pygame.K_UP:
            self.step_delay = max(100, self.step_delay - 100)
        elif key == pygame.K_DOWN:
            self.step_delay = min(2000, self.step_delay + 100)

    def _go_to_turn(self, turn: int) -> None:
        """Show a turn (kept between 0 and the last one) and pause."""
        self.turn_index = max(0, min(self.last_turn, turn))
        self.paused = True
        self.time_since_step = 0

    def _update_turn(self) -> None:
        """Go to the next turn when the delay is over."""
        elapsed = self.clock.tick(60)
        if self.paused or self.turn_index >= self.last_turn:
            return
        self.time_since_step += elapsed
        if self.time_since_step >= self.step_delay:
            self.turn_index += 1
            self.time_since_step = 0
            if self.turn_index == self.last_turn:
                self.paused = True

    def _draw(self) -> None:
        """Draw one complete image."""
        self.screen.fill(BACKGROUND)
        self._draw_connections()
        self._draw_points()
        self._draw_drones()
        self._draw_help()
        pygame.display.flip()

    def _point_position(self, name: str) -> tuple[int, int]:
        """Return the pixel of a point."""
        point = self.map_data.points[name]
        return self.view.to_screen(point.x, point.y)

    def _draw_connections(self) -> None:
        """Draw a gray line for each connection."""
        for first, second in self.map_data.connections:
            pygame.draw.line(
                self.screen,
                LINE_COLOR,
                self._point_position(first),
                self._point_position(second),
                3,
            )

    @staticmethod
    def _point_color(point: Point) -> Color:
        """Return the color asked by the user, or one chosen by the kind."""
        if point.color is not None:
            if point.color.lower() == "rainbow":
                return Viewer._rainbow_color(pygame.time.get_ticks())
            try:
                color = pygame.Color(point.color)
                return (color.r, color.g, color.b)
            except ValueError:
                pass
        if point.kind == "start":
            return START_COLOR
        if point.kind == "end":
            return END_COLOR
        return DEFAULT_POINT_COLOR

    @staticmethod
    def _rainbow_color(elapsed_ms: int) -> Color:
        """Convert a cycling rainbow hue into an RGB color."""
        hue = (elapsed_ms % 3600) / 3600
        red, green, blue = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        return (round(red * 255), round(green * 255), round(blue * 255))

    def _draw_points(self) -> None:
        """Draw a circle and the name of each point."""
        for name, point in self.map_data.points.items():
            position = self._point_position(name)
            pygame.draw.circle(
                self.screen, self._point_color(point), position, 12
            )
            label = self.point_labels[name]
            self.screen.blit(label, (position[0] + 15, position[1] - 10))

    def _group_drones(self) -> dict[Position, list[str]]:
        """Group the drones that are at the same place."""
        groups: dict[Position, list[str]] = {}
        state = self.replay.states[self.turn_index]
        for name, coordinates in state.items():
            if coordinates not in groups:
                groups[coordinates] = []
            groups[coordinates].append(name)
        return groups

    def _draw_drones(self) -> None:
        """Draw the drones, side by side when they share a place."""
        groups = self._group_drones()
        for coordinates, names in groups.items():
            center_x, center_y = self.view.to_screen(
                coordinates[0], coordinates[1]
            )
            for index, name in enumerate(sorted(names)):
                column = index % 3
                row = index // 3
                position = (center_x + (column - 1) * 15, center_y + row * 15)
                self._draw_one_drone(name, position)

    def _draw_one_drone(self, name: str, position: tuple[int, int]) -> None:
        """Draw one colored circle with the name of the drone inside."""
        number = int(name[1:])
        color = DRONE_COLORS[(number - 1) % len(DRONE_COLORS)]
        pygame.draw.circle(self.screen, color, position, 10)
        label = self.drone_labels[name]
        self.screen.blit(
            label,
            (
                position[0] - label.get_width() // 2,
                position[1] - label.get_height() // 2,
            ),
        )

    def _draw_help(self) -> None:
        """Draw the status, the speed and the list of keys."""
        if self.paused:
            status = "PAUSE"
        else:
            status = "LECTURE"
        turn_text = f"{status}  Tour {self.turn_index}/{self.last_turn}"
        speed_text = (
            f"Vitesse: {1000 / self.step_delay:.1f} tours/s  (haut/bas)"
        )
        keys_text = (
            "<-/-> tours   Espace pause   R restart   +/- zoom   "
            "Clic droit glisser: deplacer"
        )
        self._write(turn_text, self.font, TEXT_COLOR, (WINDOW_PADDING, 15))
        self._write(
            speed_text,
            self.small_font,
            HELP_COLOR,
            (WINDOW_PADDING, 38),
        )
        self._write(
            keys_text,
            self.small_font,
            HELP_COLOR,
            (WINDOW_PADDING, self.size[1] - 30),
        )

    def _write(
        self,
        text: str,
        font: pygame.font.Font,
        color: Color,
        position: tuple[int, int],
    ) -> None:
        """Write a text on the screen."""
        self.screen.blit(font.render(text, True, color), position)
