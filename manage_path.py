"""Build the routing graph and coordinate drone movements."""

from algo_solver import ConnectionManager, Zone
from manage_drones import manage_drones


def manager_path(
    all_information: dict[str, dict[str, str | int]],
    list_connection: list[list[str | int]],
    nb_drones: int,
) -> list[str]:
    """Build the graph, find routes and generate drone movements.

    Args:
        all_information: Parsed hub configuration.
        list_connection: Parsed connection configuration.
        nb_drones: Number of drones to dispatch.

    Returns:
        One movement string for each simulation turn.

    """
    graph = ConnectionManager()

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
                zone_a = graph.zone[str(hubb1)]
                zone_b = graph.zone[str(hubb2)]
                graph.add_connection(zone_a, zone_b, capacity)

    path = graph.dijkstra_path(start_hub, end_hub)
    return manage_drones(path, nb_drones, all_information, list_connection)
