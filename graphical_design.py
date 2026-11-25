from typing import Any

import viewer2d


def init_and_show_visualizer(
    all_information: dict[str, dict[str, str | int]],
    list_connection: list[list[str | int]],
    moves: list[str] | None = None,
) -> None:
    """Initialize the visualizer and display configuration data.

    Args:
        all_information: Hub coordinates and attributes.
        list_connection: Hub connections and maximum link capacities.
        moves: Optional movement list displayed in the visualizer.

    """
    if not all_information:
        return

    max_x: int = max(int(data["x"]) for data in all_information.values())
    max_y: int = max(int(data["y"]) for data in all_information.values())

    viewer2d.init(max_x + 1, max_y + 1)

    for name, data in all_information.items():
        kind = str(data.get("type", "hub"))
        kwargs: dict[str, Any] = {}

        if kind == "start_hub":
            kwargs["kind"] = "start"
        elif kind == "end_hub":
            kwargs["kind"] = "end"

        if "zone" in data:
            kwargs["zone_type"] = str(data["zone"])

        if "color" in data and data["color"]:
            kwargs["color"] = str(data["color"])

        if "max_drones" in data:
            kwargs["max_drones"] = int(data["max_drones"])

        viewer2d.place_point(name, int(data["x"]), int(data["y"]), **kwargs)

    connections_for_viewer = [
        [str(conn[0]), str(conn[1])] for conn in list_connection
    ]
    viewer2d.place_connect(connections_for_viewer)

    if moves is None:
        moves = []
    viewer2d.show(moves)
