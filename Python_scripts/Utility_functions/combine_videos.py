# combine_videos.py

import os
import subprocess

def get_video_pairs(files):
    """Group V1 and V2 video files into pairs based on naming convention."""
    pairs = {}
    for f in files:
        if f.endswith('.mp4'):
            if '_V2_' in f:
                base = f.replace('_V2_', '_')
                pairs.setdefault(base, {})['v2'] = f
            elif '_P_ToyNEW_' in f:
                pairs.setdefault(f, {})['v1'] = f
    return pairs

def format_output_name(base_name):
    """Format output filename as Toy_New_<MM>_<DD>_<YY>_<ShoeName>_P.mp4"""
    tokens = base_name.replace('.mp4', '').split('_P_ToyNEW_')
    shoe = tokens[0].replace('_', '')
    date = tokens[1].replace('-', '_')
    return f"Toy_New_{date}_{shoe}_P.mp4"

def combine_paired_videos(folder):
    """Main function to combine V1 + V2 pairs and save as clean output."""
    files = os.listdir(folder)
    pairs = get_video_pairs(files)

    for base, vids in pairs.items():
        if 'v1' in vids and 'v2' in vids:
            v1 = os.path.join(folder, vids['v1'])
            v2 = os.path.join(folder, vids['v2'])
            output = os.path.join(folder, format_output_name(base))

            if os.path.exists(output):
                print(f"✅ Already exists: {output}")
                continue

            concat_file = os.path.join(folder, 'concat_list.txt')
            with open(concat_file, 'w') as f:
                f.write(f"file '{v1}'\n")
                f.write(f"file '{v2}'\n")

            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-c', 'copy',
                output
            ]

            print(f"🔀 Combining: {vids['v1']} + {vids['v2']} → {os.path.basename(output)}")
            subprocess.run(cmd, check=True)
            os.remove(concat_file)

    print("🎉 All video pairs processed.")
