import viewer3d

def init_and_show_visualizer(all_information: dict[str, dict[str, str | int]], list_connection: list[list[str | int]], moves=None) -> None:
    if not all_information:
        return

    max_x = max(data["x"] for data in all_information.values())
    max_y = max(data["y"] for data in all_information.values())

    viewer3d.init(max_x + 1, max_y + 1)

    for name, data in all_information.items():
        kind = data.get("type", "hub")
        kwargs = {}

        if kind == "start_hub":
            kwargs["kind"] = "start"
        elif kind == "end_hub":
            kwargs["kind"] = "end"

        if "zone" in data:
            kwargs["zone_type"] = data["zone"]

        if "color" in data and data["color"]:
            kwargs["color"] = data["color"]

        if "max_drones" in data:
            kwargs["max_drones"] = data["max_drones"]

        viewer3d.place_point(name, data["x"], data["y"], **kwargs)
    
    # Si viewer3d.place_connect attend des listes de paires [hub1, hub2], 
    # on peut lui passer une vue filtrée ou s'adapter :
    connections_for_viewer = [[conn[0], conn[1]] for conn in list_connection]
    viewer3d.place_connect(connections_for_viewer)

    if moves is None:
        moves = []
    viewer3d.show(moves)
