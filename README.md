# GhrelinBehaviorQuantification

Behavioral analysis pipeline for DeepLabCut-derived tracking data from ghrelin experiments.

## Project overview

This repository contains the complete analysis pipeline for quantifying behavioral features from DeepLabCut pose-estimation data. The pipeline computes motion features (velocity, distance), trajectory curvature, and head-body angle features, with statistical comparisons across experimental groups.

## Repository structure

- `environment.yml` : Conda environment specification for reproducibility
- `DLC-Jupyter-Notebooks/` : Analysis notebooks for manuscript figures
  - `31_data_analysis_distance.ipynb` : Velocity and distance analysis
  - `37_data_analysis_curvature.ipynb` : Trajectory curvature analysis
  - `40_data_analysis_angle_features.ipynb` : Head-body misalignment analysis
- `Python_scripts/` : Core analysis modules
  - `config.py` : Database connection and data directory configuration
  - `Feature_functions/` : Feature computation modules
    - `angle_features.py` : Head-body angle calculations
    - `motion_features.py` : Velocity, distance, acceleration
    - `trajectory_curvature.py` : Path curvature computation
    - `db_utils.py` : Database utility functions
  - `Data_analysis/` : Analysis and plotting utilities
    - `fetch_id_list.py` : Trial ID filtering by experimental condition
    - `plot_groupwise_bar.py` : Statistical bar plots with Welch's t-test
    - `plot_features.py` : Exploratory plotting functions
    - `compare_distributions.py` : Distribution comparison utilities
    - `normalized_bodypart.py` : Coordinate normalization
- `DATA_DIR` (not a repo file): data directory referenced by `config.get_data_dir()` (used as CSV fallback).

## Quickstart (local)

1. Create and activate conda environment:

```bash
conda env create -f environment.yml
conda activate <env-name-from-yml>
```

2. Start Jupyter (lab or notebook) from repo root and open notebooks in `DLC-Jupyter-Notebooks/`:

```bash
jupyter lab
# or
jupyter notebook
```

3. Notebook notes:
- Notebooks add the project root to `sys.path` (see the top cell of notebooks like `40_data_analysis_angle_features.ipynb`) so scripts in `Python_scripts/` import cleanly.
- Notebooks attempt to connect to a Postgres DB via `Python_scripts.config.get_conn()` and on failure fall back to CSV files found under `DATA_DIR` (configured in `config.py`).

## Configuration and data

- Check `Python_scripts/config.py` for database credentials and data directory resolution. The notebooks handle a fallback to CSVs named like `dlc_table_*.csv` located under `DATA_DIR`.
- If you don't have DB access, place the CSV exports under the path returned by `config.get_data_dir()` or update `config.py` to point to a local folder with the expected CSVs.

### Data location

**Primary dataset (DeepLabCut pose-estimation CSVs):**  
The DeepLabCut pose-estimation output files (CSV format) are archived at Harvard Dataverse: https://doi.org/10.7910/DVN/G8CBKJ. To reproduce the analyses, download the Dataverse archive and extract the pose-estimation CSVs into the `data/` directory of the project root.

**Database table (metadata):**  
The database table (`dlc_table`) containing metadata and trial information is located in the `data/` directory as CSV files (e.g., `dlc_table_*.csv` grouped by experimental condition). A small sample CSV (`dlc_table_sample.csv`) is included in the repository for quick testing without downloading the full dataset.

**Git behaviour:**  
This repository's `.gitignore` allows CSVs and the `data/` folder to be tracked, but ignores common video file extensions (`*.mp4`, `*.avi`, `*.mov`) so raw videos are not accidentally committed. See `data/DATA_README.md` for details.

### Using an external data archive (recommended for large datasets)

For full datasets (raw videos + corresponding DeepLabCut CSV exports) we recommend hosting the complete data externally (for example, Harvard Dataverse) rather than committing large files to GitHub. In our workflow the full dataset is deposited at Harvard Dataverse (DOI: `https://doi.org/10.7910/DVN/WHH7W2`). To run the notebooks locally, instruct users to download and extract the Dataverse archive into the repository `data/` directory so the notebooks can find the expected CSVs and metadata.

Suggested steps for users (place in Methods/Supplementary or README):

