import viewer3d

def init_and_show_visualizer(all_information: dict[str, dict[str, str | int]], list_connection: list[list[str]], moves=None) -> None:
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

        if "max_drones" in data:
            kwargs["max_drones"] = data["max_drones"]

        viewer3d.place_point(name, data["x"], data["y"], **kwargs)
    viewer3d.place_connect(list_connection)

    if moves is None:
        moves = []
    viewer3d.show(moves)
