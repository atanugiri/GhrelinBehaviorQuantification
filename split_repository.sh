#!/bin/bash

# Shell script to split GhrelinBehaviorQuantification into two repositories:
# 1. DLCDatabaseSetup - Generic DLC to PostgreSQL pipeline
# 2. GhrelinBehaviorQuantification - Ghrelin-specific analysis

set -e  # Exit on error

echo "=========================================="
echo "Repository Split Script"
echo "=========================================="
echo ""

# Get the current directory (should be GhrelinBehaviorQuantification)
CURRENT_DIR="$(pwd)"
PARENT_DIR="$(dirname "$CURRENT_DIR")"

# Define new repository paths
REPO1_DIR="$PARENT_DIR/DLCDatabaseSetup"
REPO2_DIR="$CURRENT_DIR"  # Keep current location

echo "Current directory: $CURRENT_DIR"
echo "Parent directory: $PARENT_DIR"
echo "DLCDatabaseSetup will be created at: $REPO1_DIR"
echo ""

# Confirm before proceeding
read -p "Do you want to proceed with the repository split? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Operation cancelled."
    exit 0
fi

echo ""
echo "=========================================="
echo "Step 1: Creating DLCDatabaseSetup repository"
echo "=========================================="

# Create new repository directory
mkdir -p "$REPO1_DIR"
cd "$REPO1_DIR"

# Initialize git repository
git init
echo "Git repository initialized in $REPO1_DIR"

# Create directory structure
mkdir -p notebooks
mkdir -p scripts/Extract_db_columns
mkdir -p scripts/Insert_to_featuretable
mkdir -p data

echo "Directory structure created."

echo ""
echo "=========================================="
echo "Step 2: Copying files to DLCDatabaseSetup"
echo "=========================================="

# Copy notebooks (10-23)
cd "$CURRENT_DIR"
echo "Copying database setup notebooks..."
cp DLC-Jupyter-Notebooks/10_DLCjupyter.ipynb "$REPO1_DIR/notebooks/" 2>/dev/null || echo "  10_DLCjupyter.ipynb not found, skipping"
cp DLC-Jupyter-Notebooks/20_set_up_deeplabcut_db.ipynb "$REPO1_DIR/notebooks/" 2>/dev/null || echo "  20_set_up_deeplabcut_db.ipynb not found, skipping"
cp DLC-Jupyter-Notebooks/21_insert_features_to_db.ipynb "$REPO1_DIR/notebooks/" 2>/dev/null || echo "  21_insert_features_to_db.ipynb not found, skipping"
cp DLC-Jupyter-Notebooks/22_normalizedCSVs.ipynb "$REPO1_DIR/notebooks/" 2>/dev/null || echo "  22_normalizedCSVs.ipynb not found, skipping"
cp DLC-Jupyter-Notebooks/23_insert_features_to_db.ipynb "$REPO1_DIR/notebooks/" 2>/dev/null || echo "  23_insert_features_to_db.ipynb not found, skipping"

