from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd

from Python_scripts.config import load_dlc_table
from Python_scripts.Data_analysis.fetch_id_list import fetch_id_list
from Python_scripts.Data_analysis.plot_groupwise_bar import plot_groupwise_bar
from Python_scripts.Feature_functions.motion_features import (
    batch_compute_motion_features_per_minute,
)


DEFAULT_BAD_IDS = [120, 130, 137, 138, 141, 142, 166, 289, 293, 310, 312]


def _parse_task_names(values: list[str]) -> list[str]:
    task_names = [value.strip() for value in values if value.strip()]
    if not task_names:
        raise argparse.ArgumentTypeError("At least one task name is required.")
    return task_names


def _format_plot_stats(stats_df: pd.DataFrame) -> str:
    lines = []
    anova = stats_df.attrs.get("anova", {})
    if anova:
        lines.append(
            "1-way ANOVA: F(" 
            f"{int(anova.get('df_between', 0))}, {int(anova.get('df_within', 0))}) = "
            f"{anova.get('f_anova', float('nan')):.3g}, p = {anova.get('p_anova', float('nan')):.3g}"
        )

    for _, row in stats_df.iterrows():
        group_a = row.get("group_a", "Group A")
        group_b = row.get("group_b", "Group B")
        t_val = row.get("t", float("nan"))
        p_val = row.get("p_ttest", float("nan"))
        lines.append(f"t-test {group_a} vs {group_b}: t = {t_val:.3g}, p = {p_val:.3g}")

    return "\n".join(lines) if lines else "No statistics available."




def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run speed analysis and export per-trial CSV results."
    )
    parser.add_argument(
        "--task-name",
        nargs="+",
        required=True,
        help="One or more task names such as FoodOnly FoodLight ToyOnly.",
    )
    parser.add_argument(
        "--dose-mult",
        type=int,
        default=2,
        help="Dose multiplier to filter by.",
    )
    parser.add_argument(
        "--genotype",
        type=str,
        default="white",
        help="Genotype filter.",
    )
    parser.add_argument(
        "--bodypart",
        type=str,
        default="Head",
        help="Bodypart to use for motion features.",
    )
    parser.add_argument(
        "--time-limit",
        type=float,
        default=None,
        help="Optional time limit in seconds.",
    )
    parser.add_argument(
        "--smooth",
        action="store_true",
        help="Enable smoothing before feature computation.",
    )
    parser.add_argument(
        "--window",
        type=int,
        default=5,
        help="Smoothing window size.",
    )
    parser.add_argument(
        "--min-trial-length",
        type=int,
        default=None,
        help="Optional minimum trial length filter.",
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        default="results",
        help="Directory where CSV output will be written.",
    )
    parser.add_argument(
        "--bad-id",
        nargs="+",
        type=int,
        action="extend",
        default=DEFAULT_BAD_IDS.copy(),
        help="Trial IDs to exclude. Pass one or more ints, for example: --bad-id 120 130 137.",
    )
    parser.add_argument(
        "--plot-groups",
        nargs="+",
        type=str,
        default=None,
        help=(
            "Optional list of group labels to plot in the specified order. "
            "E.g.: --plot-groups Saline Ghrelin or --plot-groups Saline Inhibitory Excitatory"
        ),
    )
    return parser


def run_speed_analysis(
    task_names: list[str],
    dose_mult: int,
    genotype: str,
    bodypart: str,
    time_limit: Optional[float],
    smooth: bool,
    window: int,
    min_trial_length: Optional[int],
    results_dir: str,
    bad_ids: Optional[list[int]] = None,
    plot_groups: Optional[list[str]] = None,
) -> Path:
    dlc_table = load_dlc_table()

    saline_ids, ghrelin_ids, exc_ids, inh_ids = fetch_id_list(
        dlc_table,
        task_name=task_names,
        dose_mult=dose_mult,
        genotype=genotype,
        bad_ids=bad_ids,
        min_trial_length=min_trial_length,
    )

    group_specs = {
        "Saline": saline_ids,
        "Ghrelin": ghrelin_ids,
        "Inhibitory": inh_ids,
        "Excitatory": exc_ids,
    }
    group_specs = {
        label: ids for label, ids in group_specs.items() if ids not in (None, [], ())
    }

    # If user requested a subset/order of groups to plot, validate and filter
    if plot_groups is not None:
        missing = [g for g in plot_groups if g not in group_specs]
        if missing:
            raise ValueError(
                f"Requested plot groups not available: {missing}. "
                f"Available groups: {list(group_specs.keys())}"
            )
        # Preserve requested order and only include requested groups
        group_specs = {label: group_specs[label] for label in plot_groups}

    if not group_specs:
        raise ValueError("No groups matched the provided filters.")

    rows = []
    task_label = "_".join(task_names)

    for group_name, trial_ids in group_specs.items():
        df = batch_compute_motion_features_per_minute(
            dlc_table=dlc_table,
            trial_ids=trial_ids,
            bodypart=bodypart,
            time_limit=time_limit,
            smooth=smooth,
            window=window,
        )
        if df.empty:
            continue

        df = df.copy()
        df = df.rename(columns={"velocity_per_min": "velocity_per_minute"})
        df["group"] = group_name
        df["task"] = task_label
        df["dose_mult"] = dose_mult
        df["genotype"] = genotype
        df["bodypart"] = bodypart
        df["smooth"] = smooth
        df["window"] = window
        df["time_limit"] = time_limit
        rows.append(df)

    if not rows:
        raise ValueError("No motion feature rows were produced for the selected trials.")

    out_df = pd.concat(rows, ignore_index=True)

    out_dir = Path(results_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    smooth_tag = "smooth" if smooth else "nosmooth"
    time_tag = "all" if time_limit is None else f"t{str(time_limit).replace('.', 'p')}"
    out_path = out_dir / (
        f"speed_analysis_{task_label}_dose{dose_mult}_{genotype}_{bodypart}_"
        f"{smooth_tag}_w{window}_{time_tag}.csv"
    )

    csv_df = out_df[["task", "group", "dose_mult", "velocity_per_minute"]].copy()
    csv_df.to_csv(out_path, index=False)

    plot_df = out_df[["group", "velocity_per_minute"]].copy()
    order = list(group_specs.keys())
    fig, ax, stats_df = plot_groupwise_bar(
        plot_df,
        y="velocity_per_minute",
        ylabel="Velocity per minute",
        title=f"{task_label} | Speed Analysis",
        show_points=True,
        order=order,
    )

    # plot_groupwise_bar now prints numeric stats to stdout; no overlay text needed

    plot_path = out_dir / out_path.name.replace(".csv", ".pdf")
    fig.savefig(plot_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print(f"[✓] Saved {out_path}")
    print(f"[✓] Saved {plot_path}")
    print(f"[INFO] Rows written: {len(out_df)}")
    print(f"[INFO] Groups included: {list(group_specs.keys())}")

    return out_path


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    run_speed_analysis(
        task_names=_parse_task_names(args.task_name),
        dose_mult=args.dose_mult,
        genotype=args.genotype,
        bodypart=args.bodypart,
        time_limit=args.time_limit,
        smooth=args.smooth,
        window=args.window,
        min_trial_length=args.min_trial_length,
        results_dir=args.results_dir,
        bad_ids=args.bad_id,
        plot_groups=args.plot_groups,
    )


if __name__ == "__main__":
    main()