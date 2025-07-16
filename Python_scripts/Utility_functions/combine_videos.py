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
            else:
                # Accept any base file (not V2)
                pairs.setdefault(f, {})['v1'] = f
    return pairs


def format_output_name(base_name):
    """
    Returns: ToyNew_<MM_DD_YY>_<AnimalNameNoUnderscores>_<P_or_Y>.mp4
    Handles both single- and multi-word animal names.
    """
    base = os.path.basename(base_name).replace('.mp4', '')
    parts = base.split('_')

    if 'V2' in parts:
        parts.remove('V2')

    try:
        condition = parts[-2]  # 'P' or 'Y'
        date_parts = parts[-1].split('-')  # ['MM', 'DD', 'YY']
        date = '_'.join(date_parts)

        animal_name_parts = parts[:-2]
        animal_name = ''.join(animal_name_parts)  # no underscores

        return f"ToyNew_{date}_{animal_name}_{condition}.mp4"
    except Exception as e:
        print(f"❌ Filename parsing error: {base_name} → {e}")
        raise



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
