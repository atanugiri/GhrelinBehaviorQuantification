import os
import shutil
import re

def copy_avi_files_from_dated_folders(src_root, dst_root, prefix='Food_Light'):
    """
    Copies and renames .avi files using the date from the folder path and the cleaned animal info.

    Input path example:
        .../Food Light Experiment/September/9-9-24/Azul P 9-9-24.avi

    Output filename:
        Food_Light_9_9_24_Azul_P.avi

    Parameters:
    ----------
    src_root : str
        Root directory to recursively search for .avi files.

    dst_root : str
        Destination directory for renamed files.

    prefix : str
        Prefix to prepend to output filenames.
    """
    os.makedirs(dst_root, exist_ok=True)

    for root, _, files in os.walk(src_root):
        # Extract date from folder name
        parts = root.split(os.sep)
        if len(parts) < 1:
            continue
        folder_date = parts[-1]
        if not re.match(r'^\d{1,2}-\d{1,2}-\d{2,4}$', folder_date):
            continue
        date_clean = folder_date.replace('-', '_')

        for file in files:
            if file.lower().endswith('.avi'):
                # Remove extension and trailing date if present
                base = file[:-4]  # remove ".avi"
                animal_part = re.sub(r'\s*\d{1,2}-\d{1,2}-\d{2,4}$', '', base)
                animal_clean = re.sub(r'[^\w\s]', ' ', animal_part)
                animal_clean = re.sub(r'\s+', '_', animal_clean.strip())
                animal_clean = re.sub(r'_+', '_', animal_clean)

                new_filename = f"{prefix}_{date_clean}_{animal_clean}.avi"
                src_file = os.path.join(root, file)
                dst_file = os.path.join(dst_root, new_filename)

                print(f"✅ Copying: {src_file} -> {dst_file}")
                shutil.copy2(src_file, dst_file)
