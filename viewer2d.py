"""Simple 2D map and drone replay data API.

Usage (same functions as the 3D viewer):

    init(max_x, max_y)
    place_point(name, x, y)
    place_connect([["a", "b"], ...])
    show(moves)
"""

Position = tuple[float, float]
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
    from viewer2d_ui import Viewer

    Viewer(_map_data, replay, size).run()
