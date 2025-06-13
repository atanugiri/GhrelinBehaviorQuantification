import os
import shutil
import re

def copy_trials_with_clean_names(src_root, dst_root, prefix='ToyOnly'):
    """
    Copies trial video files with standardized filenames from a source directory tree to a destination directory.

    This function walks through all subdirectories of `src_root`, searching for video files that match
    the naming pattern like 'Trial 1.mp4' or 'Trial_2.mp4' (case-insensitive), while ignoring files
    like 'Trial_1_bottom_left.mp4'. It constructs a new filename using the provided `prefix`, the 
    cleaned subdirectory names, and a sanitized version of the original filename.

    Parameters:
    ----------
    src_root : str
        The root directory to search for video files. Assumes that trial videos are located at
        depth ≥ 2, i.e., inside subfolders organized as `DayFolder/AnimalFolder/Trial X.mp4`.

    dst_root : str
        The directory where the renamed video files will be copied.

    prefix : str, optional
        A prefix to prepend to the cleaned filenames. For example, if prefix='Toy_Only',
        the output filenames will look like 'Toy_Only_11_11_24_Teal_Orange_None_Cyan_Trial_1.mp4'.

    Notes:
    -----
    - Animal folder names are cleaned to remove special characters, replace spaces with underscores,
      and collapse repeated underscores.
    - Filenames are also normalized by replacing spaces with underscores.
    - If a folder structure does not meet the expected depth (e.g., Day/Animal), that file is skipped.
    """
    os.makedirs(dst_root, exist_ok=True)

    # Match exactly: 'Trial 1.mp4', 'Trial_2.mp4', etc. (but NOT Trial_1_bottom_left.mp4)
    trial_pattern = re.compile(r'^Trial[\s_]*\d+\.mp4$', re.IGNORECASE)

    for root, _, files in os.walk(src_root):
        for filename in files:
            if trial_pattern.match(filename):
                rel_path = os.path.relpath(root, src_root)
                parts = rel_path.split(os.sep)

                if len(parts) < 2:
                    print(f"⚠️ Skipping {os.path.join(root, filename)} — insufficient path info.")
                    continue

                day_folder = parts[0]
                animal_folder = parts[1]

                day_clean = day_folder.replace('-', '_')

                # Clean animal block
                animal_clean = re.sub(r'None\s*\d+', 'None', animal_folder)
                animal_clean = re.sub(r'[^\w\s]', ' ', animal_clean)
                animal_clean = re.sub(r'\s+', '_', animal_clean.strip())
                animal_clean = re.sub(r'_+', '_', animal_clean)

                # Clean filename
                filename_clean = re.sub(r'\s+', '_', filename.strip())

                new_filename = f"{prefix}_{day_clean}_{animal_clean}_{filename_clean}"
                src_file = os.path.join(root, filename)
                dst_file = os.path.join(dst_root, new_filename)

                print(f"✅ Copying: {src_file} -> {dst_file}")
                shutil.copy2(src_file, dst_file)
            else:
                print(f"⏭️ Skipped (not base Trial file): {filename}")
