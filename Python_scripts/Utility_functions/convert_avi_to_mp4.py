# convert_avi_to_mp4.py

import os
import subprocess

def convert_avi_to_mp4(input_dir):
    """Convert all .avi files in a folder to .mp4 using ffmpeg."""
    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.avi'):
            avi_path = os.path.join(input_dir, filename)
            mp4_filename = os.path.splitext(filename)[0] + '.mp4'
            mp4_path = os.path.join(input_dir, mp4_filename)

            if os.path.exists(mp4_path):
                print(f"Already exists, skipping: {mp4_filename}")
                continue

            cmd = [
                'ffmpeg',
                '-i', avi_path,
                '-c:v', 'libx264',
                '-crf', '23',
                '-preset', 'fast',
                mp4_path
            ]

            print(f"Converting: {filename} -> {mp4_filename}")
            subprocess.run(cmd, check=True)

    print("✅ Conversion complete.")
