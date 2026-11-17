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

    def dikstra_path(self, start_hub: str, end_hub: str) -> list[str]:
        if start_hub not in self.zone or end_hub not in self.zone:
            return []

        pq = [(0, start_hub, [start_hub])]
        visited = set()
        while pq:
            cost, current_hub, path = heapq.heappop(pq)
            if current_hub == end_hub:
                return path

            if current_hub in visited:
                continue
            visited.add(current_hub)

            for neighbor_hub, _ in self.connection.get(current_hub, []):
                neighbor_name = neighbor_hub.name
                if neighbor_name not in visited:
                    zone_type = neighbor_hub.zone_type
                    move_cost = 2 if zone_type == "restricted" else 1

                    if zone_type == "blocked":
                        continue

                    heapq.heappush(pq, (cost + move_cost, neighbor_name, path + [neighbor_name]))
        return []


def manager_path(all_information: dict[str, dict[str, str | int]], list_connection: list[str]) -> None:
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
            capacity = 1
            hubb1, hubb2 = connection[0], connection[1]
            if hubb1 in graph.zone and hubb2 in graph.zone:
                zone_a = graph.zone[hubb1]
                zone_b = graph.zone[hubb2]
                print(zone_a.name)
                graph.add_connection(zone_a, zone_b, capacity)
                graph.show(zone_a.name)

    path = graph.dikstra_path(start_hub, end_hub)
    print(f"\n\nchemin trouver: \n{path}\n\n")
