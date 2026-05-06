```
python -m pipelines.concat_csvs \
results/angle_runs/angle_FoodOnly_dose2_white_wNone_all.csv \
results/angle_runs/angle_ToyOnly_dose2_white_wNone_all.csv \
results/angle_runs/angle_LightOnly_dose2_white_wNone_all.csv \
results/angle_runs/angle_FoodLight_dose2_white_wNone_all.csv \
results/angle_runs/angle_ToyLight_dose2_white_wNone_all.csv \
--output 2x_angle_analysis_saline_vs_excitatory.csv
```

```
python -m pipelines.run_angle_analysis \      
  --task-name FoodOnly ToyOnly LightOnly FoodLight ToyLight \
  --dose-mult 2 \
  --plot-groups Saline Inhibitory \
  --results-dir results/angle_runs \
  --min-trial-length 0
```