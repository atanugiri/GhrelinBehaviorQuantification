#!/usr/bin/env python3
"""Single entrypoint to run 2X feature analysis per task.

Workflow:
1) Run feature analysis for each task in --tasks.
2) Save per-task outputs as XLSX.
3) Save per-task plots as PDF.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import matplotlib

# Non-interactive backend for script runs
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from scripts.config import load_dlc_table
from scripts.Data_analysis.fetch_id_list import fetch_id_list
from scripts.Data_analysis.plot_groupwise_bar import plot_groupwise_bar
from scripts.Feature_functions.angle_features import batch_angle_features
from scripts.Feature_functions.motion_features import (
    batch_compute_motion_features_per_minute,
)
from scripts.Feature_functions.trajectory_curvature import (
    batch_trajectory_curvature,
)


DEFAULT_BAD_IDS = [120, 130, 137, 138, 141, 142, 166, 289, 293, 310, 312]
DEFAULT_TASKS = ["FoodOnly", "FoodLight", "ToyOnly", "ToyLight", "LightOnly"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run 2X feature analysis per task and save XLSX/PDF outputs."
    )
    parser.add_argument(
        "--feature",
        type=str,
        default="curvature",
        choices=["curvature", "speed", "angle"],
        help="Feature to analyze (default: curvature).",
    )
    parser.add_argument(
        "--dose-mult",
        type=int,
        default=2,
        help="Dose multiplier filter (default: 2).",
    )
    parser.add_argument(
        "--genotype",
        type=str,
        default="white",
        help="Genotype filter (default: white).",
    )
    parser.add_argument(
        "--tasks",
        nargs="+",
        default=DEFAULT_TASKS,
        help=(
            "Task list to run. "
            "AllTask means FoodOnly+FoodLight+ToyOnly+ToyLight+LightOnly only. "
            "Default: FoodOnly FoodLight ToyOnly ToyLight LightOnly"
        ),
    )
    parser.add_argument(
        "--min-trial-length",
        type=int,
        default=None,
        help="Optional minimum trial length filter.",
    )
    parser.add_argument(
        "--outdir",
        type=str,
        default="results",
        help="Base output directory; files are saved under <outdir>/<feature>/ (default: results).",
    )
    parser.add_argument(
        "--bad-ids",
        nargs="*",
        type=int,
        default=DEFAULT_BAD_IDS,
        help="IDs to exclude. Defaults to notebook bad_id list.",
    )
    parser.add_argument(
        "--include-chemo",
        action="store_true",
        help="Also run SalineVsChemo comparison (Saline, Inhibitory, Excitatory).",
    )
    return parser.parse_args()


def _normalize_tasks(task_names: Sequence[str]) -> List[Tuple[str, Optional[Sequence[str] | str]]]:
    normalized: List[Tuple[str, Optional[Sequence[str] | str]]] = []
    for name in task_names:
        if name.lower() in {"alltask", "all", "none"}:
            normalized.append(("AllTask", DEFAULT_TASKS))
        else:
            normalized.append((name, name))
    return normalized


def _save_table_outputs(df: pd.DataFrame, base_path: Path) -> None:
    xlsx_path = base_path.with_suffix(".xlsx")
    df.to_excel(xlsx_path, index=False)
    print(f"[✓] Saved {xlsx_path}")


def main() -> None:
    args = parse_args()

    dose_label = f"{args.dose_mult}X"
    prefix = f"White_{dose_label}"

    curvature_params = {"bodypart": "Midback", "window": 23}
    speed_params = {
        "bodypart": "Head",
        "time_limit": None,
        "smooth": False,
        "window": 5,
    }
    angle_params = {
        "smooth_window": None,
        "likelihood_threshold": 0.65,
    }

    outdir = Path(args.outdir) / args.feature
    outdir.mkdir(parents=True, exist_ok=True)

    dlc_table = load_dlc_table()

    tasks = _normalize_tasks(args.tasks)

    comparison_sets: List[Tuple[str, List[str]]] = [
        ("SalineVsGhrelin", ["Saline", "Ghrelin"]),
    ]
    if args.include_chemo:
        comparison_sets.append(
            ("SalineVsChemo", ["Saline", "Inhibitory", "Excitatory"])
        )

    if not tasks:
        raise ValueError("No tasks found for the selected filters.")

    num_tables = 0

    print(f"[INFO] Loaded dlc_table with {len(dlc_table)} rows")
    print(f"[INFO] Output directory: {outdir.resolve()}")
    print(f"[INFO] Tasks to process: {[task_label for task_label, _ in tasks]}")

    for task_label, task_name in tasks:
        print("\n" + "=" * 60)
        print(f"Processing task: {task_label}")
        print("=" * 60)

        saline_id, ghrelin_id, exc_id, inh_id = fetch_id_list(
            dlc_table,
            task_name=task_name,
            dose_mult=args.dose_mult,
            bad_ids=args.bad_ids,
            genotype=args.genotype,
            min_trial_length=args.min_trial_length,
        )

        print(f"saline_id: {len(saline_id)} trials")
        print(f"ghrelin_id: {len(ghrelin_id)} trials")
        print(f"inh_id: {len(inh_id)} trials")
        print(f"exc_id: {len(exc_id)} trials")

        all_groups = {
            "Saline": saline_id,
            "Ghrelin": ghrelin_id,
            "Inhibitory": inh_id,
            "Excitatory": exc_id,
        }

        for comparison_name, groups in comparison_sets:
            group_specs = {
                label: all_groups[label]
                for label in groups
                if all_groups[label] not in (None, [], ())
            }

            if len(group_specs) < 2:
                print(f"[WARN] Missing groups for {task_label} - {comparison_name}, skipping...")
                continue

            print(f"\n[INFO] Running {args.feature} analysis for {task_label} ({comparison_name})...")
            frames = []
            for label, ids in group_specs.items():
                if args.feature == "curvature":
                    df = batch_trajectory_curvature(dlc_table, ids, **curvature_params)
                    if df.empty:
                        continue
                elif args.feature == "speed":
                    df = batch_compute_motion_features_per_minute(
                        dlc_table,
                        ids,
                        **speed_params,
                    )
                    if df.empty:
                        continue
                    df = df[["trial_id", "velocity_per_min"]].copy().dropna()
                else:
                    df = batch_angle_features(
                        dlc_table,
                        ids,
                        **angle_params,
                    )
                    if df.empty:
                        continue
                    df = df[["trial_id", "head_body_misalignment_p95"]].copy().dropna()

                if df.empty:
                    continue
                df["group"] = label
                df["task"] = task_label
                frames.append(df)

            if frames:
                df_out = pd.concat(frames, ignore_index=True)

                if args.feature == "curvature":
                    y_col = "mean_curvature"
                    y_label = "Mean curvature"
                    suffix = "curvature"
                    title_tail = f"Curvature | window={curvature_params['window']}"
                elif args.feature == "speed":
                    y_col = "velocity_per_min"
                    y_label = "Average speed (units/min)"
                    suffix = "speed"
                    title_tail = f"Speed | window={speed_params['window']}"
                else:
                    y_col = "head_body_misalignment_p95"
                    y_label = "Mean head_body_misalignment_p95"
                    suffix = "angle"
                    title_tail = f"Angle | likelihood={angle_params['likelihood_threshold']}"

                _save_table_outputs(
                    df_out,
                    outdir / f"{prefix}_{task_label}_{comparison_name}_{suffix}",
                )
                order = [g for g in groups if g in df_out["group"].unique()]
                fig, ax, stats_df = plot_groupwise_bar(
                    df_out,
                    y=y_col,
                    ylabel=y_label,
                    plot_type="bar",
                    show_points=True,
                    order=order,
                )
                ax.set_title(
                    f"{task_label} | {comparison_name} | {title_tail}",
                    pad=20,
                )
                pdf_path = outdir / f"{prefix}_{task_label}_{comparison_name}_{suffix}.pdf"
                fig.savefig(pdf_path, dpi=300, bbox_inches="tight")
                plt.close(fig)
                print(f"[✓] Saved {pdf_path}")
                print(stats_df)
                num_tables += 1

    if num_tables == 0:
        raise ValueError(f"No Saline/Ghrelin {args.feature} data found for the selected tasks.")

    print("\n" + "=" * 60)
    print(f"Analysis complete! Processed {len(tasks)} task conditions.")
    print(f"Saved per-task {args.feature} XLSX/PDF outputs: {num_tables}")
    print("=" * 60)


if __name__ == "__main__":
    main()
