#!/usr/bin/env bash
set -euo pipefail

# Curvature
python reproduce_2x_features.py --feature curvature --tasks AllTask
python reproduce_2x_features.py --feature curvature
python reproduce_2x_features.py --feature curvature --tasks AllTask --include-chemo
python reproduce_2x_features.py --feature curvature --include-chemo

# Speed
python reproduce_2x_features.py --feature speed --tasks AllTask
python reproduce_2x_features.py --feature speed
python reproduce_2x_features.py --feature speed --tasks AllTask --include-chemo
python reproduce_2x_features.py --feature speed --include-chemo

# Angle
python reproduce_2x_features.py --feature angle --tasks AllTask
python reproduce_2x_features.py --feature angle
python reproduce_2x_features.py --feature angle --tasks AllTask --include-chemo
python reproduce_2x_features.py --feature angle --include-chemo

# 10X (Saline vs Ghrelin only)
python reproduce_2x_features.py --dose-mult 10 --feature curvature --tasks AllTask
python reproduce_2x_features.py --dose-mult 10 --feature curvature
python reproduce_2x_features.py --dose-mult 10 --feature speed --tasks AllTask
python reproduce_2x_features.py --dose-mult 10 --feature speed
python reproduce_2x_features.py --dose-mult 10 --feature angle --tasks AllTask
python reproduce_2x_features.py --dose-mult 10 --feature angle
