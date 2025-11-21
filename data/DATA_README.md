# data/ — data placeholder and layout

This folder is a repository-local placeholder describing where small, shareable data artifacts should live. Only include small, derived or metadata files (for example, DeepLabCut-generated CSV exports). Do NOT commit large raw video files into the repository; instead store them on external storage and reference them from metadata CSVs.

Recommended layout and conventions

- `data/dlc_table_YYYYMMDD.csv` — CSV export(s) of the PostgreSQL `dlc_table` metadata table. Filenames may be grouped by experimental condition (e.g., `dlc_table_saline.csv`, `dlc_table_ghrelin.csv`). The notebooks expect files matching the glob `dlc_table_*.csv` when using the CSV fallback. These are the primary files that should be placed in `data/`.

- `data/metadata_<note>.csv` — any small metadata tables (e.g., video path mappings, trial exclusions) used by notebooks.

- `data/README` or `data/DATA_README.md` — this file describing conventions.

Notes about the database and CSV fallback

- Notebooks call `Python_scripts.config.get_conn()` to attempt a PostgreSQL connection. If a DB connection is unavailable they call `Python_scripts.config.get_data_dir()` and look for `dlc_table_*.csv` under that path (or `data/` if configured to do so).

- For reproducible archiving, export your `dlc_table` from PostgreSQL as CSV and place the exported CSV(s) in `data/` before running the notebooks.

Video files

- Raw video files are large and should be stored outside the git repo (network drive, S3, or lab server). Put a small CSV in `data/` that maps `trial_id` to a remote or local path and use `resolve_video_path()` in the notebooks to map stored paths to local files when available. Do not add raw videos to version control. To help prevent accidental commits, this repository provides a top-level `.gitignore` that ignores common video file extensions.

## External archive (recommended for large datasets)

This repository is intended to store code, notebooks, and small metadata CSVs only. For the full dataset (raw videos and the matching DeepLabCut CSV exports) we recommend using an external data archive. For this project the dataset is hosted at Harvard Dataverse:

https://doi.org/10.7910/DVN/WHH7W2

Do NOT commit the full dataset to GitHub. Instead, instruct users/reviewers to download the archive from Dataverse and extract it into the repository `data/` folder. The notebooks will then find the expected CSVs (for example `dlc_table_*.csv`) under `data/`.

### Download & extract (example commands)

1. Download (browser or command line):

   curl -L -o ghrelin_dataset.tar.gz "https://dataverse.harvard.edu/api/access/datafile/<<file-id>>"

   Replace `<<file-id>>` with the Dataverse-accessible file id or use the web download link provided on the Dataverse page.

2. Extract into `data/`:

   mkdir -p data
   tar -xzf ghrelin_dataset.tar.gz -C data/

3. Verify checksums if a `SHA256SUMS` file is provided:

   shasum -a 256 -c data/SHA256SUMS

4. Run notebooks from repository root (so imports and relative paths resolve):

   jupyter lab

If you prefer, we can add a small helper script `scripts/download_data.sh` to automate these steps.

Checksums and minimal sample data

- For reproducibility, include SHA256 checksums for any CSVs you add (create a `SHA256SUMS` file in `data/` listing filenames and checksums). If you wish to provide a tiny sample for reviewers, include a small trimmed CSV with a clear filename (e.g., `dlc_table_sample.csv`) and document its provenance in this file.

Short reproduction example

1. Export `dlc_table` from Postgres:

   psql -h <host> -U <user> -d <db> -c "COPY (SELECT * FROM dlc_table) TO STDOUT WITH CSV HEADER" > data/dlc_table_20251121.csv

2. Compute checksums:

   shasum -a 256 data/dlc_table_20251121.csv > data/SHA256SUMS

3. Start Jupyter from repository root and run `DLC-Jupyter-Notebooks/37_data_analysis_curvature.ipynb`.

Short reproduction example

1. Export `dlc_table` from Postgres:

   psql -h <host> -U <user> -d <db> -c "COPY (SELECT * FROM dlc_table) TO STDOUT WITH CSV HEADER" > data/dlc_table_20251121.csv

2. Start Jupyter from repository root and run `DLC-Jupyter-Notebooks/37_data_analysis_curvature.ipynb`.

(Feel free to edit this file to reflect your lab's storage conventions.)