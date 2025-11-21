# GhrelinBehaviorQuantification

Short README for the `GhrelinBehaviorQuantification` analysis project.

## Project overview

- Purpose: analysis pipeline for DeepLabCut-derived behavioral tracking data related to ghrelin experiments. Contains Jupyter notebooks for exploratory data analysis and Python scripts to extract/compute behavioral features (e.g., trajectory curvature, angle features, motion metrics) and insert them into a database.

## Repository layout (important items)

- `environment.yml` : conda environment used for reproducible environments.
- `DLC-Jupyter-Notebooks/` : analysis notebooks (e.g., `40_data_analysis_angle_features.ipynb`).
- `Python_scripts/` : reusable scripts and modules including:
  - `config.py` : provides `get_conn()` and `get_data_dir()` used to connect to Postgres or fallback to CSV.
  - `Data_analysis/`, `Feature_functions/`, `Extract_db_columns/`, `Insert_to_featuretable/`, `Utility_functions/` : core analysis utilities and helpers.
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
The DeepLabCut pose-estimation output files (CSV format) are archived at Harvard Dataverse: https://doi.org/10.7910/DVN/WHH7W2. To reproduce the analyses, download the Dataverse archive and extract the pose-estimation CSVs into the `data/` directory of the project root.

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

## Important notebooks

- `DLC-Jupyter-Notebooks/40_data_analysis_angle_features.ipynb` — calculates and plots angle features and exports summary Excel files.
- `DLC-Jupyter-Notebooks/30_data_analysis.ipynb` and related notebooks — other analyses and visualizations.

### Code location

- All analysis code is in `Python_scripts/`. Key subdirectories:
  - `Python_scripts/Feature_functions/` — feature implementations (e.g., `trajectory_curvature.py`, `angle_features.py`, `motion_features.py`)
  - `Python_scripts/Data_analysis/` — analysis helpers and plotting utilities (e.g., `compute_binned_curvature_stats.py`, `plot_groupwise_bar.py`)
  - `Python_scripts/Insert_to_featuretable/` — database insertion utilities
  - `Python_scripts/Extract_db_columns/` — metadata extraction and normalization
- Notebooks (in `DLC-Jupyter-Notebooks/`) import these modules by adding the repository root to `sys.path` (see the top cell in notebooks).

### Statistical outputs

- Figures and statistical reports generated by the notebooks are saved in the working directory when notebooks are executed from the project root. Typical outputs include PDF figures (e.g., `White_Modulation_2X_{task_name}_ang_likelihood_sweep.pdf`) and Excel summary files (e.g., `10X_White_Angle.xlsx`).

### Reproducibility notes (data/code/outputs)

- To reproduce: clone the repository, change to the project root, create the conda environment from `environment.yml`, and run the notebooks from the project root so imports from `Python_scripts/` resolve.
- Do not publish absolute local paths (for example `/Users/atanugiri/...`) in the manuscript; use repository-relative paths such as `DLC-Jupyter-Notebooks/37_data_analysis_curvature.ipynb` and `Python_scripts/Feature_functions/trajectory_curvature.py` instead.

### Sample data for quick testing

- A small sanitized sample of the `dlc_table` metadata is included: `data/dlc_table_sample.csv`. This allows reviewers to run notebooks without downloading the full dataset from Dataverse.
- To use the sample: run notebooks from the project root (notebooks will load CSVs from `data/` when a DB connection is not available).
- For full analyses: download the Dataverse archive (https://doi.org/10.7910/DVN/WHH7W2) and extract into `data/`.

### Code availability

- The project source code, notebooks, and environment files supporting analyses are archived at Zenodo: https://zenodo.org/records/17280634. Cite this record when referring to the code used in the manuscript.

## Development notes

- To run individual scripts, use `python` from the repository root so imports from `Python_scripts` resolve correctly.
- Consider adding a `requirements.txt` or a pinned `environment.yml` environment name for easier activation.

## Recommended next steps

- Add `CONTRIBUTING.md` with development guidelines (how to run notebooks, format code, run tests).
- Add `DB_SETUP.md` with step-by-step database credentials, connection, and how to generate CSV fallbacks.
- Optionally add a small `README-notebooks.md` describing each notebook (purpose and expected inputs/outputs).

## Contact

- Repository owner / maintainer: `atanugiri` (local workspace)

---

(Generated automatically — tell me if you want more detail in any section or want me to also create `CONTRIBUTING.md` and `DB_SETUP.md`.)