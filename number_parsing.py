import sys

def raise_ERROR(message: str):
    print(f"[ERROR] : Config not valid.\n{message}", file=sys.stderr)
    sys.exit(1)

def check_number_validate(clean_content: list[str]) -> None:
    number_start = sum(1 for line in clean_content if line.startswith("start_hub"))
    number_end = sum(1 for line in clean_content if line.startswith("end_hub"))
    if number_start != 1 or number_end != 1:
        raise_ERROR("See in hub configuration")


def connection_parsing(clean_content: list[str]) -> list[list[str]]:
    list_connection: list[list[str]] = []
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
                raise_ERROR(f"Duplicate connection found between '{hubs1}' and '{hubs2}'")

            seen_connection.add(connect_tuple)
            list_connection.append([hubs1, hubs2])

    return list_connection

def check_in_connect_and_file(connection: list[list[str]], all_hub: dict[str, dict[str, str | int]]) -> None:
    for conn in connection:
        hubs1, hubs2 = conn

        if hubs1 not in all_hub:
            raise_ERROR(f"{hubs1} not in your hub")

        if hubs2 not in all_hub:
            raise_ERROR(f"{hubs1} not in your hub")
