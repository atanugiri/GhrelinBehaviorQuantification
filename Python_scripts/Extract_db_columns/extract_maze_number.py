from pathlib import Path
import re
import pandas as pd


# --- Helpers -----------------------------------------------------------------

# Strip trailing variations like: _Trial1, _trial_2, _Trial-03
TRIAL_SUFFIX_RX = re.compile(r'_(?:[Tt]rial)[ _-]?\d+$')

def _strip_trial_suffix(stem: str) -> str:
    return TRIAL_SUFFIX_RX.sub('', stem)

# Optional: strip quadrant suffixes like _top_left / _bottom_right
QUAD_SUFFIX_RX = re.compile(r'_(?:top|bottom)_(?:left|right)$', flags=re.I)

def _strip_quadrant_suffix(stem: str) -> str:
    return QUAD_SUFFIX_RX.sub('', stem)

def _prefix_from_stem(stem: str) -> str:
    """
    Prefix is the first 5 tokens: Task_MM_DD_YY_HealthCode
    """
    parts = stem.split('_')
    # Expect at least: Task, MM, DD, YY, HealthCode, Animal
    if len(parts) < 6:
        return ''
    return '_'.join(parts[:5])


# --- Public API ---------------------------------------------------------------

def load_mother_videos(raw_video_dirs):
    """
    Return only mother videos that end with 4 animal tokens, with optional Trial suffix.

    Matches:
      Prefix_A1_A2_A3_A4.mp4
      Prefix_A1_A2_A3_A4_Trial2.mp4
      (Prefix is everything before the 4-animal block.)
    """
    mother_pat = re.compile(
        r'^.+_(?:[^_]+_){3}[^_]+(?:_(?:[Tt]rial)[ _-]?\d+)?\.mp4$'
    )
    all_mothers = []
    for folder in raw_video_dirs:
        folder_path = Path(folder)
        for p in folder_path.glob("*.mp4"):
            if mother_pat.match(p.name):
                all_mothers.append(p)
    return all_mothers


def build_prefix_to_animal_map(mother_videos):
    """
    Build a map: 'Task_MM_DD_YY_HealthCode' -> [A1, A2, A3, A4]
    (Where animals are taken case-sensitively from filenames.)
    """
    prefix_to_animals = {}
    for mv in mother_videos:
        base = _strip_trial_suffix(mv.stem)
        # Everything before the 4-animal block is the prefix.
        m = re.match(r'^(?P<prefix>.+?)_(?P<animals>(?:[^_]+_){3}[^_]+)$', base)
        if not m:
            continue
        prefix = m.group('prefix')
        animals = m.group('animals').split('_')
        if len(animals) == 4:
            prefix_to_animals[prefix] = animals
    return prefix_to_animals


def get_maze_number(video_name, animal_name, prefix_to_animals):
    """
    Given a split video name (with or without _Trial# / quadrant suffix)
    and the DB 'name' column, return maze number 1–4, else None.

    - Uses consistent 5-token prefix: Task_MM_DD_YY_HealthCode
    - Case-insensitive animal match
    - Tolerates trailing digits in animal_name (e.g., 'None4' -> 'None')
    """
    stem = Path(video_name).stem
    stem = _strip_trial_suffix(stem)
    stem = _strip_quadrant_suffix(stem)

    prefix = _prefix_from_stem(stem)
    if not prefix:
        return None

    parts = stem.split('_')
    # Expected at least 6 tokens: ... + Animal
    animal_from_split = parts[5] if len(parts) >= 6 else None

    # Prefer DB name; fallback to animal parsed from split filename
    candidate = animal_name if pd.notna(animal_name) and str(animal_name) != '' else animal_from_split
    if not candidate:
        return None

    # Normalize candidate (e.g., 'None4' -> 'None')
    candidate_clean = re.sub(r'\d+$', '', str(candidate)).lower()

    animals = prefix_to_animals.get(prefix)
    if not animals:
        return None

    for i, a in enumerate(animals):
        if a.lower() == candidate_clean:
            return i + 1

    return None


def update_maze_numbers_in_db(conn, dlc_table_name, prefix_to_animals):
    """
    Read id, video_name, name from dlc_table, compute maze_number,
    and update the database. Prints a clear sanity line for each update.
    """
    df = pd.read_sql(f"SELECT id, video_name, name FROM {dlc_table_name}", conn)

    with conn.cursor() as cur:
        for _, row in df.iterrows():
            video_name = row['video_name']
            animal_name = row['name']

            maze_number = get_maze_number(video_name, animal_name, prefix_to_animals)
            if maze_number is not None:
                stem_clean = _strip_quadrant_suffix(_strip_trial_suffix(Path(video_name).stem))
                prefix = _prefix_from_stem(stem_clean)
                animals = prefix_to_animals.get(prefix, [])
                if animals:
                    mother_video = f"{prefix}_{'_'.join(animals)}_Trial_1.mp4"
                else:
                    mother_video = "(mother not found in map)"

                print(f"[✓] {video_name} → {mother_video} → maze {maze_number}")

                cur.execute(
                    f"UPDATE {dlc_table_name} SET maze_number = %s WHERE id = %s",
                    (int(maze_number), int(row['id']))
                )

    conn.commit()
    print("✅ Maze number update complete.")
