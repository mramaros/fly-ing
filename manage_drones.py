"""Drone dispatch and turn-by-turn movement management."""


def manage_drones(
    list_path: list[list[str]],
    nb_drones: int,
    all_information: dict[str, dict[str, str | int]],
    list_connection: list[list[str | int]],
) -> list[str]:
    """Move drones while respecting zone and link capacities.

    Args:
        list_path: Candidate routes from the solver.
        nb_drones: Number of drones to dispatch.
        all_information: Hub configuration data.
        list_connection: Connection and capacity data.

    Returns:
        Movement instructions, one list item per turn.

    """
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
                zone_capacities[name] = int(data.get("max_drones", 1))
            except (TypeError, ValueError):
                zone_capacities[name] = 1

    connection_names: dict[tuple[str, str], str] = {}
    connection_capacities: dict[tuple[str, str], int] = {}
    for conn in list_connection:
        z1, z2 = str(conn[0]), str(conn[1])
        try:
            capacity = int(conn[2]) if len(conn) >= 3 else 1
        except (TypeError, ValueError):
            capacity = 1

        connection_names[(z1, z2)] = f"{z1}-{z2}"
        connection_names[(z2, z1)] = f"{z1}-{z2}"
        connection_capacities[(z1, z2)] = capacity
        connection_capacities[(z2, z1)] = capacity

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
        for drone, zone in drone_zone.items():
            if drone in restricted_transit:
                continue
            zone_occupancy[zone] = zone_occupancy.get(zone, 0) + 1

        turn_moves: list[str] = []
        turn_link_usage: dict[tuple[str, str], int] = {}

        moved_drones: set[str] = set()

        for d_name in list(restricted_transit):
            transit = restricted_transit[d_name]
            source = transit["source"]
            target = transit["target"]

            if zone_occupancy.get(target, 0) >= zone_capacities.get(target, 1):
                continue

            link_key = (source, target)
            if link_key not in connection_capacities:
                link_key = (target, source)

            link_usage[link_key] = max(
                0,
                link_usage.get(link_key, 0) - 1,
            )
            zone_occupancy[target] = zone_occupancy.get(target, 0) + 1
            drone_zone[d_name] = target
            restricted_transit.pop(d_name)
            moved_drones.add(d_name)
            turn_moves.append(f"{d_name}-{target}")

        ordered_drones = sorted(
            (
                d_name
                for d_name in drone_zone
                if d_name not in restricted_transit
                and d_name not in moved_drones
                and drone_zone[d_name] != end_hub
            ),
            key=lambda d_name: drone_steps[d_name],
            reverse=True,
        )

        for d_name in ordered_drones:
            current = drone_zone[d_name]

            candidates: list[tuple[int, int, int, int, str, int]] = []
            assigned_route = drone_route[d_name]

            route_indexes = [assigned_route]
            route_indexes.extend(
                i for i in range(len(list_path)) if i != assigned_route
            )

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
                link_used = (
                    link_usage.get(link_key, 0)
                    + turn_link_usage.get(link_key, 0)
                )
                if link_used >= link_limit:
                    continue

                remaining_zones = route[position + 1:]
                remaining_cost = sum(
                    2 if zone_types.get(zone) == "restricted" else 1
                    for zone in remaining_zones
                )
                remaining_priorities = sum(
                    zone_types.get(zone) == "priority"
                    for zone in remaining_zones
                )
                priority_bonus = (
                    0 if zone_types.get(next_zone) == "priority" else 1
                )
                free_capacity = zone_limit - zone_used
                candidates.append(
                    (
                        remaining_cost,
                        -remaining_priorities,
                        priority_bonus,
                        -free_capacity,
                        next_zone,
                        route_index,
                    )
                )

            if not candidates:
                continue

            candidates.sort()
            next_zone = candidates[0][4]
            drone_route[d_name] = candidates[0][5]

            link_key = (current, next_zone)
            if link_key not in connection_capacities:
                link_key = (next_zone, current)

            turn_link_usage[link_key] = (
                turn_link_usage.get(link_key, 0) + 1
            )

            if zone_types.get(next_zone) == "restricted":
                link_usage[link_key] = link_usage.get(link_key, 0) + 1
                zone_occupancy[current] = max(
                    0,
                    zone_occupancy.get(current, 1) - 1,
                )

                connection_name = connection_names.get(
                    (current, next_zone),
                    f"{current}-{next_zone}",
                )
                turn_moves.append(f"{d_name}-{connection_name}")
                restricted_transit[d_name] = {
                    "source": current,
                    "target": next_zone,
                }
                drone_steps[d_name] += 1
            else:
                zone_occupancy[current] = max(
                    0,
                    zone_occupancy.get(current, 1) - 1,
                )
                zone_occupancy[next_zone] = (
                    zone_occupancy.get(next_zone, 0) + 1
                )
                drone_zone[d_name] = next_zone
                drone_steps[d_name] += 1
                turn_moves.append(f"{d_name}-{next_zone}")

        if turn_moves:
            move_history.append(" ".join(turn_moves))

    return move_history
