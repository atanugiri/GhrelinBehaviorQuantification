"""
Utility functions for the Feature_functions package.

CSV-based data access functions for trial metadata and file paths.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, Union


def get_trial_meta(dlc_table: pd.DataFrame, trial_id: int) -> Tuple[Optional[float], Optional[float]]:
    """
    Returns (trial_length_seconds, frame_rate_fps) from dlc_table DataFrame.
    
    Args:
        dlc_table: DataFrame containing trial metadata
        trial_id: Trial identifier
        
    Returns:
        Tuple of (trial_length_s, frame_rate_fps), or (None, None) if not found
    """
    row = dlc_table[dlc_table['id'] == trial_id]
    
    if row.empty:
        return None, None
    
    trial_length = row['trial_length'].iloc[0] if 'trial_length' in row.columns else None
    frame_rate = row['frame_rate'].iloc[0] if 'frame_rate' in row.columns else None
    
    # Convert to float if not None
    trial_length = float(trial_length) if trial_length is not None and pd.notna(trial_length) else None
    frame_rate = float(frame_rate) if frame_rate is not None and pd.notna(frame_rate) else None
    
    return trial_length, frame_rate


def get_csv_path(dlc_table: pd.DataFrame, trial_id: int) -> str:
    """
    Get CSV file path from dlc_table DataFrame for a given trial ID.
    Converts relative paths to absolute paths from project root.
    
    Args:
        dlc_table: DataFrame containing trial metadata
        trial_id: Trial identifier
        
    Returns:
        CSV file path as string (absolute path resolved from project root)
        
    Raises:
        ValueError: If CSV path not found for the trial ID
    """
    row = dlc_table[dlc_table['id'] == trial_id]
    
    if row.empty or 'csv_file_path' not in row.columns:
        raise ValueError(f"csv_file_path not found for id={trial_id}")
    
    csv_path = row['csv_file_path'].iloc[0]
    
    if pd.isna(csv_path):
        raise ValueError(f"csv_file_path is None for id={trial_id}")
    
    csv_path = str(csv_path)
    
    # If path is relative, resolve it from project root
    if not Path(csv_path).is_absolute():
        # Get project root (2 levels up from this file: db_utils.py -> Feature_functions -> Python_scripts -> root)
        project_root = Path(__file__).resolve().parents[2]
        csv_path = str(project_root / csv_path)
    
    return csv_path