import os

input_dir = r"C:\DeepLabCutProjects\data\ToyNEW RatVideos\10-16-23"

for filename in os.listdir(input_dir):
    if filename.lower().endswith('.avi'):
        new_name = filename.replace(' - Copy', '').replace('  ', ' ').replace(' ', '_')
        src = os.path.join(input_dir, filename)
        dst = os.path.join(input_dir, new_name)
        if src != dst:
            os.rename(src, dst)
            print(f"Renamed: {filename} -> {new_name}")
