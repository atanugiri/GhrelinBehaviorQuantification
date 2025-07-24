import os
import re
import subprocess
from tkinter import Tk
from tkinter.filedialog import askopenfilename, askdirectory

def split_videos_by_quadrants(input_dir=None, output_dir=None, mode=None):
    if mode not in {"1", "2"}:
        print("Invalid mode. Use '1' for folder mode or '2' for single file mode.")
        return

    root = Tk()
    root.withdraw()

    if mode == "1":
        if not input_dir:
            input_dir = askdirectory(title="Select Folder Containing .mp4 Files")
            if not input_dir:
                print("No input folder selected.")
                return
        if not output_dir:
            output_dir = askdirectory(title="Select Output Folder")
            if not output_dir:
                print("No output folder selected.")
                return

        mp4_files = [f for f in os.listdir(input_dir) if f.endswith(".mp4")]
        for video_file in mp4_files:
            input_path = os.path.join(input_dir, video_file)
            process_video(input_path, output_dir)

    elif mode == "2":
        if not input_dir:
            input_file = askopenfilename(title="Select a Video File", filetypes=[("MP4 files", "*.mp4")])
            if not input_file:
                print("No file selected.")
                return
        else:
            input_file = input_dir  # here input_dir acts as full path to the file

        if not output_dir:
            output_dir = askdirectory(title="Select Output Folder")
            if not output_dir:
                print("No output folder selected.")
                return

        process_video(input_file, output_dir)

    root.destroy()


def process_video(input_path, output_dir):
    filename = os.path.basename(input_path)
    base_name, _ = os.path.splitext(filename)

    # Pattern: Prefix_AnimalBlock_Trial_x.mp4
    match = re.match(r"^(.*)_(\w+_\w+_\w+_\w+)(?:_Trial_\d+)?$", base_name)
    if not match:
        print(f"Filename format not recognized: {filename}")
        return

    prefix = match.group(1)
    animal_block = match.group(2)
    animals = animal_block.split("_")

    if len(animals) != 4:
        print(f"Unexpected animal block format: {animal_block}")
        return

    quadrant_labels = ['top_left', 'top_right', 'bottom_left', 'bottom_right']
    crop_filters = {
        'top_left':     "crop=in_w/2:in_h/2:0:0",
        'top_right':    "crop=in_w/2:in_h/2:in_w/2:0",
        'bottom_left':  "crop=in_w/2:in_h/2:0:in_h/2",
        'bottom_right': "crop=in_w/2:in_h/2:in_w/2:in_h/2"
    }

    for label, animal in zip(quadrant_labels, animals):
        if not animal or animal.lower() == 'none':
            continue  # Skip if placeholder or blank
        output_filename = f"{prefix}_{animal}.mp4"
        output_path = os.path.join(output_dir, output_filename)

        command = [
            "ffmpeg", "-y", "-i", input_path,
            "-filter:v", crop_filters[label],
            output_path
        ]

        print(f"Saving {label} as {output_filename}")
        subprocess.run(command, shell=True)

    print(f"Finished processing: {filename}")

# Example usage
if __name__ == "__main__":
    # Example: folder mode
    # split_videos_by_quadrants(mode="1")

    # Example: single file mode with hardcoded input path
    # split_videos_by_quadrants(input_dir="path_to_file.mp4", output_dir="your_output_folder", mode="3")

    # For interactive GUI selection
    split_videos_by_quadrants(mode="1")  # or "2"
