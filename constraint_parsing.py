"""Validation helpers for parsed flying-network configuration content."""

import sys
from typing import NoReturn


def raise_ERROR(message: str) -> NoReturn:
    """Print a configuration error and terminate the program.

    Args:
        message: The reason the configuration is invalid.

    """
    print(f"[ERROR] : Config not valid.\n{message}", file=sys.stderr)
    sys.exit(1)


def check_number_validate(clean_content: list[str], nb_drones: int) -> None:
    """Validate hub counts and the number of drones.

    Args:
        clean_content: Cleaned lines from the configuration file.
        nb_drones: Requested drone count.

    """
    number_start = sum(
        1
        for line in clean_content
        if line.split()
        and line.split()[0].removesuffix(":") == "start_hub"
    )
    number_end = sum(
        1
        for line in clean_content
        if line.split()
        and line.split()[0].removesuffix(":") == "end_hub"
    )
    if number_start != 1 or number_end != 1:
        raise_ERROR("See in hub configuration")
    if nb_drones <= 0:
        raise_ERROR("number of drones must > 0")


def connection_parsing(clean_content: list[str]) -> list[list[str | int]]:
    """Parse and validate connection entries.

    Args:
        clean_content: Cleaned lines from the configuration file.

    Returns:
        A list containing hub names and their maximum link capacity.

    """
    list_connection: list[list[str | int]] = []
    seen_connection = set()
    for line in clean_content:
        if line.startswith("connection:"):
            parts = line.split()
            if len(parts) < 2:
                raise_ERROR("Invalide connection format")

            hubs = parts[1].split("-")
            if len(hubs) != 2:
                raise_ERROR("Invalide connection format")

            hubs1, hubs2 = hubs[0].strip(), hubs[1].strip()

            connect_tuple = tuple(sorted([hubs1, hubs2]))

            if connect_tuple in seen_connection:
                raise_ERROR(
                    f"Duplicate connection found between '{hubs1}'"
                    f" and '{hubs2}'"
                )

            seen_connection.add(connect_tuple)

            max_link_capacity = 1
            v = "1"
            for part in parts[2:]:
                if "max_link_capacity=" in part:
                    clean_part = part.replace("[", "").replace("]", "")
                    if "=" in clean_part:
                        k, v = clean_part.split("=", 1)
                        if k == "max_link_capacity":
                            try:
                                max_link_capacity = int(v)
                                if max_link_capacity <= 0:
                                    raise_ERROR(
                                        "max_link_capacity must be a "
                                        "positive integer"
                                    )
                            except ValueError:
                                raise_ERROR(
                                    "Invalid max_link_capacity value"
                                )

            list_connection.append([hubs1, hubs2, max_link_capacity])

    return list_connection


def check_in_connect_and_file(
    connection: list[list[str | int]],
    all_hub: dict[str, dict[str, str | int]],
) -> None:
    """Verify that every connection references an existing hub.

    Args:
        connection: Connections containing hub names and capacities.
        all_hub: Hub configuration indexed by hub name.

    """
    for conn in connection:
        hubs1, hubs2 = conn[0], conn[1]

        if hubs1 not in all_hub:
            raise_ERROR(f"Hub '{hubs1}' does not exist")

        if hubs2 not in all_hub:
            raise_ERROR(f"Hub '{hubs2}' does not exist")


def constraining_value(all_hub: dict[str, dict[str, str | int]]) -> None:
    """Validate hub zones and maximum drone values.

    Args:
        all_hub: Hub configuration indexed by hub name.

    """
    for name, value in all_hub.items():
        zone_content: int | str | None = value.get("zone")
        valide_content = ("normal", "restricted", "blocked", "priority")
        if zone_content not in valide_content:
            raise_ERROR(f"Invalid zone type for hub '{name}'")

        max_drone_zone_value: int | str | None = value.get("max_drones")
        if max_drone_zone_value is not None:
            try:
                if int(max_drone_zone_value) <= 0:
                    raise_ERROR(
                        f"max_drones must be positive for hub '{name}'"
                    )
            except ValueError:
                raise_ERROR(f"Invalid max_drones value for hub '{name}'")
