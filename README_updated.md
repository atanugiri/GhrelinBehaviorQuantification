# GhrelinBehaviorQuantification

Behavioral analysis pipeline for ghrelin-modulated exploratory behavior in mice, using DeepLabCut pose-estimation data.

## Overview

This repository contains analysis code for quantifying behavioral features from pose-estimation data. The pipeline computes:
- **Trajectory curvature**: Local path curvature at each timepoint
- **Velocity features**: Speed, distance traveled, and angular velocity
- **Angle features**: Head-body misalignment, tail bend index

For database setup and data ingestion, see the companion repository:
- [DLCDatabaseSetup](https://github.com/atanugiri/DLCDatabaseSetup)

## Repository Structure

```
GhrelinBehaviorQuantification/
├── DLC-Jupyter-Notebooks/          # Analysis notebooks
│   ├── 30_data_analysis.ipynb     # General analysis
│   ├── 31_data_analysis_distance.ipynb  # Distance metrics
│   ├── 37_data_analysis_curvature.ipynb # Curvature analysis
│   └── 40_data_analysis_angle_features.ipynb  # Angle features
├── Python_scripts/
│   ├── Feature_functions/          # Feature computation modules
│   │   ├── trajectory_curvature.py
│   │   ├── motion_features.py
│   │   └── angle_features.py
│   ├── Data_analysis/              # Statistical analysis and plotting
│   └── Utility_functions/          # Helper utilities
├── data/                           # Sample data for testing
│   ├── dlc_table_sample.csv       # Minimal test dataset
│   └── DATA_README.md             # Data documentation
├── environment.yml                 # Conda environment
└── requirements.txt                # Pip packages

```

## Data Availability

**Full Dataset**: The complete behavioral dataset is archived on Harvard Dataverse:
- DOI: [10.7910/DVN/WHH7W2](https://doi.org/10.7910/DVN/WHH7W2)
- Includes: `dlc_table` CSV files with pose coordinates and metadata

**Sample Data**: A minimal test dataset (`data/dlc_table_sample.csv`) is included in this repository for quick testing without downloading the full archive.

## Code Availability

This code is archived on Zenodo:
- DOI: [10.5281/zenodo.17280634](https://zenodo.org/records/17280634)

## Setup

### 1. Prerequisites

You need a PostgreSQL database populated with DLC data. To set this up:
1. Clone the [DLCDatabaseSetup](https://github.com/atanugiri/DLCDatabaseSetup) repository
2. Follow its setup instructions to create and populate your database
3. Return here for analysis

### 2. Environment Setup

```bash
# Create conda environment
conda env create -f environment.yml
conda activate DLC

# Or install with pip
pip install -r requirements.txt
```

### 3. Download Full Dataset (Optional)

For full analysis, download data from Harvard Dataverse:

```bash
# Visit https://doi.org/10.7910/DVN/WHH7W2
# Download dlc_table CSV files to data/ directory
```

### 4. Configure Database Connection

Edit `Python_scripts/config.py` to point to your PostgreSQL database (created via DLCDatabaseSetup).

## Workflow

### Analysis Notebooks

Run notebooks in sequence:

1. **30_data_analysis.ipynb**: General behavioral metrics
2. **31_data_analysis_distance.ipynb**: Distance traveled, velocity
3. **37_data_analysis_curvature.ipynb**: Trajectory curvature analysis
4. **40_data_analysis_angle_features.ipynb**: Angular features

### Feature Computation

Key modules in `Python_scripts/Feature_functions/`:

- `trajectory_curvature.py`: Computes curvature κ(t) = |ẋÿ - ẏẍ| / (ẋ² + ẏ²)^(3/2)
- `motion_features.py`: Speed, distance, acceleration
- `angle_features.py`: Head-body angle, tail bend, angular velocity

### Statistical Outputs

All statistical outputs are generated in the analysis notebooks and include:
- Summary statistics (mean ± SEM) per treatment group
- Distribution comparisons (t-tests, ANOVA)
- Plots saved to notebook output or specified directories

## Dependencies

- Python 3.8.20
- DeepLabCut 2.3.9
- PostgreSQL (via psycopg2)
- Analysis: pandas 2.0.3, numpy 1.24.4, scipy 1.10.1, matplotlib 3.7.5, scikit-learn 1.3.2

See `requirements.txt` for complete list.

## Citation

If you use this code or data, please cite:
- This repository: [10.5281/zenodo.17280634](https://zenodo.org/records/17280634)
- Dataset: [10.7910/DVN/WHH7W2](https://doi.org/10.7910/DVN/WHH7W2)
- DeepLabCut: Mathis et al. (2018) Nature Neuroscience

## Related Repositories

- [DLCDatabaseSetup](https://github.com/atanugiri/DLCDatabaseSetup): Generic DLC to PostgreSQL pipeline

## License

[Specify your license]

## Contact

For questions or issues, please open a GitHub issue.
