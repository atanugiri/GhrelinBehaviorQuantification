#!/usr/bin/env bash
set -euo pipefail

# adjust if you use `python3` or a conda env name
CONDA_ENV=ghrelin
PY=python3

TASKS=(FoodOnly ToyOnly LightOnly FoodLight ToyLight)
DOSE=2
PLOT_GROUPS=(Saline Ghrelin)
RESULTS_DIR=results/curvature_runs
LOGDIR=logs/curvature_runs
mkdir -p "$RESULTS_DIR" "$LOGDIR"

# activate conda env (works in interactive shells)
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$CONDA_ENV"

for t in "${TASKS[@]}"; do
  echo "Running task: $t"
  OUTDIR="$RESULTS_DIR"
  mkdir -p "$OUTDIR"
  LOG="$LOGDIR/${t}.log"
  $PY -m pipelines.run_curvature_analysis \
    --task-name "$t" \
    --dose-mult "$DOSE" \
    --plot-groups "${PLOT_GROUPS[@]}" \
    --results-dir "$OUTDIR" \
    --min-trial-length 0 \
    2>&1 | tee "$LOG"
done