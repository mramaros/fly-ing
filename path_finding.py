import heapq


class Zone:
    def __init__(self, name: str, x: int, y: int, priority: str | int | None = "normal") -> None:
        self.name = name
        self.x = x
        self.y = y
        self.zone_type = priority


class connectionManager:
    def __init__(self) -> None:
        self.zone: dict[str, Zone] = {}
        self.connection: dict[str, list[tuple[Zone, int]]] = {}

    def add_connection(self, zone_a: Zone, zone_b: Zone, capacity: int) -> None:
        self.connection.setdefault(zone_a.name, []).append((zone_b, capacity))
        self.connection.setdefault(zone_b.name, []).append((zone_a, capacity))

    def show(self, zone_name: str) -> None:
        if zone_name in self.connection:
            voisins_info = [f"{z.name} (capacité: {cap})" for z, cap in self.connection[zone_name]]
            print(f"Connexions de {zone_name} : {voisins_info}")

    def dikstra_path(self, start_hub: str, end_hub: str) -> list[list[str]]:
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
                    heapq.heappush(queue, (new_cost, path + [neighbor_name]))

        if not shortest_paths:
            return []

        # Keep near-optimal routes for load balancing, but cap the search.
        near_optimal: list[list[str]] = []
        stack: list[tuple[str, list[str], int]] = [(start_hub, [start_hub], 0)]
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
                    stack.append((neighbor_name, path + [neighbor_name], new_cost))

        near_optimal.sort(key=lambda route: (len(route), route))
        if near_optimal:
            return near_optimal
        return shortest_paths


def manager_path(
    all_information: dict[str, dict[str, str | int]],
    list_connection: list[list[str | int]],
    nb_drones: int,
) -> list[str]:
    graph = connectionManager()

    start_hub = ""
    end_hub = ""
    for name, data in all_information.items():
        x = int(data.get("x", 0))
        y = int(data.get("y", 0))
        type_zone = data.get("zone")
        zone_car = data.get("type")

        if zone_car == "start_hub":
            start_hub = name

        if zone_car == "end_hub":
            end_hub = name

        graph.zone[name] = Zone(name=name, x=x, y=y, priority=type_zone)

    for connection in list_connection:
        if len(connection) >= 2:
            capacity = int(connection[2]) if len(connection) >= 3 else 1
            hubb1, hubb2 = connection[0], connection[1]
            if hubb1 in graph.zone and hubb2 in graph.zone:
                zone_a = graph.zone[hubb1]
                zone_b = graph.zone[hubb2]
                graph.add_connection(zone_a, zone_b, capacity)

    path = graph.dikstra_path(start_hub, end_hub)
    move = manage_drones(path, nb_drones, all_information, list_connection)

    return move


