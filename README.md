# GhrelinBehaviorQuantification

Behavioral analysis pipeline for DeepLabCut pose-estimation data from ghrelin experiments.

## Overview

This repository contains a complete **CSV-based** analysis pipeline for quantifying behavioral features from DeepLabCut tracking data. The pipeline computes motion features (velocity, distance), trajectory curvature, and head-body angle features, with statistical comparisons across experimental groups.

## Repository Structure

```
├── DLC-Jupyter-Notebooks/     # Analysis notebooks
│   ├── 2x_data_analysis.ipynb     # 2X dose analysis
│   └── 10x_data_analysis.ipynb    # 10X dose analysis
├── Python_scripts/            # Core analysis modules
│   ├── config.py                  # Project configuration & CSV loader
│   ├── Feature_functions/         # Feature computation
│   │   ├── motion_features.py
│   │   ├── trajectory_curvature.py
│   │   ├── angle_features.py
│   │   └── db_utils.py
│   └── Data_analysis/             # Analysis utilities
│       ├── fetch_id_list.py
│       ├── plot_groupwise_bar.py
│       └── normalized_bodypart.py
├── data/                      # Data directory
│   ├── dlc_table.csv             # Trial metadata (tracked in repo)
│   └── DlcDataPytorchFiltered/   # DeepLabCut CSV outputs (by strain/magnification)
└── environment.yml            # Conda environment
```

## Quick Start

**Prerequisites:** Conda or Miniconda installed

1. **Clone and setup environment:**
```bash
git clone https://github.com/atanugiri/GhrelinBehaviorQuantification.git
cd GhrelinBehaviorQuantification
conda env create -f environment.yml
conda activate ghrelin
```

2. **Run analysis in VS Code or Jupyter Lab:**

   **Option A - VS Code (Recommended):**
   - Open the project folder in VS Code
   - Open any notebook in `DLC-Jupyter-Notebooks/`
   - Select the `ghrelin` kernel from the kernel picker (top right)
   - Run cells sequentially

   **Option B - Jupyter Lab:**
   ```bash
   jupyter lab
   ```
   - Navigate to `DLC-Jupyter-Notebooks/`
   - Open `2x_data_analysis.ipynb` or `10x_data_analysis.ipynb`
   - Select the `ghrelin` kernel if prompted
   - Execute cells in order

## Analysis Notebooks

### Main Analysis Notebooks

- **`2x_data_analysis.ipynb`**: Analyzes 2X dose experiments
  - Compares Saline vs Ghrelin groups
  - Computes velocity, curvature, and angle features
  - Generates statistical plots for all task conditions

- **`10x_data_analysis.ipynb`**: Analyzes 10X dose experiments
  - Compares Saline vs Ghrelin groups
  - Same feature analyses as 2X notebook
  - Handles NaN modulation values correctly

Both notebooks:
- Load data from `dlc_table.csv` 
- Support all task conditions: AllTask, FoodOnly, FoodLight, ToyOnly, ToyLight, LightOnly
- Generate PDF plots and Excel exports
- Use Welch's t-test for statistical comparisons

## Data

**DeepLabCut pose-estimation CSVs:**
See `data/DATA_README.md` for download, extraction, and archive details for the DeepLabCut CSVs (the archive is named `DlcDataPytorchFiltered.zip`).

**Trial metadata:**
`data/dlc_table.csv` contains trial IDs, experimental conditions, and CSV paths. This file is tracked in the repository and may be regenerated from raw video/CSV metadata using the `DLCDatabaseSetup` repository tools:

https://github.com/atanugiri/DLCDatabaseSetup/tree/main

**Directory structure:**
The `data/` folder should contain:
- `dlc_table.csv` - Trial metadata
- `DlcDataPytorchFiltered/` - DeepLabCut CSV outputs, organized by strain/magnification and task (e.g., `WhiteAnimals10X/FoodOnly/...`)

CSV paths in `dlc_table.csv` are relative (e.g., `data/DlcDataPytorchFiltered/WhiteAnimals10X/FoodOnly/...`) and are resolved by `config.py`.