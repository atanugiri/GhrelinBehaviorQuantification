# GhrelinBehaviorQuantification

Behavioral analysis pipeline for DeepLabCut pose-estimation data from ghrelin experiments. Computes speed, trajectory curvature, and head-body angle features with statistical comparisons across experimental groups.

## Repository Structure

```
├── run_analysis.py            # Main entrypoint
├── runme.sh                   # Reproduces all results in one shot
├── scripts/
│   ├── config.py
│   ├── features/              # motion_features.py, trajectory_curvature.py, angle_features.py
│   └── analysis/              # fetch_id_list.py, plot_groupwise_bar.py, plot_trajectories.py, ...
├── data/
│   ├── dlc_table.csv
│   └── DlcDataPytorchFiltered/
├── results/                   # Generated on run
└── environment.yml
```

## Quick Start

```bash
git clone https://github.com/atanugiri/GhrelinBehaviorQuantification.git
cd GhrelinBehaviorQuantification
conda env create -f environment.yml
conda activate ghrelin
bash runme.sh
```

## Usage

```bash
python run_analysis.py --feature FEATURE [--dose-mult N] [--tasks TASK ...] [--include-chemo]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--feature` | `curvature` | `curvature`, `speed`, or `angle` |
| `--dose-mult` | `2` | Dose multiplier (`2` or `10`) |
| `--tasks` | all 5 tasks | Task names, or `AllTask` |
| `--include-chemo` | off | Add Saline vs Inhibitory vs Excitatory comparison |

Outputs are saved to `results/<feature>/White_<N>X_<task>_<comparison>_<feature>.{xlsx,pdf}`.

Trajectory figures (fixed ID sets) are produced by:
```bash
python -m scripts.analysis.plot_trajectories
```

## Features

- **Curvature**: `Midback` bodypart, window 23
- **Speed**: `Head` bodypart, window 5, no smoothing
- **Angle**: head-body misalignment p95, likelihood threshold 0.65

Task conditions: `FoodOnly`, `FoodLight`, `ToyOnly`, `ToyLight`, `LightOnly`. Statistical comparisons use Welch's t-test.

## Data

See `data/DATA_README.md` for the DeepLabCut CSV archive (`DlcDataPytorchFiltered.zip`). CSV paths in `dlc_table.csv` are relative and resolved by `scripts/config.py`.
