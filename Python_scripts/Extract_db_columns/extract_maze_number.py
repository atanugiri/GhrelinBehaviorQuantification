from pathlib import Path
import re
import pandas as pd


def load_mother_videos(raw_video_dirs):
    """
    Load mother videos from given directories.
    Match files ending in 4 animal names (w/ or w/o _Trial_#).
    """
    all_videos = []
    for folder in raw_video_dirs:
        folder_path = Path(folder)
        # Match files with 4 trailing underscore-separated tokens
        all_videos += list(folder_path.glob("*.mp4"))
    return all_videos


def build_prefix_to_animal_map(mother_videos):
    """
    Create a mapping from prefix → list of 4 animals.
    Supports filenames like:
    - Prefix_Animal1_Animal2_Animal3_Animal4.mp4
    - Prefix_Animal1_Animal2_Animal3_Animal4_Trial_1.mp4
    """
    prefix_to_animals = {}

    for mv in mother_videos:
        base = mv.stem

        # Match with optional '_Trial_#'
        match = re.match(r"^(.*)_((?:[^_]+_){3}[^_]+)(?:_Trial_\d+)?$", base)
        if match:
            prefix = match.group(1)
            animal_block = match.group(2)
            animals = animal_block.split("_")
            if len(animals) == 4:
                prefix_to_animals[prefix] = animals

    return prefix_to_animals


def get_maze_number(video_name, animal_name, prefix_to_animals):
    """
    Given a split video name and animal name, return maze number (1–4).
    Handles both with and without '_Trial_#' in mother video.
    """
    stem = Path(video_name).stem

    # Remove trailing _Trial# if present
    stem = re.sub(r"_Trial\d+$", "", stem)

    parts = stem.split("_")
    if len(parts) < 5:
        return None  # Not enough parts to contain animal and prefix

    prefix = "_".join(parts[:-1])
    animal = parts[-1]

    animals = prefix_to_animals.get(prefix)
    if not animals or animal_name not in animals:
        return None

    return animals.index(animal_name) + 1


def update_maze_numbers_in_db(conn, dlc_table_name, prefix_to_animals):
    """
    Read video_name and name from dlc_table, compute maze_number,
    and update the database. Also print sanity check info.
    """
    df = pd.read_sql(f"SELECT id, video_name, name FROM {dlc_table_name}", conn)

    with conn.cursor() as cur:
        for _, row in df.iterrows():
            video_name = row['video_name']
            animal_name = row['name']
            maze_number = get_maze_number(video_name, animal_name, prefix_to_animals)

            if maze_number is not None:
                stem = Path(video_name).stem
                prefix = "_".join(stem.split("_")[:-1])
                animals = prefix_to_animals.get(prefix, [])
                mother_video = f"{prefix}_{'_'.join(animals)}_Trial_1.mp4"
                print(f"[✓] {video_name} → {mother_video} → maze {maze_number}")

                cur.execute(
                    f"UPDATE {dlc_table_name} SET maze_number = %s WHERE id = %s",
                    (maze_number, int(row['id']))
                )

    conn.commit()
    print("✅ Maze number update complete.")
