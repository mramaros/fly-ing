import sys
import parsing
from number_parsing import check_in_connect_and_file, check_number_validate, connection_parsing
import pprint
from graphical_design import init_and_show_visualizer

if __name__ == "__main__":
    find_file = sys.argv[1]
    brute_content = parsing.brute_info(find_file)

    clean_content = parsing.to_list(brute_content)
    all_information: dict[str, dict[str, str | int]] = parsing.parsing_hub_and_connection(clean_content)

    nb_brute: str = ""
    for i in clean_content:
        if i.startswith("nb_drones:"):
            nb_brute: str = i.replace(":", "")
    number_of_drones = parsing.take_nb_of_drones(nb_brute)
    check_number_validate(clean_content)
    parsing.check_x_coordinate(all_information)
    list_connection = connection_parsing(clean_content)
    check_in_connect_and_file(list_connection, all_information)

    print(list_connection)
    pprint.pprint(all_information)

    init_and_show_visualizer(all_information, list_connection)
