import re

def extract_animal_name(filename):
    # Mapping from quadrant to animal position
    quadrant_to_position = {
        'top_left': 0,
        'top_right': 1,
        'bottom_left': 2,
        'bottom_right': 3,
    }

    # Extract quadrant
    match_quadrant = re.search(r'(top_left|top_right|bottom_left|bottom_right)', filename)
    if not match_quadrant:
        return None

    quadrant = match_quadrant.group(1)
    animal_index = quadrant_to_position[quadrant]

    # Match pattern between two underscore groups of 4 or more before Trial
    match_animal_block = re.search(r'_{4,}(.*?)_{4,}Trial_\d+', filename)
    if not match_animal_block:
        return None

    animal_block = match_animal_block.group(1)
    animal_list = animal_block.split('_')

    if animal_index >= len(animal_list):
        return None

    return animal_list[animal_index]
