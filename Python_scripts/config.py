"""Configuration helpers for the GhrelinBehaviorQuantification project.

CSV-based data access configuration.

Provides:
- get_project_root(): returns the project root directory
- get_data_dir(): returns the data directory path
- load_dlc_table(): loads dlc_table.csv into a pandas DataFrame
"""
from pathlib import Path
import pandas as pd


def get_project_root() -> Path:
    """Return the project root directory (parent of Python_scripts/)."""
    return Path(__file__).resolve().parents[1]


def get_data_dir() -> Path:
    """Return the data directory path (project_root/data)."""
    return get_project_root() / 'data'


def load_dlc_table(filename: str = 'dlc_table.csv') -> pd.DataFrame:
    """
    Load dlc_table CSV file from the data directory.
    
    Args:
        filename: Name of the CSV file (default: 'dlc_table.csv')
    
    Returns:
        DataFrame containing trial metadata
        
    Raises:
        FileNotFoundError: If the CSV file doesn't exist
    """
    data_dir = get_data_dir()
    csv_path = data_dir / filename
    
    if not csv_path.exists():
        raise FileNotFoundError(
            f"dlc_table CSV not found at {csv_path}\n"
            f"Please ensure the data directory contains {filename}"
        )
    
    return pd.read_csv(csv_path)
