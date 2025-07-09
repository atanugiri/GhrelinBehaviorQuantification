import os
import subprocess

input_dir = r"C:\DeepLabCutProjects\data\FoodLight\SplitVideos"

# Loop through all AVI files
for filename in os.listdir(input_dir):
    if filename.lower().endswith('.avi'):
        avi_path = os.path.join(input_dir, filename)
        mp4_filename = os.path.splitext(filename)[0] + '.mp4'
        mp4_path = os.path.join(input_dir, mp4_filename)

        # Skip if already converted
        if os.path.exists(mp4_path):
            print(f"Already exists, skipping: {mp4_filename}")
            continue

        # ffmpeg command
        cmd = [
            'ffmpeg',
            '-i', avi_path,
            '-c:v', 'libx264',
            '-crf', '23',
            '-preset', 'fast',
            mp4_path
        ]

        print(f"Converting: {filename} → {mp4_filename}")
        subprocess.run(cmd, check=True)

print("✅ Conversion complete.")
