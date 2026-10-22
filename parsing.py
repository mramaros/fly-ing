import sys

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
            print("Erreur : La configuration du fichier est invalide.", file=sys.stderr)
            sys.exit(1)

    return true_config

def in_key(key: list[str], line: str) -> bool:
    for i in key:
        if line.startswith(i):
            return True
    return False


def take_information(list_clean: list[str], key_found: str) -> list[str]:
    key_content: list[str] = []
    for i in list_clean:
        if i.startswith(key_found):
            key_content = i.split(" ")
            return key_content
    return key_content

def parsing() -> None:
    find_file = sys.argv[1]
    brute_content = brute_info(find_file)

    clean_content = to_list(brute_content)

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

    print_tmp(clean_content)
    print_tmp(take_information(clean_content, "hub"))
