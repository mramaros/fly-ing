"""Validate a map, compute drone paths, and launch the visualizer."""

import importlib
import sys


def main() -> None:
    """Run the map solver after checking its visualization dependency."""
    try:
        importlib.import_module("pygame")
    except ImportError:
        raise SystemExit(
            "Error: pygame is required. Install it with 'pip install pygame'."
        ) from None

    from constraint_parsing import (
        check_in_connect_and_file,
        check_number_validate,
        connection_parsing,
        constraining_value,
        raise_ERROR,
    )
    from graphical_design import init_and_show_visualizer
    from manage_path import manager_path
    import parsing

    if len(sys.argv) != 2:
        raise_ERROR("usage: python3 main.py <maps>")

    find_file = sys.argv[1]
    brute_content = parsing.brute_info(find_file)

    clean_content = parsing.to_list(brute_content)
    all_information: dict[str, dict[str, str | int]] = (
        parsing.parsing_hub_and_connection(clean_content)
    )

    nb_brute: str = ""
    for i in clean_content:
        if i.startswith("nb_drones:"):
            nb_brute = i.replace(":", "")

    number_of_drones = parsing.take_nb_of_drones(nb_brute)
    if number_of_drones >= 2000:
        raise_ERROR("Sorry, 2000 is my maximal capacity for visualization")
    check_number_validate(clean_content, number_of_drones)
    parsing.check_x_coordinate(all_information)

    list_connection: list[list[str | int]] = connection_parsing(clean_content)
    check_in_connect_and_file(list_connection, all_information)
    constraining_value(all_information)

    generale_move = manager_path(
        all_information, list_connection, number_of_drones
    )
    for turn_moves in generale_move:
        print(turn_moves)

    init_and_show_visualizer(all_information, list_connection, generale_move)


if __name__ == "__main__":
    main()
