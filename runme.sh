#!/usr/bin/env bash
set -euo pipefail

# Curvature
python run_analysis.py --feature curvature --tasks AllTask
python run_analysis.py --feature curvature
python run_analysis.py --feature curvature --tasks AllTask --include-chemo
python run_analysis.py --feature curvature --include-chemo

# Speed
python run_analysis.py --feature speed --tasks AllTask
python run_analysis.py --feature speed
python run_analysis.py --feature speed --tasks AllTask --include-chemo
python run_analysis.py --feature speed --include-chemo

# Angle
python run_analysis.py --feature angle --tasks AllTask
python run_analysis.py --feature angle
python run_analysis.py --feature angle --tasks AllTask --include-chemo
python run_analysis.py --feature angle --include-chemo

# 10X (Saline vs Ghrelin only)
python run_analysis.py --dose-mult 10 --feature curvature --tasks AllTask
python run_analysis.py --dose-mult 10 --feature curvature
python run_analysis.py --dose-mult 10 --feature speed --tasks AllTask
python run_analysis.py --dose-mult 10 --feature speed
python run_analysis.py --dose-mult 10 --feature angle --tasks AllTask
python run_analysis.py --dose-mult 10 --feature angle

# Trajectory (individual curvature examples)
# python -m scripts.analysis.plot_trajectories
