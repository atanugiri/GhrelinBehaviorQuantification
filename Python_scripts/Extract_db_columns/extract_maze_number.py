from pathlib import Path
import re
import pandas as pd
import psycopg2


def load_mother_videos(raw_video_dirs):
    """
    Scan multiple directories for mother videos and return a list of Path objects.
    """
    all_videos = []
    for folder in raw_video_dirs:
        folder_path = Path(folder)
        all_videos += list(folder_path.glob("*_Trial_*.mp4"))
    return all_videos


def build_prefix_to_animal_map(mother_videos):
    """
    Create a mapping from prefix → list of 4 animals
    """
    prefix_to_animals = {}
    for mv in mother_videos:
        base = mv.stem
        match = re.search(r"^(.*)_((?:[^_]+_){3}[^_]+)_Trial_\d+$", base)
        if match:
            prefix = match.group(1)
            animal_block = match.group(2)
            animals = animal_block.split("_")
            if len(animals) == 4:
                prefix_to_animals[prefix] = animals
    return prefix_to_animals
    

def get_maze_number(video_name, animal_name, prefix_to_animals):
    """
    Given a split video name and animal name, return the maze number (1–4).
    Returns None if:
    - the video ends with '_Trial%d'
    - no matching mother video is found
    """
    stem = Path(video_name).stem

    # Case 2: Skip if ends with '_Trial' + number
    if re.search(r"_Trial\d+$", stem):
        return None

    try:
        # Case 1: remove last part (animal name) to get mother video prefix
        prefix = '_'.join(stem.split('_')[:-1])
        animals = prefix_to_animals.get(prefix)

        if not animals or animal_name not in animals:
            return None

        return animals.index(animal_name) + 1
    except Exception:
        return None


def update_maze_numbers_in_db(conn, dlc_table_name, prefix_to_animals):
    """
    Read video_name and name from dlc_table, compute maze_number,
    and update the database. Also print out sanity check info for each match.
    """
    df = pd.read_sql(f"SELECT id, video_name, name FROM {dlc_table_name}", conn)

    with conn.cursor() as cur:
        for _, row in df.iterrows():
            video_name = row['video_name']
            animal_name = row['name']
            maze_number = get_maze_number(video_name, animal_name, prefix_to_animals)

            # Print sanity check info if maze_number was computed
            if maze_number is not None:
                stem = Path(video_name).stem
                mother_prefix = '_'.join(stem.split('_')[:-1])
                mother_video = f"{mother_prefix}_{'_'.join(prefix_to_animals[mother_prefix])}_Trial_1.mp4"
                print(f"[✓] {video_name} → {mother_video} → maze {maze_number}")

                cur.execute(
                    f"UPDATE {dlc_table_name} SET maze_number = %s WHERE id = %s",
                    (maze_number, int(row['id']))
                )

    conn.commit()
    print("✅ Maze number update complete.")

