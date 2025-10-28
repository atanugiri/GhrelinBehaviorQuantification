"""
Feature Functions Package

This package contains modules for computing behavioral features from DeepLabCut data.

Main modules:
- angle_features: Compute angle-based features (head-body misalignment, tail bend, etc.)
- db_utils: Database utility functions (get_trial_meta, get_csv_path, etc.)
- motion_features: Compute motion-based features
- spatial_entropy: Spatial distribution analysis
"""

# Import commonly used functions for easy access
from .db_utils import get_trial_meta, get_csv_path
from .angle_features import angle_features_for_trial, batch_angle_features

# Make these available when someone does: from Feature_functions import *
__all__ = [
    'angle_features_for_trial',
    'batch_angle_features', 
    'get_trial_meta',
    'get_csv_path',
]