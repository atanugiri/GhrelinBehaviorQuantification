def is_dlc_data_already_inserted(conn, video_id):
    cursor = conn.cursor()
    cursor.execute("SELECT t FROM dlc_table WHERE id = %s", (video_id,))
    result = cursor.fetchone()
    cursor.close()
    return result is not None and result[0] is not None
