import constraint_parsing


def brute_info(file_destination: str) -> str:
    """Read the content of the specified file and return it as a string.
    Args:
        file_destination: The path to the file to be read.
    Returns:
        The content of the file as a string.
    Raises:
        FileNotFoundError: If the specified file does not exist.
    """
    try:
        with open(file_destination, "r", encoding="utf-8") as info:
            return info.read()
    except FileNotFoundError:
        return ""


def to_list(content: str) -> list[str]:
    """Convert file content into cleaned lines.

    Args:
        content: Raw file content.

    Returns:
        A list of non-empty lines without comments.

    """
    list_clean: list[str] = content.splitlines()
    true_config: list[str] = []
    for tmp in list_clean:
        stripped_line = tmp.strip()
        if not stripped_line:
            continue
        if stripped_line.startswith("#"):
            continue
        i = 0
        while i < len(stripped_line):
            if stripped_line[i] == "#":
                break
            i += 1
        clean_line = stripped_line[:i].strip()
        if clean_line:
            true_config.append(clean_line)
    for tmp in true_config:
        occurence = 0
        for ch in tmp:
            if ch == ":":
                occurence += 1
        if occurence != 1:
            constraint_parsing.raise_ERROR("")

    return true_config


def in_key(key: list[str], line: str) -> bool:
    """Check if the first part of a line (before the colon) is in a list of keys.
    Args:
        key: A list of valid keys.
        line: A line from the configuration file.
    Returns:
        True if the first part of the line is in the list of keys, False otherwise.
    """
    parts = line.split()
    if not parts:
        return False

    line_key = parts[0].removesuffix(":")
    return line_key in key


def take_hub_list(list_brute: list[str]) -> dict[str, dict[str, int | str]]:
    """Parse the cleaned lines from the configuration file and extract hub information.
    Args:
        list_brute: A list of cleaned lines from the configuration file.
    Returns:
        A dictionary where each key is a hub name and the value is another dictionary containing hub attributes
        such as type, coordinates, color, zone, and maximum number of drones.
    Raises:
        ValueError: If the hub information is invalid or if there are duplicate hub names."""
    dict_hub: dict[str, dict[str, str | int]] = {}
    valid_hub_types = {"start_hub", "end_hub", "hub"}

    for line in list_brute:
        parts = line.split()
        if not parts:
            constraint_parsing.raise_ERROR("Empty configuration line")

        typed = parts[0].removesuffix(":")
        if typed in {"nb_drones", "connection"}:
            continue
        if typed not in valid_hub_types:
            constraint_parsing.raise_ERROR(
                f"Unknown configuration key: '{typed}'"
            )
        if len(parts) < 4:
            constraint_parsing.raise_ERROR(
                f"Invalid {typed} format: expected name x y"
            )

        name = parts[1]
        if name in dict_hub:
            constraint_parsing.raise_ERROR(
                f"Duplicate hub name found: '{name}'"
            )

        try:
            x = int(parts[2])
            y = int(parts[3])
        except ValueError:
            constraint_parsing.raise_ERROR(
                f"Invalid coordinates for hub '{name}'"
            )

        color_val = ""
        zone = "normal"
        capacity = 1
        for part in parts[4:]:
            clean_part = part.strip("[]")
            if "=" not in clean_part:
                continue

            key, value = clean_part.split("=", 1)
            if key == "color":
                color_val = value
            elif key == "zone":
                zone = value
            elif key == "max_drones":
                try:
                    capacity = int(value)
                except ValueError:
                    constraint_parsing.raise_ERROR(
                        f"Invalid max_drones value for hub '{name}'"
                    )

        dict_hub[name] = {
            "type": typed,
            "x": x,
            "y": y,
            "color": color_val,
            "zone": zone,
            "max_drones": capacity,
        }

    return dict_hub


def parsing_hub_and_connection(
    clean_content: list[str],
) -> dict[str, dict[str, str | int]]:
    """Parse the cleaned lines from the configuration file and extract hub information.
    Args:
        clean_content: A list of cleaned lines from the configuration file.
    Returns: A dictionary where each key is a hub name and the value
            is another dictionary containing hub attributes"""
    all_key: list[str] = [
        "nb_drones",
        "start_hub",
        "end_hub",
        "hub",
        "connection",
    ]
    result: list[bool] = []
    for line in clean_content:
        result_bool = in_key(all_key, line)
        result.append(result_bool)
    if not all(result):
        constraint_parsing.raise_ERROR(
            "La configuration du fichier est invalide."
        )

    dic_information: dict[str, dict[str, int | str]] = take_hub_list(
        clean_content
    )

    return dic_information


def take_nb_of_drones(part: str) -> int:
    """Extract the number of drones from a configuration line.
    Args:
        part: A line from the configuration file that specifies the number of drones.
    Returns:
        The number of drones specified in the line.
    """
    line = part.split()
    if len(line) != 2:
        constraint_parsing.raise_ERROR("Invalid nb_drones format")

    try:
        return int(line[1])
    except ValueError:
        constraint_parsing.raise_ERROR("Le nombre de drones est invalide.")


def number_of(
    key: str, dic_information: dict[str, dict[str, int | str]]
) -> int:
    """Count the number of hubs of a specific type in the hub information dictionary.
    Args:
        key: The type of hub to count (e.g., "start_hub", "end_hub").
        dic_information: A dictionary containing hub information.
    Returns:
        The count of hubs of the specified type.
    """
    number: int = 0
    for i in dic_information.values():
        if i.get("type") == key:
            number += 1
    return number


def check_x_coordinate(
    dic_information: dict[str, dict[str, int | str]],
) -> None:
    """Check for duplicate coordinates in the hub information dictionary.
    Args:
        dic_information: A dictionary containing hub information.
    Raises:
        ValueError: If duplicate coordinates are found in the hub information.
    """
    seen_coordinate = set()
    for hub_name, hub_data in dic_information.items():
        coords = hub_data.get("x"), hub_data.get("y")

        if coords in seen_coordinate:
            constraint_parsing.raise_ERROR(
                f"Duplicate coordinates found at hub '{hub_name}': {coords}"
            )
        seen_coordinate.add(coords)