1. Download the dataset archive from the Dataverse record: `https://doi.org/10.7910/DVN/WHH7W2`.
2. Extract the archive into the repository `data/` directory (for example `tar -xzf ghrelin_dataset.tar.gz -C data/` or unzip to `data/`).
3. Verify checksums (if provided) with `shasum -a 256 -c data/SHA256SUMS`.
4. Run the notebooks from the project root so they can find metadata CSVs under `data/` or via the path returned by `Python_scripts.config.get_data_dir()`.

### Checksums and minimal sample data

- For reproducibility and archival, we recommend adding SHA256 checksums for CSVs placed in `data/`. Include a `data/SHA256SUMS` file with lines like `SHA256  filename`. If you want reviewers to run the notebooks without full datasets, include a tiny sample CSV named `dlc_table_sample.csv` and document it in `data/DATA_README.md`.

## Analysis notebooks

Each notebook performs a complete analysis workflow from data loading to statistical testing and figure generation:

- **`31_data_analysis_distance.ipynb`**: Computes average velocity per minute for each trial, performs parameter sweeps (smoothing window), and generates statistical comparisons between treatment groups using Welch's t-test.

- **`37_data_analysis_curvature.ipynb`**: Calculates trajectory curvature from normalized body part coordinates, performs window size optimization, and compares curvature distributions across experimental groups.

- **`40_data_analysis_angle_features.ipynb`**: Computes head-body misalignment angles, optimizes likelihood thresholds, and generates publication-ready figures with statistical annotations.

All notebooks support both PostgreSQL database connections and CSV fallback mode for offline analysis.

### Statistical outputs

## Statistical analysis

All statistical comparisons use **Welch's t-test** (unpaired, assuming unequal variance) implemented via `scipy.stats.ttest_ind` with `equal_var=False`. The `plot_groupwise_bar()` function automatically computes test statistics, p-values, and Cohen's d effect sizes, annotating figures with significance stars.

### Output files

Notebooks generate publication-ready outputs in the working directory:
- **PDF figures**: Parameter sweep plots (e.g., `White_2X_AllTask_Head_velocity_window_sweep.pdf`)
- **Individual figures**: Single condition plots with statistics (e.g., `White_10X_AllTask_velocity.pdf`)
- **Excel files**: Trial-level data with metadata for data submission (e.g., `10X_White_Velocity.xlsx`, `10X_White_Angle.xlsx`)

- To reproduce: clone the repository, change to the project root, create the conda environment from `environment.yml`, and run the notebooks from the project root so imports from `Python_scripts/` resolve.
- Do not publish absolute local paths (for example `/Users/atanugiri/...`) in the manuscript; use repository-relative paths such as `DLC-Jupyter-Notebooks/37_data_analysis_curvature.ipynb` and `Python_scripts/Feature_functions/trajectory_curvature.py` instead.

### Sample data for quick testing

- A small sanitized sample of the `dlc_table` metadata is included: `data/dlc_table_sample.csv`. This allows reviewers to run notebooks without downloading the full dataset from Dataverse.
- To use the sample: run notebooks from the project root (notebooks will load CSVs from `data/` when a DB connection is not available).
- For full analyses: download the Dataverse archive (https://doi.org/10.7910/DVN/WHH7W2) and extract into `data/`.
## Module dependencies

The codebase uses a clean dependency structure:
- Notebooks import feature computation functions (e.g., `batch_compute_motion_features_per_minute`, `batch_angle_features`)
- Feature functions use database utilities (`db_utils.py`) and normalization (`normalized_bodypart.py`)
- All plotting uses `plot_groupwise_bar()` for consistent statistical annotation
- The `config.py` module handles database connections with automatic CSV fallback

## Development notes

- Run notebooks from the repository root to ensure `sys.path` includes `Python_scripts/`
- The `gastric` conda environment (from `environment.yml`) includes all dependencies
- For individual script execution: `python -m Python_scripts.Feature_functions.motion_features` (from repo root)
## Recommended next steps

- Add `CONTRIBUTING.md` with development guidelines (how to run notebooks, format code, run tests).
- Add `DB_SETUP.md` with step-by-step database credentials, connection, and how to generate CSV fallbacks.
- Optionally add a small `README-notebooks.md` describing each notebook (purpose and expected inputs/outputs).

## Contact

- Repository owner / maintainer: `atanugiri` (local workspace)

---

(Generated automatically — tell me if you want more detail in any section or want me to also create `CONTRIBUTING.md` and `DB_SETUP.md`.)