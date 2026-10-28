"""Build the simple-fork map with the 3D API and replay a solution."""

import viewer3d

MOVES = [
    "D1-junction D2-junction",
    "D1-path_a D2-path_b D3-junction D4-junction",
    "D1-goal D2-goal D3-path_a D4-path_b",
    "D3-goal D4-goal",
]


def main() -> None:
    """Place the points and the connections, then open the window."""
    viewer3d.init(3, 2)
    viewer3d.place_point("start", 0, 1, kind="start", color="green")
    viewer3d.place_point("junction", 1, 1, color="yellow", max_drones=2)
    viewer3d.place_point("path_a", 2, 2, color="blue")
    viewer3d.place_point("path_b", 2, 0, color="blue")
    viewer3d.place_point("goal", 3, 1, kind="end", color="red")
    viewer3d.place_connect([
        ["start", "junction", "2"],
        ["junction", "path_a"],
        ["junction", "path_b"],
        ["path_a", "goal"],
        ["path_b", "goal"],
    ])
    viewer3d.show(MOVES, nb_drones=4)


if __name__ == "__main__":
    main()
