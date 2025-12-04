# GhrelinBehaviorQuantification

Behavioral analysis pipeline for DeepLabCut pose-estimation data from ghrelin experiments.

## Overview

This repository contains a complete **CSV-based** analysis pipeline for quantifying behavioral features from DeepLabCut tracking data. The pipeline computes motion features (velocity, distance), trajectory curvature, and head-body angle features, with statistical comparisons across experimental groups.

**Key Features:**
- Pure CSV workflow (no database required)
- Minimal Python environment (Python 3.10, pandas, numpy, scipy, matplotlib, seaborn, opencv)
- Reproducible analyses with tracked metadata
- Statistical testing with Welch's t-test and effect sizes

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
│   ├── dlc_table.csv             # Trial metadata
│   ├── WhiteAnimals/             # DeepLabCut CSVs
│   └── BlackAnimals/             # DeepLabCut CSVs
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

## Data

**DeepLabCut pose-estimation CSVs:**  
Available at Harvard Dataverse: https://doi.org/10.7910/DVN/G8CBKJ

**Trial metadata:**  
`data/dlc_table.csv` contains trial IDs, experimental conditions, and CSV paths. This file is tracked in the repository.

**Directory structure:**  
The `data/` folder should contain:
- `dlc_table.csv` - Trial metadata
- `WhiteAnimals/` - DeepLabCut tracking CSVs organized by task
- `BlackAnimals/` - DeepLabCut tracking CSVs organized by task

CSV paths in `dlc_table.csv` are relative (e.g., `data/WhiteAnimals/ToyOnly/...`) and automatically resolved by `config.py`.

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

## Statistical Analysis

All comparisons use **Welch's t-test** (unpaired, unequal variance) via `scipy.stats.ttest_ind(equal_var=False)`. The `plot_groupwise_bar()` function computes:
- Test statistics and p-values
- Cohen's d effect sizes
- Significance annotations (*, **, ***)

## Output Files

Notebooks generate in the working directory:
- **PDF figures**: `White_{dose}_{task}_{feature}.pdf` (e.g., `White_10X_AllTask_velocity.pdf`)
- **Excel files**: `{dose}_White_{task}_{comparison}_{feature}.xlsx` (optional export)

## Development

- Run notebooks from repository root for correct imports
- Module structure: Notebooks → Feature functions → Utilities
- CSV-only mode (no database required)
- All paths are resolved automatically by `config.py`

## Contact

Repository: https://github.com/atanugiri/GhrelinBehaviorQuantification