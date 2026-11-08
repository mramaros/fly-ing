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


def manager_path(all_information: dict[str, dict[str, str | int]], list_connection: list[str]) -> None:
    graph = connectionManager()

    for name, data in all_information.items():
        x = int(data.get("x", 0))
        y = int(data.get("y", 0))
        type_zone = data.get("zone")

        graph.zone[name] = Zone(name=name, x=x, y=y, priority=type_zone)

    for connection in list_connection:
        if len(connection) >= 2:
            capacity = 1
            hubb1, hubb2 = connection[0], connection[1]
            if hubb1 in graph.zone and hubb2 in graph.zone:
                zone_a = graph.zone[hubb1]
                zone_b = graph.zone[hubb2]
                print(zone_a.name)
                graph.add_connection(zone_a, zone_b, capacity)
                graph.show(zone_a.name)


