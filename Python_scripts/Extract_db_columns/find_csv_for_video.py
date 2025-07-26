from pathlib import Path

# base_data_dir = Path.home() / "Downloads" / "data" / "ToyOnlyWhite" / "DlcDataPytorchFiltered"

def find_csv_for_video(video_name, base_data_dir):
    """
    Given a video filename, search for the corresponding DLC CSV in base_data_dir.

    Args:
        video_name (str): Name of the video file (.mp4, .avi, etc.)
        base_data_dir (Path or str): Directory to search for the corresponding CSV file.

    Returns:
        str or None: Full path to the matched CSV file, or None if no match is found.
    """
    base_data_dir = Path(base_data_dir)  # Ensure it's a Path object
    stem = Path(video_name).stem  # Remove file extension
    pattern = f"{stem}*_filtered.csv"

    matches = list(base_data_dir.glob(pattern))
    if matches:
        return str(matches[0])

    return None
