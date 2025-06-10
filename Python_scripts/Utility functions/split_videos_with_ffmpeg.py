#!/usr/bin/env python
# coding: utf-8

import os
import subprocess
from tkinter import Tk
from tkinter.filedialog import askdirectory, askopenfilename
import re

BASE_PATH = r"C:\DeepLabCutProjects\DLC-Atanu-2024-12-25\Ghrelin\2024"

def split_videos_with_ffmpeg():
    # Use tkinter to select a mode
    print("Select processing mode:")
    print("1. Process all videos in a folder")
    print("2. Process multiple folders")
    print("3. Process a single video file")
    mode = input("Enter 1, 2, or 3: ").strip()

    root = Tk()
    root.withdraw()

    folder_paths = []

    if mode == "1":
        folder_path = askdirectory(title="Select Folder Containing .mp4 Files")
        if folder_path:
            folder_paths.append(folder_path)
        else:
            print("No folder selected. Exiting.")
            return
    elif mode == "2":
        print("Select multiple folders. Click 'Cancel' when done.")
        while True:
            folder_path = askdirectory(title="Select a Folder (Cancel to Stop)")
            if folder_path:
                folder_paths.append(folder_path)
            else:
                break
        if not folder_paths:
            print("No folders selected. Exiting.")
            return
    elif mode == "3":
        file_path = askopenfilename(title="Select a Video File", filetypes=[("MP4 files", "*.mp4")])
        if not file_path:
            print("No file selected. Exiting.")
            return
        folder_paths.append(os.path.dirname(file_path))
        process_video(file_path, os.path.dirname(file_path))
        return
    else:
        print("Invalid input. Exiting.")
        return

    root.destroy()

    for folder_path in folder_paths:
        print(f"Processing folder: {folder_path}")
        mp4_files = [f for f in os.listdir(folder_path) if f.endswith(".mp4") and not re.search(r'_(top|bottom)_(left|right)\.mp4$', f)]
        if not mp4_files:
            print(f"No eligible .mp4 files found in {folder_path}. Skipping.")
            continue

        for video_file in mp4_files:
            process_video(os.path.join(folder_path, video_file), folder_path)

def process_video(input_path, folder_path):
    video_file = os.path.basename(input_path)
    print(f"Processing file: {video_file}")
    base_name, ext = os.path.splitext(video_file)  # Extract base filename without .mp4

    # Extract the relevant portion of the path after BASE_PATH and clean it up
    relative_path = os.path.relpath(input_path, BASE_PATH)
    cleaned_path = re.sub(r'[\\, ]+', '_', relative_path)  # Replace spaces, backslashes, and commas with '_'
    cleaned_path = cleaned_path.replace("-", "_")  # Replace hyphens with underscores

    # Ensure spaces in the original name are replaced for output naming
    sanitized_name = re.sub(r'\s+', '_', base_name)  # Base name without .mp4
    sanitized_name = sanitized_name.replace("-", "_")  # Replace hyphens with underscores

    # Remove '.mp4' if mistakenly left in cleaned_path
    cleaned_path = re.sub(r'\.mp4$', '', cleaned_path)

    # Remove redundant base name from cleaned_path if present
    cleaned_path = re.sub(r'_?' + re.escape(sanitized_name) + r'$', '', cleaned_path)

    # Define output paths for the 4 quadrants
    output_paths = {
        "top_left": os.path.join(folder_path, f"{cleaned_path}_{sanitized_name}_top_left.mp4"),
        "top_right": os.path.join(folder_path, f"{cleaned_path}_{sanitized_name}_top_right.mp4"),
        "bottom_left": os.path.join(folder_path, f"{cleaned_path}_{sanitized_name}_bottom_left.mp4"),
        "bottom_right": os.path.join(folder_path, f"{cleaned_path}_{sanitized_name}_bottom_right.mp4")
    }

    # Define FFmpeg crop commands for each quadrant
    commands = {
        "top_left": ["ffmpeg", "-y", "-i", input_path, "-filter:v", "crop=in_w/2:in_h/2:0:0", output_paths["top_left"]],
        "top_right": ["ffmpeg", "-y", "-i", input_path, "-filter:v", "crop=in_w/2:in_h/2:in_w/2:0", output_paths["top_right"]],
        "bottom_left": ["ffmpeg", "-y", "-i", input_path, "-filter:v", "crop=in_w/2:in_h/2:0:in_h/2", output_paths["bottom_left"]],
        "bottom_right": ["ffmpeg", "-y", "-i", input_path, "-filter:v", "crop=in_w/2:in_h/2:in_w/2:in_h/2", output_paths["bottom_right"]]
    }

    # Run FFmpeg commands for each quadrant
    for quadrant, command in commands.items():
        print(f"Generating {quadrant} for {video_file}")
        subprocess.run(command, shell=True)

    print(f"Finished processing {video_file}.")

if __name__ == "__main__":
    split_videos_with_ffmpeg()

