import os
import pandas as pd
import numpy as np
import cv2
from tqdm import tqdm

# Directories
input_dir = r"C:\DeepLabCutProjects\DLC-Atanu-2024-12-25\Analyzed-videos-filtered"
output_dir = os.path.join(input_dir, "NormalizedCSVs")
log_path = os.path.join(output_dir, "normalization_log.txt")
os.makedirs(output_dir, exist_ok=True)

# Unit square reference (top-right, top-left, bottom-left, bottom-right)
unit_square = np.array([
    [1, 0],  # Corner1
    [0, 0],  # Corner2
    [0, 1],  # Corner3
    [1, 1],  # Corner4
], dtype=np.float32)

# Body parts to normalize
body_parts = [
    'Head', 'Leftear', 'Rightear', 'Tailbase',
    'Neck', 'Midback', 'Lowerback',
    'Corner1', 'Corner2', 'Corner3', 'Corner4'
]

# Log skipped files
log_entries = []

# Process files with progress bar
all_files = [f for f in os.listdir(input_dir) if f.endswith(".csv") and "normalized" not in f.lower()]
for filename in tqdm(all_files, desc="Normalizing CSVs"):
    filepath = os.path.join(input_dir, filename)
    try:
        df = pd.read_csv(filepath, header=[1, 2])

        # Step 1: Use high-confidence corner points only for homography
        src_pts = []
        for corner in ['Corner1', 'Corner2', 'Corner3', 'Corner4']:
            lx = df[(corner, 'x')]
            ly = df[(corner, 'y')]
            ll = df[(corner, 'likelihood')]
            mask = ll > 0.9

            if mask.sum() == 0:
                log_entries.append(f"{filename} - Skipped: No valid points for {corner}")
                src_pts = None
                break

            avg_x = lx[mask].mean()
            avg_y = ly[mask].mean()
            src_pts.append([avg_x, avg_y])

        if src_pts is None:
            continue

        src_pts = np.array(src_pts, dtype=np.float32)

        if np.isnan(src_pts).any():
            log_entries.append(f"{filename} - Skipped: Invalid corner average (NaNs)")
            continue

        try:
            # Step 2: Compute homography
            H, _ = cv2.findHomography(src_pts, unit_square)

            # Step 3: Apply to all body parts
            for bp in body_parts:
                x = df[(bp, 'x')]
                y = df[(bp, 'y')]
                ones = np.ones_like(x)
                coords = np.vstack([x, y, ones])
                warped = H @ coords
                warped /= warped[2]
                df[(bp, 'x')] = warped[0]
                df[(bp, 'y')] = warped[1]

            # Step 4: Save normalized CSV
            output_path = os.path.join(output_dir, filename.replace(".csv", "_normalized.csv"))
            df.to_csv(output_path, index=False)

        except Exception as e:
            log_entries.append(f"{filename} - Skipped: Homography application failed ({str(e)})")

    except Exception as e:
        log_entries.append(f"{filename} - Skipped: Failed to load/process file ({str(e)})")

# Save log
with open(log_path, 'w') as log_file:
    log_file.write("\n".join(log_entries))

print(f"\nFinished normalization. Log saved to: {log_path}")
