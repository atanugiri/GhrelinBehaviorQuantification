def extract_maze_number(filename):
    quadrant_to_maze = {
        'top_left': 1,
        'top_right': 2,
        'bottom_left': 3,
        'bottom_right': 4,
    }

    for quadrant in quadrant_to_maze:
        if quadrant in filename:
            return quadrant_to_maze[quadrant]

    return None