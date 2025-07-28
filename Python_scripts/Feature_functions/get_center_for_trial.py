def get_center_for_trial(trial_id, conn, table='dlc_table'):
    """
    get center for trial id based on maze number
    """
    q = f"""SELECT genotype, task, maze_number FROM {table} WHERE id = %s"""
    cur = conn.cursor()
    cur.execute(q, (trial_id,))
    row = cur.fetchone()
    
    if not row:
        print(f"[WARNING] Trial ID {trial_id} not found. Using default center (0, 1).")
        return (0, 1)

    genotype, task, maze = row

    if genotype=='black' and task == 'ToyOnly':
        center = {1: (1, 0), 2: (1, 1), 4: (0, 1)}.get(maze, (0, 1))
    elif genotype=='black' and task == 'LightOnly':
        center = {1: (0, 1), 2: (0, 1), 4: (1, 0)}.get(maze, (0, 1))
    elif genotype=='black' and task == 'ToyLightNew':
        center = {1: (1, 0), 2: (1, 1), 4: (0, 1)}.get(maze, (0, 1))    
    elif genotype == 'white' and task in (
        'ToyOnly', 'LightOnly', 'FoodLight', 'ToyOnlyExcitatory', 'ToyOnlyInhibitory'):
        center = (1, 0) if maze == 4 else (0, 1)
    else:
        center = (0, 1)

    # print(f"[DEBUG] Trial ID {trial_id}: task = {task}, maze = {maze}, center = {center}")
    return center
