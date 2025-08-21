import pandas as pd
from typing import Sequence, Optional, Tuple, List

def fetch_id_list(
    conn,
    task_name: Optional[Sequence[str] | str] = "LightOnly",  # None -> all tasks; list/tuple -> IN (...)
    dose_mult: int = 10,
    genotype: str = "white",
    bad_ids: Optional[Sequence[int]] = None,
    csv_prefix: Optional[str] = None,   # e.g., "dlc_table" -> dlc_table_saline.csv, ...
    min_trial_length: Optional[int] = None
) -> Tuple[List[int], List[int], List[int], List[int]]:
    """
    Returns: (saline_id, ghrelin_id, Exc_id, Inh_id)

    Filters applied to ALL four cohorts:
      - genotype, dose_mult, (optional) min_trial_length
      - task filter: skipped if task_name is None; uses '=' if str; uses IN (...) if list/tuple/set.
    """
    bad_ids = set(bad_ids or [])

    # Always-on filters (no task yet)
    where = ["genotype = %s", "dose_mult = %s"]
    params = [genotype, dose_mult]
    if min_trial_length is not None:
        where.append("trial_length >= %s")
        params.append(min_trial_length)

    # Optional task filter
    if task_name is not None:
        if isinstance(task_name, (list, tuple, set)):
            task_list = list(task_name)
            placeholders = ",".join(["%s"] * len(task_list))
            where.append(f"task IN ({placeholders})")
            params.extend(task_list)
        else:
            where.append("task = %s")
            params.append(task_name)

    base_where_sql = " AND ".join(where)

    def _run(label, health, modulation):
        q = f"""
            SELECT id, video_name, task, health, genotype, modulation, trial_length, dose_mult
            FROM dlc_table
            WHERE {base_where_sql} AND health = %s AND modulation = %s
            ORDER BY id;
        """
        df = pd.read_sql_query(q, conn, params=params + [health, modulation])
        if not df.empty:
            df = df[~df["id"].isin(bad_ids)].copy()
        if csv_prefix:
            df.to_csv(f"{csv_prefix}_{label}.csv", index=False)
        return df["id"].tolist()

    saline_id  = _run("saline",     health="saline",  modulation="NA")
    ghrelin_id = _run("ghrelin",    health="ghrelin", modulation="NA")
    Exc_id     = _run("excitatory", health="saline",  modulation="Excitatory")
    Inh_id     = _run("inhibitory", health="ghrelin", modulation="Inhibitory")

    return saline_id, ghrelin_id, Exc_id, Inh_id
