import sys
import number_parsing


def brute_info(file_destination: str) -> str:
    try:
        with open (file_destination, "r", encoding="utf-8") as info:
            content = info.read()
            return content
    except FileNotFoundError:
        print("FileNotFoundError")
    return ""

def print_tmp(list_pt: list[str]) -> None:
    for i in list_pt:
        print(i)

def to_list(content: str) -> list[str]:
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
            number_parsing.raise_ERROR("")

    return true_config

def in_key(key: list[str], line: str) -> bool:
    for i in key:
        if line.startswith(i):
            return True
    return False

def take_hub_list(list_brute: list[str]) -> dict[str, dict[str, int | str]]:
    dict_hub: dict[str, dict[str, str | int]] = {}
    for lists in list_brute:
        i = lists.split(" ")
        typed: str = i[0].replace(":", "")
        name = i[1]
        if name in dict_hub:
            number_parsing.raise_ERROR(f"Duplicate hub name found: '{name}'")
        if len(i) >= 3:
            color_val: str = ""
            zone: str = "normal"
            capacity: int = 1
            try:
                x = int(i[2])
                y = int(i[3])
                for part in i[4:]:
                    if "color=" in part or "zone" in part or "max_drones" in part:
                        clean_part = part.replace("[", "").replace("]", "")
                        if "=" in clean_part:
                            k, v = clean_part.split("=", 1)
                            if k == "color":
                                color_val = v
                            if k == "zone":
                                zone = v
                            if k == "max_drones":
                                try:
                                    capacity = int(v)
                                except Exception as e:
                                    number_parsing.raise_ERROR("")
                dict_hub[name] = {
                    "type" : typed,
                    "x" : x,
                    "y" : y,
                    "color" : color_val,
                    "zone" : zone,
                    "max_drones" : capacity
                }
            except Exception as e:
                print(f"[ERROR]: {e}")
        elif lists.startswith("nb_drones") or lists.startswith("connection"):
            if not 2 >= len(i) <= 3:
                number_parsing.raise_ERROR("")
            try:
                ...
            except Exception :
                ...
        else:
            number_parsing.raise_ERROR("")
    return dict_hub

def parsing_hub_and_connection(clean_content: list[str]) -> dict[str, dict[str, str | int]]:

    all_key: list[str] = ["nb_drones",
                          "start_hub",
                          "end_hub",
                          "hub",
                          "connection"
                          ]
    result: list[bool] = []
    for line in clean_content:
        result_bool = in_key(all_key, line)
        result.append(result_bool)
    if not all(result):
        print("Erreur : La configuration du fichier est invalide.", file=sys.stderr)
        sys.exit(1)

    dic_information: dict[str, dict[str, int | str]] = take_hub_list(clean_content)

    return dic_information

def take_nb_of_drones(part: str) -> int:
    line = part.split(" ")
    try:
        if len(line) == 2:
            return int(line[1])
    except Exception:
        print("Erreur : La configuration du fichier est invalide.", file=sys.stderr)
        sys.exit(1)
    return 0


def number_of(key: str, dic_information: dict[str, dict[str, int | str]]) -> int:
    number: int = 0
    for i in dic_information.values():
        if i.get("type") == key:
            number += 1
    return number


def check_x_coordinate(dic_information: dict[str, dict[str, int | str]]) -> None:
    seen_coordinate = set()
    for hub_name, hub_data in dic_information.items():
        coords = hub_data.get("x"), hub_data.get("y")

        if coords in seen_coordinate:
            number_parsing.raise_ERROR(f"Duplicate coordinates found at hub '{hub_name}': {coords}")
        seen_coordinate.add(coords)
