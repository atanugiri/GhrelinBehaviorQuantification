# GhrelinBehaviorQuantification

Behavioral analysis pipeline for DeepLabCut pose-estimation data from ghrelin experiments.

## Overview

This repository contains a complete **CSV-based** analysis pipeline for quantifying behavioral features from DeepLabCut tracking data. The pipeline computes speed, trajectory curvature, and head-body angle features, with statistical comparisons across experimental groups (Saline vs Ghrelin, and optionally Saline vs Inhibitory vs Excitatory).

## Repository Structure

```
├── reproduce_2x_features.py   # Main entrypoint — run all analyses
├── runme.sh                   # One-shot script to reproduce all results
├── scripts/                   # Core analysis modules
│   ├── config.py                  # Project configuration & CSV loader
│   ├── features/         # Feature computation
│   │   ├── motion_features.py
│   │   ├── trajectory_curvature.py
│   │   ├── angle_features.py
│   │   └── db_utils.py
│   └── analysis/             # Analysis utilities
│       ├── fetch_id_list.py
│       ├── plot_groupwise_bar.py
│       └── normalized_bodypart.py
├── data/                      # Data directory
│   ├── dlc_table.csv             # Trial metadata (tracked in repo)
│   └── DlcDataPytorchFiltered/   # DeepLabCut CSV outputs (by strain/magnification)
├── results/                   # Output directory (generated on run)
│   ├── curvature/
│   ├── speed/
│   └── angle/
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

2. **Reproduce all results:**
```bash
bash runme.sh
```
This runs all features (curvature, speed, angle) for both 2X and 10X dose conditions and saves outputs to `results/`.

## Analysis Script

`reproduce_2x_features.py` is the single entrypoint for all analyses.

**Usage:**
```bash
python reproduce_2x_features.py [--feature FEATURE] [--dose-mult N] [--tasks TASK [TASK ...]] [--include-chemo] [--outdir DIR] [--bad-ids ID [ID ...]] [--min-trial-length N]
```

**Key options:**

| Flag | Default | Description |
|------|---------|-------------|
| `--feature` | `curvature` | Feature to analyze: `curvature`, `speed`, or `angle` |
| `--dose-mult` | `2` | Dose multiplier: `2` for 2X, `10` for 10X |
| `--tasks` | all 5 tasks | Space-separated task names, or `AllTask` for all five |
| `--include-chemo` | off | Also run Saline vs Inhibitory vs Excitatory comparison |
| `--outdir` | `results` | Base output directory; outputs go to `<outdir>/<feature>/` |
| `--bad-ids` | preset list | Trial IDs to exclude |

**Examples:**
```bash
# 2X curvature, all tasks, Saline vs Ghrelin
python reproduce_2x_features.py --feature curvature --tasks AllTask

# 2X speed, specific tasks, including chemo comparison
python reproduce_2x_features.py --feature speed --tasks FoodOnly ToyOnly --include-chemo

# 10X angle, all tasks
python reproduce_2x_features.py --feature angle --dose-mult 10 --tasks AllTask
```

**Output files** are saved as `results/<feature>/White_<N>X_<task>_<comparison>_<feature>.{xlsx,pdf}`.

## Features

- **Curvature**: Mean trajectory curvature using `Midback` bodypart, smoothing window 23
- **Speed**: Velocity per minute using `Head` bodypart, window 5, no smoothing
- **Angle**: Head-body misalignment (p95) with likelihood threshold 0.65

All comparisons use Welch's t-test. Per-task XLSX tables and PDF bar plots are saved for each run.

## Task Conditions

Five task conditions are supported: `FoodOnly`, `FoodLight`, `ToyOnly`, `ToyLight`, `LightOnly`. `AllTask` is a shorthand for all five combined.

## Data

**DeepLabCut pose-estimation CSVs:**
See `data/DATA_README.md` for download, extraction, and archive details for the DeepLabCut CSVs (the archive is named `DlcDataPytorchFiltered.zip`).

**Directory structure:**
The `data/` folder should contain:
- `dlc_table.csv` — trial metadata
- `DlcDataPytorchFiltered/` — DeepLabCut CSV outputs, organized by strain/magnification and task (e.g., `WhiteAnimals10X/FoodOnly/...`)

CSV paths in `dlc_table.csv` are relative and resolved by `config.py`.