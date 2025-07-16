from pathlib import Path

# base_data_dir = Path(r"C:\DeepLabCutProjects\data")  # Adjust if needed
base_data_dir = Path.home() / "Downloads" / "data" / "ToyLight" / "DlcDataPytorchFiltered"

def find_csv_for_video(video_name):
    """
    Given a video filename, search for the corresponding DLC CSV in DlcData subfolders.
    """
    stem = Path(video_name).stem  # remove .mp4 or .avi
    pattern = f"{stem}*_filtered.csv"

    matches = list(base_data_dir.glob(pattern))
    if matches:
        return str(matches[0])  # Return full path as string

    return None  # If no match found
