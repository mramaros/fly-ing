"""Graph model and shortest-path solving utilities."""

import heapq


class Zone:
    """Represent a graph zone and its coordinates.

    Args:
        name: Name of the zone.
        x: Horizontal coordinate of the zone.
        y: Vertical coordinate of the zone.
        priority: Zone behavior and priority.

    """

    def __init__(
        self,
        name: str,
        x: int,
        y: int,
        priority: str | int | None = "normal",
    ) -> None:
        """Initialize a zone."""
        self.name = name
        self.x = x
        self.y = y
        self.zone_type = priority


class ConnectionManager:
    """Store zones and their connections and find routes between them."""

    def __init__(self) -> None:
        """Initialize an empty graph."""
        self.zone: dict[str, Zone] = {}
        self.connection: dict[str, list[tuple[Zone, int]]] = {}

    def add_connection(
        self,
        zone_a: Zone,
        zone_b: Zone,
        capacity: int,
    ) -> None:
        """Add a bidirectional connection between two zones.

        Args:
            zone_a: First zone.
            zone_b: Second zone.
            capacity: Link capacity.

        """
        self.connection.setdefault(zone_a.name, []).append((zone_b, capacity))
        self.connection.setdefault(zone_b.name, []).append((zone_a, capacity))

    def dijkstra_path(self, start_hub: str, end_hub: str) -> list[list[str]]:
        """Find minimum-cost and near-optimal routes between two zones.

        Args:
            start_hub: Name of the starting zone.
            end_hub: Name of the destination zone.

        Returns:
            Shortest or near-optimal paths ordered for load balancing.

        """
        if start_hub not in self.zone or end_hub not in self.zone:
            return []

        queue: list[tuple[int, list[str]]] = [(0, [start_hub])]
        shortest_paths: list[list[str]] = []
        min_cost = float("inf")

        while queue:
            cost, path = heapq.heappop(queue)
            current_hub = path[-1]

            if cost > min_cost:
                continue

            if current_hub == end_hub:
                if cost < min_cost:
                    min_cost = cost
                    shortest_paths = [path]
                elif cost == min_cost and path not in shortest_paths:
                    shortest_paths.append(path)
                continue

            for neighbor_hub, _ in self.connection.get(current_hub, []):
                neighbor_name = neighbor_hub.name
                zone_type = neighbor_hub.zone_type

                if zone_type == "blocked" or neighbor_name in path:
                    continue

                new_cost = cost + (2 if zone_type == "restricted" else 1)
                if new_cost <= min_cost:
                    heapq.heappush(
                        queue,
                        (new_cost, path + [neighbor_name]),
                    )

        if not shortest_paths:
            return []

        near_optimal: list[list[str]] = []
        stack: list[tuple[str, list[str], int]] = [
            (start_hub, [start_hub], 0)
        ]
        max_cost = min_cost + 6

        while stack and len(near_optimal) < 100:
            zone, path, cost = stack.pop()
            if cost > max_cost:
                continue
            if zone == end_hub:
                if cost <= max_cost and path not in near_optimal:
                    near_optimal.append(path)
                continue

            for neighbor_hub, _ in self.connection.get(zone, []):
                neighbor_name = neighbor_hub.name
                zone_type = neighbor_hub.zone_type

                if zone_type == "blocked" or neighbor_name in path:
                    continue

                new_cost = cost + (2 if zone_type == "restricted" else 1)
                if new_cost <= max_cost:
                    stack.append(
                        (neighbor_name, path + [neighbor_name], new_cost)
                    )

        near_optimal.sort(
            key=lambda route: (
                sum(
                    2 if self.zone[name].zone_type == "restricted" else 1
                    for name in route[1:]
                ),
                -sum(
                    self.zone[name].zone_type == "priority"
                    for name in route[1:]
                ),
                len(route),
                route,
            )
        )
        if near_optimal:
            return near_optimal
        return shortest_paths