def manage_drones(list_path: list[list[str]], nb_drones: int, all_information: dict[str, dict[str, str | int]], list_connection: list[list[str | int]]) -> list[str]:
    if not list_path or nb_drones <= 0:
        return []

    zone_types: dict[str, str] = {}
    zone_capacities: dict[str, int] = {}
    start_hub = ""
    end_hub = ""

    for name, data in all_information.items():
        zone_types[name] = str(data.get("zone", "normal"))
        if data.get("type") == "start_hub":
            start_hub = name
            zone_capacities[name] = nb_drones
        elif data.get("type") == "end_hub":
            end_hub = name
            zone_capacities[name] = nb_drones
        else:
            try:
                zone_capacities[name] = max(0, int(data.get("max_drones", 1)))
            except (TypeError, ValueError):
                zone_capacities[name] = 1

    connection_names: dict[tuple[str, str], str] = {}
    connection_capacities: dict[tuple[str, str], int] = {}
    for conn in list_connection:
        z1, z2 = str(conn[0]), str(conn[1])
        try:
            capacity = max(1, int(conn[2]) if len(conn) >= 3 else 1)
        except (TypeError, ValueError):
            capacity = 1

        connection_names[(z1, z2)] = f"{z1}-{z2}"
        connection_names[(z2, z1)] = f"{z1}-{z2}"
        connection_capacities[(z1, z2)] = capacity
        connection_capacities[(z2, z1)] = capacity

    # Round-robin assignment balances all near-optimal routes.
    drone_route = {
        f"D{i}": (i - 1) % len(list_path)
        for i in range(1, nb_drones + 1)
    }
    drone_steps = {f"D{i}": 0 for i in range(1, nb_drones + 1)}
    drone_zone = {f"D{i}": start_hub for i in range(1, nb_drones + 1)}

    restricted_transit: dict[str, dict[str, str]] = {}
    link_usage: dict[tuple[str, str], int] = {}
    move_history: list[str] = []

    for _ in range(1000):
        if all(zone == end_hub for zone in drone_zone.values()):
            break

        zone_occupancy: dict[str, int] = {}
        for zone in drone_zone.values():
            zone_occupancy[zone] = zone_occupancy.get(zone, 0) + 1

        turn_moves: list[str] = []
        turn_link_usage: dict[tuple[str, str], int] = {}

        # Restricted drones finish only when their target zone has room.
        for d_name in list(restricted_transit):
            transit = restricted_transit[d_name]
            source = transit["source"]
            target = transit["target"]

            if zone_occupancy.get(target, 0) >= zone_capacities.get(target, 1):
                continue

            link_key = (source, target)
            if link_key not in connection_capacities:
                link_key = (target, source)

            link_usage[link_key] = max(0, link_usage.get(link_key, 0) - 1)
            zone_occupancy[target] = zone_occupancy.get(target, 0) + 1
            drone_zone[d_name] = target
            restricted_transit.pop(d_name)
            turn_moves.append(f"{d_name}-{target}")

        # Most advanced drones first prevent bottleneck starvation.
        ordered_drones = sorted(
            (
                d_name for d_name in drone_zone
                if d_name not in restricted_transit
                and drone_zone[d_name] != end_hub
            ),
            key=lambda d_name: drone_steps[d_name],
            reverse=True,
        )

        for d_name in ordered_drones:
            current = drone_zone[d_name]

            candidates: list[tuple[int, int, int, str, int]] = []
            assigned_route = drone_route[d_name]

            route_indexes = [assigned_route]
            route_indexes.extend(i for i in range(len(list_path)) if i != assigned_route)

            for route_index in route_indexes:
                route = list_path[route_index]
                try:
                    position = route.index(current)
                except ValueError:
                    continue

                if position >= len(route) - 1:
                    continue

                next_zone = route[position + 1]
                if zone_types.get(next_zone) == "blocked":
                    continue

                zone_limit = zone_capacities.get(next_zone, 1)
                zone_used = zone_occupancy.get(next_zone, 0)
                if next_zone != end_hub and zone_used >= zone_limit:
                    continue

                link_key = (current, next_zone)
                if link_key not in connection_capacities:
                    link_key = (next_zone, current)

                link_limit = connection_capacities.get(link_key, 1)
                link_used = link_usage.get(link_key, 0) + turn_link_usage.get(link_key, 0)
                if link_used >= link_limit:
                    continue

                remaining = len(route) - position - 1
                priority_bonus = 0 if zone_types.get(next_zone) == "priority" else 1
                free_capacity = zone_limit - zone_used
                candidates.append((remaining, priority_bonus, -free_capacity, next_zone, route_index))

            if not candidates:
                continue

            candidates.sort()
            next_zone = candidates[0][3]
            drone_route[d_name] = candidates[0][4]

            link_key = (current, next_zone)
            if link_key not in connection_capacities:
                link_key = (next_zone, current)

            turn_link_usage[link_key] = turn_link_usage.get(link_key, 0) + 1

            if zone_types.get(next_zone) == "restricted":
                link_usage[link_key] = link_usage.get(link_key, 0) + 1
                zone_occupancy[current] = max(0, zone_occupancy.get(current, 1) - 1)

                connection_name = connection_names.get((current, next_zone), f"{current}-{next_zone}")
                turn_moves.append(f"{d_name}-{connection_name}")
                restricted_transit[d_name] = {"source": current, "target": next_zone}
                drone_steps[d_name] += 1
            else:
                zone_occupancy[current] = max(0, zone_occupancy.get(current, 1) - 1)
                zone_occupancy[next_zone] = zone_occupancy.get(next_zone, 0) + 1
                drone_zone[d_name] = next_zone
                drone_steps[d_name] += 1
                turn_moves.append(f"{d_name}-{next_zone}")

        if turn_moves:
            move_history.append(" ".join(turn_moves))

    return move_history