"""Simple 2D map and drone replay using Pygame.

Usage (same functions as the 3D viewer):

    init(max_x, max_y)
    place_point(name, x, y)
    place_connect([["a", "b"], ...])
    show(moves)
"""

import pygame

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
POINT_KINDS = ("hub", "start", "end")


class Point:
    """A named place of the map."""

    def __init__(
        self, name: str, x: int, y: int, kind: str, color: str | None
    ) -> None:
        """Store the name, the coordinates, the kind and the color."""
        self.name = name
        self.x = x
        self.y = y
        self.kind = kind
        self.color = color


class MapData:
    """The points and the connections given by the algorithm."""

    def __init__(self) -> None:
        """Create an empty map that still needs init()."""
        self.bounds: tuple[int, int] | None = None
        self.points: dict[str, Point] = {}
        self.connections: list[tuple[str, str]] = []

    def reset(self, max_x: int, max_y: int) -> None:
        """Prepare an empty map."""
        if max_x < 0 or max_y < 0:
            raise ValueError("max_x and max_y must be >= 0")
        self.bounds = (max_x, max_y)
        self.points = {}
        self.connections = []

    def check_ready(self) -> None:
        """Raise an error if init() was not called."""
        if self.bounds is None:
            raise RuntimeError("call init(max_x, max_y) first")

    def add_point(self, point: Point) -> None:
        """Add a point, refuse duplicates and unknown kinds."""
        if point.name in self.points:
            raise ValueError(f"duplicate point '{point.name}'")
        if point.kind not in POINT_KINDS:
            raise ValueError("kind must be 'hub', 'start' or 'end'")
        self.points[point.name] = point

    def add_connections(self, connections: list[list[str]]) -> None:
        """Add connections given as [name1, name2] (or with a capacity)."""
        for connection in connections:
            if len(connection) not in (2, 3):
                raise ValueError(f"bad connection {connection}: need [a, b]")
            first = connection[0]
            second = connection[1]
            if first not in self.points or second not in self.points:
                raise ValueError(f"unknown point in connection {connection}")
            self.connections.append((first, second))

    def start_name(self) -> str | None:
        """Return the name of the start point, or None if there is none."""
        for point in self.points.values():
            if point.kind == "start":
                return point.name
        return None


class Replay:
    """Position of every drone after each turn (in map coordinates)."""

    def __init__(
        self, map_data: MapData, moves: list[str], nb_drones: int
    ) -> None:
        """Build one state per turn from the lines given by the algorithm."""
        self.map_data = map_data
        self.positions: dict[str, Position] = {}
        self.states: list[dict[str, Position]] = []
        count = self._count_drones(moves, nb_drones)
        self._place_drones_on_start(count)
        self.states.append(dict(self.positions))
        for turn in moves:
            for token in turn.split():
                self._apply_token(token)
            self.states.append(dict(self.positions))

    @staticmethod
    def _count_drones(moves: list[str], nb_drones: int) -> int:
        """Return the biggest of nb_drones and the highest D<ID> found."""
        count = nb_drones
        for turn in moves:
            for token in turn.split():
                name = token.partition("-")[0]
                if name.startswith("D") and name[1:].isdigit():
                    count = max(count, int(name[1:]))
        return count

    def _place_drones_on_start(self, count: int) -> None:
        """Put D1 ... D<count> on the start point (nothing if no start)."""
        start_name = self.map_data.start_name()
        if start_name is None:
            return
        start = self.map_data.points[start_name]
        for number in range(1, count + 1):
            self.positions[f"D{number}"] = (float(start.x), float(start.y))

    def _apply_token(self, token: str) -> None:
        """Apply one move: D<ID>-<zone> or D<ID>-<zone1>-<zone2>."""
        drone, separator, destination = token.partition("-")
        if separator == "" or drone not in self.positions:
            return
        points = self.map_data.points
        if destination in points:
            target = points[destination]
            self.positions[drone] = (float(target.x), float(target.y))
            return
        ends = destination.split("-", 1)
        if len(ends) == 2 and ends[0] in points and ends[1] in points:
            source = points[ends[0]]
            target = points[ends[1]]
            middle_x = (source.x + target.x) / 2
            middle_y = (source.y + target.y) / 2
            self.positions[drone] = (middle_x, middle_y)


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
        """Main loop: events, time, drawing."""
        try:
            while self.running:
                self._handle_events()
                self._update_turn()
                self._draw()
        finally:
            pygame.quit()

    # ------------------------------------------------------------ events

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

    # -------------------------------------------------------------- time

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

    # ----------------------------------------------------------- drawing

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
        self._write(speed_text, self.small_font, HELP_COLOR,
                    (WINDOW_PADDING, 38))
        self._write(keys_text, self.small_font, HELP_COLOR,
                    (WINDOW_PADDING, self.size[1] - 30))

    def _write(
        self,
        text: str,
        font: pygame.font.Font,
        color: Color,
        position: tuple[int, int],
    ) -> None:
        """Write a text on the screen."""
        self.screen.blit(font.render(text, True, color), position)


# The data given by the algorithm is kept here between the calls below.
_map_data = MapData()


def init(max_x: int, max_y: int) -> None:
    """Prepare an empty map."""
    _map_data.reset(max_x, max_y)


def place_point(
    name: str,
    x: int,
    y: int,
    *,
    kind: str = "hub",
    zone_type: str = "normal",
    color: str | None = None,
    max_drones: int = 1,
) -> None:
    """Add a named point at the given coordinates.

    zone_type and max_drones are accepted to keep the same call as the 3D
    viewer, but the 2D viewer does not draw them.
    """
    _map_data.check_ready()
    _map_data.add_point(Point(name, x, y, kind, color))


def place_connect(list_connection: list[list[str]]) -> None:
    """Add connections as pairs of point names."""
    _map_data.check_ready()
    _map_data.add_connections(list_connection)


def show(
    moves: list[str] | None = None,
    nb_drones: int = 0,
    size: tuple[int, int] = (900, 600),
) -> None:
    """Display the map and replay drones with keyboard controls."""
    _map_data.check_ready()
    if moves is None:
        moves = []
    replay = Replay(_map_data, moves, nb_drones)
    Viewer(_map_data, replay, size).run()
