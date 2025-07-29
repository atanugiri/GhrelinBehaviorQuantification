import os
import cv2
import psycopg2
import pandas as pd
import platform


def find_video_path(video_name, base_video_dir, subdir):
    # for subdir in video_subdirs:
    folder = os.path.join(base_video_dir, subdir, 'SplitVideos')
    candidate = os.path.join(folder, video_name)
    if os.path.isfile(candidate):
        return candidate
    return None

def get_video_info(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None, None, None, None
    num_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return num_frames, frame_rate, width, height

def update_video_info_in_db(conn, base_video_dir, subdir):
    cursor = conn.cursor()
    
    # Select incomplete rows
    query = """
        SELECT id, video_name FROM dlc_table
        WHERE num_frames IS NULL OR frame_rate IS NULL OR video_width IS NULL OR video_height IS NULL;
    """
    df = pd.read_sql_query(query, conn)

    updates = []
    for _, row in df.iterrows():
        video_id = row['id']
        video_name = row['video_name']
        path = find_video_path(video_name, base_video_dir, subdir)

        if path:
            num_frames, frame_rate, width, height = get_video_info(path)
            if None not in (num_frames, frame_rate, width, height):
                print(f"ID {video_id}: {video_name} — {num_frames} frames, {frame_rate:.2f} fps, {width}x{height}")
                updates.append((num_frames, frame_rate, width, height, video_id))
            else:
                print(f"Could not read metadata: {video_name}")
        else:
            print(f"File not found: {video_name}")

    # Batch update
    if updates:
        cursor.executemany("""
            UPDATE dlc_table
            SET num_frames = %s,
                frame_rate = %s,
                video_width = %s,
                video_height = %s
            WHERE id = %s;
        """, updates)
        conn.commit()
        print(f"\nUpdated {len(updates)} rows.")
    else:
        print("No updates made.")
