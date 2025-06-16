print("parse_dlc_csv module loaded") # temp

import pandas as pd
import numpy as np

def parse_dlc_csv(csv_path, frame_rate, bodyparts, likelihood_threshold=0.9):
    print(f"[DEBUG] bodyparts: {bodyparts}") # temp

    df = pd.read_csv(csv_path, header=[1, 2])  # ✅ Skip scorer row

    num_frames = len(df)
    t = np.round(np.arange(num_frames) / frame_rate, 3)

    rows = []
    for i in range(num_frames):
        row = {'t': t[i]}
        for part in bodyparts:
            try:
                x = df[part]['x'].iloc[i]
                y = df[part]['y'].iloc[i]
                p = df[part]['likelihood'].iloc[i]

                if p >= likelihood_threshold:
                    row[f"{part.lower()}_x"] = round(x, 3)
                    row[f"{part.lower()}_y"] = round(x, 3)
                else:
                    row[f"{part.lower()}_x"] = np.nan
                    row[f"{part.lower()}_y"] = np.nan
            except KeyError:
                # Skip missing body parts gracefully
                row[f"{part.lower()}_x"] = np.nan
                row[f"{part.lower()}_y"] = np.nan
        rows.append(row)

    return rows  # Each row = one frame of cleaned data
