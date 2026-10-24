import sys
from parsing import parsing_hub_and_connection, take_nb_of_drones, to_list, brute_info


if __name__ == "__main__":
    find_file = sys.argv[1]
    brute_content = brute_info(find_file)

    clean_content = to_list(brute_content)
    all_information: dict[str, dict[str, str | int]] = parsing_hub_and_connection(clean_content)

    nb_brute: str = ""
    for i in clean_content:
        if i.startswith("nb_drones:"):
            nb_brute: str = i.replace(":", "")
    number_of_drones = take_nb_of_drones(nb_brute)
    print(all_information)
