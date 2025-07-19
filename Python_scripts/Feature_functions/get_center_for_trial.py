def get_center_for_trial(trial_id, conn, table='dlc_table'):
    q = f"""SELECT task, maze_number FROM {table} WHERE id = %s"""
    cur = conn.cursor()
    cur.execute(q, (trial_id,))
    row = cur.fetchone()
    
    if not row:
        print(f"[WARNING] Trial ID {trial_id} not found. Using default center (0, 1).")
        return (0, 1)

    task, maze = row

    if task == 'ToyOnly':
        center = {1: (1, 0), 2: (1, 1), 4: (0, 1)}.get(maze, (0, 1))
    elif task == 'LightOnly':
        center = {1: (0, 1), 2: (0, 1), 4: (1, 0)}.get(maze, (0, 1))
    elif task == 'ToyLightNew':
        center = {1: (1, 0), 2: (1, 1), 4: (0, 1)}.get(maze, (0, 1))        
    else:
        center = (0, 1)

    # print(f"[DEBUG] Trial ID {trial_id}: task = {task}, maze = {maze}, center = {center}")
    return center
