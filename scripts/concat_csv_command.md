```
python -m pipelines.concat_csvs \
    results/curvature_runs/curvature_FoodOnly_dose2_white_Midback_smooth_w23_all.csv \
    results/curvature_runs/curvature_ToyOnly_dose2_white_Midback_smooth_w23_all.csv \
    results/curvature_runs/curvature_LightOnly_dose2_white_Midback_smooth_w23_all.csv \
    results/curvature_runs/curvature_FoodLight_dose2_white_Midback_smooth_w23_all.csv \
    results/curvature_runs/curvature_ToyLight_dose2_white_Midback_smooth_w23_all.csv \
    --output 2x_curvature_analysis_saline_vs_excitatory.csv
```