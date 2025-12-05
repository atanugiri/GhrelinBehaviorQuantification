import pandas as pd
from typing import Sequence, Optional, Tuple, List, Union
from pathlib import Path

def fetch_id_list(
    conn_or_df: Union[object, pd.DataFrame],
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
    
    Args:
        conn_or_df: Either a database connection object or a pandas DataFrame (dlc_table)
    """
    bad_ids = set(bad_ids or [])
    
    # Determine if using database or DataFrame
    use_df = isinstance(conn_or_df, pd.DataFrame)
    
    if use_df:
        # CSV/DataFrame mode
        dlc_table = conn_or_df.copy()
        
        def _run_df(label, health, modulation):
            # Apply filters
            df = dlc_table.loc[
                (dlc_table['genotype'] == genotype) &
                (dlc_table['dose_mult'] == dose_mult) &
                (dlc_table['health'] == health)
            ].copy()
            
            # Handle modulation filter (match both "NA" string and NaN/null values)
            if modulation == "NA":
                # For "NA", match both the string "NA" and NaN values
                mask = (df['modulation'] == "NA") | (df['modulation'].isna())
                df = df.loc[mask]
            else:
                # For specific modulations, exact match
                df = df.loc[df['modulation'] == modulation]
            
            # Task filter
            if task_name is not None:
                if isinstance(task_name, (list, tuple, set)):
                    df = df[df['task'].isin(task_name)]
                else:
                    df = df[df['task'] == task_name]
            
            # Min trial length filter
            if min_trial_length is not None:
                df = df[df['trial_length'] >= min_trial_length]
            
            # Remove bad IDs
            if not df.empty:
                df = df[~df['id'].isin(bad_ids)].copy()
            
            # Optional CSV export
            if csv_prefix:
                df.to_csv(f"{csv_prefix}_{label}.csv", index=False)
            
            return df['id'].tolist()
        
        saline_id  = _run_df("saline",     health="saline",  modulation="NA")
        ghrelin_id = _run_df("ghrelin",    health="ghrelin", modulation="NA")
        Exc_id     = _run_df("excitatory", health="saline",  modulation="Excitatory")
        Inh_id     = _run_df("inhibitory", health="ghrelin", modulation="Inhibitory")
        
    else:
        # Database mode (legacy)
        conn = conn_or_df
        
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

# --- Main Test Block ----------------------------------------------------------

if __name__ == "__main__":
    import sys
    from pathlib import Path
    # Add project root to sys.path for module imports
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    from Python_scripts.config import load_dlc_table

    # Load dlc_table.csv (default location)
    try:
        dlc_table = load_dlc_table()
    except Exception as e:
        print(f"Error loading dlc_table.csv: {e}")
        sys.exit(1)

    # Example usage: fetch IDs for LightOnly, dose_mult=10, genotype='white'
    saline_id, ghrelin_id, Exc_id, Inh_id = fetch_id_list(
        dlc_table,
        task_name="FoodOnly",
        dose_mult=2,
        genotype="white",
        bad_ids=None,
        csv_prefix=None,
        min_trial_length=None
    )
    print(f"Saline IDs: {saline_id}")
    print(f"Ghrelin IDs: {ghrelin_id}")
    print(f"Excitatory IDs: {Exc_id}")
    print(f"Inhibitory IDs: {Inh_id}")
