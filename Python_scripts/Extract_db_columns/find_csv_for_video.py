from pathlib import Path

base_data_dir = Path(r"C:\DeepLabCutProjects\data")  # Adjust if needed

def find_csv_for_video(video_name):
    """
    Given a video filename, search for the corresponding DLC CSV in DlcData subfolders.
    """
    stem = Path(video_name).stem  # remove .mp4 or .avi
    pattern = f"{stem}DLC_resnet50_*.csv"

    for subdir in base_data_dir.iterdir():
        dlc_dir = subdir / "DlcData"
        if dlc_dir.exists():
            matches = list(dlc_dir.glob(pattern))
            if matches:
                return str(matches[0])  # return full path as string

    return None  # if no match found