# Copy Python_scripts/Extract_db_columns
echo "Copying Extract_db_columns scripts..."
cp -r Python_scripts/Extract_db_columns/* "$REPO1_DIR/scripts/Extract_db_columns/" 2>/dev/null || echo "  Extract_db_columns directory issue"

# Copy Python_scripts/Insert_to_featuretable
echo "Copying Insert_to_featuretable scripts..."
cp -r Python_scripts/Insert_to_featuretable/* "$REPO1_DIR/scripts/Insert_to_featuretable/" 2>/dev/null || echo "  Insert_to_featuretable directory issue"

# Copy config.py and __init__.py
echo "Copying configuration files..."
cp Python_scripts/config.py "$REPO1_DIR/scripts/" 2>/dev/null || echo "  config.py not found"
cp Python_scripts/__init__.py "$REPO1_DIR/scripts/" 2>/dev/null || echo "  __init__.py not found"

# Copy root files
echo "Copying root configuration files..."
cp environment.yml "$REPO1_DIR/" 2>/dev/null || echo "  environment.yml not found"
cp requirements.txt "$REPO1_DIR/" 2>/dev/null || echo "  requirements.txt not found"
cp .gitignore "$REPO1_DIR/" 2>/dev/null || echo "  .gitignore not found"

# Create placeholder DATA_README.md in Repo1
cat > "$REPO1_DIR/data/DATA_README.md" << 'EOF'
# Data Directory

This directory is where your `dlc_table` CSV files should be placed.

## Expected Format

The database ingestion scripts expect CSV files with the following columns:
- `id`: Unique identifier for each trial
- `task`: Experimental task name
- `modulation`: Treatment/modulation applied
- `video_path`: Path to the corresponding video file

## Usage

1. Place your DLC output CSVs in this directory
2. Run the notebooks in `notebooks/` to ingest data into PostgreSQL
3. The `config.py` file in `scripts/` will read from this directory

## Note

Video files should NOT be committed to git. Only CSV metadata files should be tracked.
EOF

echo "Data README created."

echo ""
echo "=========================================="
echo "Step 3: Creating README for DLCDatabaseSetup"
echo "=========================================="

cat > "$REPO1_DIR/README.md" << 'EOF'
# DLCDatabaseSetup

A reusable pipeline for ingesting DeepLabCut (DLC) pose-estimation data into a PostgreSQL database.

## Overview

This repository provides a modular workflow to:
1. Process DLC output CSV files
2. Extract metadata from video filenames
3. Normalize body part coordinates
4. Store pose data and metadata in a PostgreSQL database

The pipeline is designed to be experiment-agnostic and can be adapted for any DLC project.

## Repository Structure

```
DLCDatabaseSetup/
├── notebooks/                      # Jupyter notebooks for database setup
│   ├── 10_DLCjupyter.ipynb        # DLC project setup
│   ├── 20_set_up_deeplabcut_db.ipynb  # Database initialization
│   ├── 21_insert_features_to_db.ipynb # Data ingestion (method 1)
│   ├── 22_normalizedCSVs.ipynb    # Coordinate normalization
│   └── 23_insert_features_to_db.ipynb # Data ingestion (method 2)
├── scripts/                        # Python utility modules
│   ├── Extract_db_columns/        # Metadata extraction functions
│   ├── Insert_to_featuretable/    # Database insertion utilities
│   └── config.py                  # Database connection configuration
├── data/                           # Input CSV files (not tracked)
├── environment.yml                 # Conda environment specification
└── requirements.txt                # Pip package list

```

## Setup

### 1. Environment Setup

```bash
# Create conda environment
conda env create -f environment.yml
conda activate DLC

# Or install with pip
pip install -r requirements.txt
```

### 2. Database Configuration

Edit `scripts/config.py` to configure your PostgreSQL connection:

```python
def get_conn():
    return psycopg2.connect(
        dbname="your_database_name",
        user="your_username",
        password="your_password",
        host="your_host",
        port="5432"
    )
```

### 3. Data Preparation

Place your DLC output CSV files in the `data/` directory. The expected format is documented in `data/DATA_README.md`.

## Workflow

1. **Initialize Database** (`20_set_up_deeplabcut_db.ipynb`)
   - Creates `dlc_table` and related schemas
   - Defines columns: id, video_name, task, modulation, etc.

2. **Normalize Coordinates** (`22_normalizedCSVs.ipynb`)
   - Converts pixel coordinates to normalized arena coordinates
   - Applies coordinate transformations based on arena boundaries

3. **Insert Data** (`21_insert_features_to_db.ipynb` or `23_insert_features_to_db.ipynb`)
   - Ingests DLC CSV files into PostgreSQL
   - Extracts metadata from video filenames
   - Validates likelihood thresholds

## Output

The pipeline produces a PostgreSQL database with the following structure:

- **dlc_table**: Metadata for each trial (id, task, modulation, video_path, etc.)
- **pose tables**: Coordinate data for each body part (x, y, likelihood per frame)

## Dependencies

- Python 3.8+
- DeepLabCut 2.3.9
- PostgreSQL
- Key packages: pandas, numpy, psycopg2, scipy

See `requirements.txt` for full list.

## Integration with Analysis Pipelines

This repository provides the database foundation. For ghrelin-specific behavioral analysis, see:
- [GhrelinBehaviorQuantification](https://github.com/atanugiri/GhrelinBehaviorQuantification)

## Citation

If you use this pipeline, please cite:
- DeepLabCut: Mathis et al. (2018) Nature Neuroscience
- This repository: [Add Zenodo DOI when available]

## License

[Specify your license]

## Contact

For questions or issues, please open a GitHub issue or contact [your email].
EOF

echo "README.md created for DLCDatabaseSetup."

echo ""
echo "=========================================="
echo "Step 4: Committing DLCDatabaseSetup repository"
echo "=========================================="

cd "$REPO1_DIR"
git add .
git commit -m "Initial commit: DLC to PostgreSQL pipeline

- Database setup notebooks (10-23)
- Metadata extraction utilities
- Data ingestion scripts
- Configuration management"

echo "Initial commit created for DLCDatabaseSetup."
echo ""
echo "To push to GitHub, run:"
echo "  cd $REPO1_DIR"
echo "  git remote add origin <your-repo-url>"
echo "  git push -u origin main"

echo ""
echo "=========================================="
echo "Step 5: Cleaning up GhrelinBehaviorQuantification"
echo "=========================================="

cd "$CURRENT_DIR"

echo "Removing database setup notebooks from GhrelinBehaviorQuantification..."
rm -f DLC-Jupyter-Notebooks/10_DLCjupyter.ipynb
rm -f DLC-Jupyter-Notebooks/20_set_up_deeplabcut_db.ipynb
rm -f DLC-Jupyter-Notebooks/21_insert_features_to_db.ipynb
rm -f DLC-Jupyter-Notebooks/22_normalizedCSVs.ipynb
rm -f DLC-Jupyter-Notebooks/23_insert_features_to_db.ipynb

echo "Removing Extract_db_columns directory..."
rm -rf Python_scripts/Extract_db_columns

echo "Removing Insert_to_featuretable directory..."
rm -rf Python_scripts/Insert_to_featuretable

echo ""
echo "=========================================="
echo "Step 6: Updating README for GhrelinBehaviorQuantification"
echo "=========================================="

cat > "$CURRENT_DIR/README_updated.md" << 'EOF'
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
EOF

echo "Updated README created as README_updated.md"
echo ""
echo "To apply the updated README, run:"
echo "  mv README_updated.md README.md"

echo ""
echo "=========================================="
echo "SPLIT COMPLETE!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  ✓ Created DLCDatabaseSetup at: $REPO1_DIR"
echo "  ✓ Copied database setup files"
echo "  ✓ Created README for DLCDatabaseSetup"
echo "  ✓ Initialized git repository"
echo "  ✓ Removed database setup files from GhrelinBehaviorQuantification"
echo "  ✓ Created updated README (README_updated.md)"
echo ""
echo "Next steps:"
echo "  1. Review DLCDatabaseSetup at: $REPO1_DIR"
echo "  2. Push DLCDatabaseSetup to GitHub"
echo "  3. Replace README: mv README_updated.md README.md"
echo "  4. Commit changes to GhrelinBehaviorQuantification"
echo "  5. Test both repositories independently"
echo ""
echo "Done!"
