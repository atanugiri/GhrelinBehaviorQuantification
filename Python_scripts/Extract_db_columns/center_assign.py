# center_assign.py
from typing import Optional, Tuple, List, Dict, Any

# Rule keys can be used: genotype, task, maze
RULES = [
    # --- black animals ---
    {"genotype": "black", "task": "FoodOnly",             "center": (0.5, 0.5)},
    {"genotype": "black", "task": "FoodLight",            "center": (0.0, 1.0)},
    {"genotype": "black", "task": "ToyOnly",   "maze": 1, "center": (1.0, 0.0)},
    {"genotype": "black", "task": "ToyOnly",   "maze": 2, "center": (1.0, 1.0)},
    {"genotype": "black", "task": "ToyOnly",   "maze": 4, "center": (0.0, 1.0)},
    {"genotype": "black", "task": "ToyLight",             "center": (0.0, 1.0)},
    {"genotype": "black", "task": "LightOnly", "maze": 4, "center": (1.0, 0.0)},
    {"genotype": "black", "task": "LightOnly",            "center": (0.0, 1.0)},

    # --- white MazeOnly (intent: always (1,0)) ---
    {"genotype": "white", "task": "MazeOnly", "center": (0.5, 0.5)},

    # --- white (all doses) ---
    {"genotype": "white", "maze": 4, "center": (1.0, 0.0)},  # specific first
    {"genotype": "white",            "center": (0.0, 1.0)},  # generic fallback

    # Fallback (any row not matched above)
    {"center": (0.0, 1.0)},
]

def _rule_matches(rule, genotype, task, maze) -> bool:
    """
    True iff all specified fields in the rule match the row.
    Missing keys in the rule are wildcards.
    """
    if "genotype" in rule and rule["genotype"] is not None and rule["genotype"] != genotype:
        return False
    if "task" in rule and rule["task"] is not None and rule["task"] != task:
        return False
    if "maze" in rule and rule["maze"] is not None and rule["maze"] != maze:
        return False
    return True


def find_center_for_task(trial_id: int, conn, table: str = "dlc_table"):
    """
    Fetch minimal fields for the trial, scan RULES in order,
    return the first matching (center_x, center_y).
    """
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT genotype, task, maze FROM {table} WHERE id=%s",
            (trial_id,)
        )
        row = cur.fetchone()
    if not row:
        raise ValueError(f"Trial ID {trial_id} not found in {table}.")
    genotype, task, maze = row

    for rule in RULES:  # first-match wins
        if _rule_matches(rule, genotype, task, maze):
            return rule["center"]
    return (0.0, 1.0)  # fallback


def update_center_for_task(conn, id_list=None, table: str = "dlc_table", force: bool = False, batch_size: int = 1000):
    """
    Compute centers and bulk-update the DB.
    - If id_list is None:
        * force=False: update only rows missing center_x or center_y
        * force=True:  update all rows
    - If id_list is provided:
        * force=False: update only those among id_list that are missing
        * force=True:  overwrite centers for those ids
    Returns: number of rows updated.
    """
    with conn.cursor() as cur:
        if id_list is None:
            cur.execute(
                f"SELECT id FROM {table}"
                if force else
                f"SELECT id FROM {table} WHERE center_x IS NULL OR center_y IS NULL"
            )
            ids = [r[0] for r in cur.fetchall()]
        else:
            ids = list(id_list)
            if not force and ids:
                placeholders = ",".join(["%s"] * len(ids))
                cur.execute(
                    f"SELECT id FROM {table} WHERE id IN ({placeholders}) AND (center_x IS NULL OR center_y IS NULL)",
                    ids
                )
                ids = [r[0] for r in cur.fetchall()]

    if not ids:
        return 0

    updates = []
    for tid in ids:
        cx, cy = find_center_for_task(tid, conn, table)
        updates.append((cx, cy, tid))

    updated = 0
    with conn.cursor() as cur:
        for i in range(0, len(updates), batch_size):
            chunk = updates[i:i+batch_size]
            cur.executemany(f"UPDATE {table} SET center_x=%s, center_y=%s WHERE id=%s", chunk)
            updated += cur.rowcount
    conn.commit()
    return updated
