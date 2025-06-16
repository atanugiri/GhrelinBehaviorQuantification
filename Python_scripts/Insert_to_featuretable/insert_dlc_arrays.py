def insert_dlc_arrays(conn, video_id, df_parsed, bodyparts):
    cursor = conn.cursor()

    # Prepare arrays
    t = df_parsed['t'].tolist()

    data = {'t': t, 'video_id': video_id}

    for part in bodyparts:
        part_lower = part.lower()
        data[f"{part_lower}_x"] = df_parsed.get(f"{part_lower}_x", []).tolist()
        data[f"{part_lower}_y"] = df_parsed.get(f"{part_lower}_y", []).tolist()

    # Build columns list
    columns = ['t'] + [f"{part.lower()}_{axis}" for part in bodyparts for axis in ['x', 'y']]

    # SQL: update col1 = %s, col2 = %s, ...
    set_clause = ', '.join([f"{col} = %s" for col in columns])

    query = f"""
        UPDATE dlc_table
        SET {set_clause}
        WHERE video_id = %s;
    """

    values = [data[col] for col in columns] + [video_id]

    try:
        cursor.execute(query, values)
        conn.commit()
        print(f"✅ Inserted video_id {video_id}")
    except Exception as e:
        conn.rollback()
        print(f"❌ SQL insert failed for video_id {video_id}: {e}")

    cursor.close()
