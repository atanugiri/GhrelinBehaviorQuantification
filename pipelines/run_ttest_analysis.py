#!/usr/bin/env python
"""
T-test analysis script for comparing groups across tasks and features.
"""

import argparse
import pandas as pd
from scipy.stats import ttest_ind


def load_data(xlsx_file):
    """Load data from xlsx file."""
    df = pd.read_excel(xlsx_file, sheet_name=0)
    return df


def run_ttest(df, task_name, groups, feature):
    """
    Run unpaired t-test comparing two groups for a specific feature and task.
    
    Args:
        df: DataFrame with the data
        task_name: Name of the task to filter, or None to include all tasks
        groups: Tuple of (group1, group2) to compare
        feature: Feature name to analyze
    
    Returns:
        Dictionary with results
    """
    if feature not in df.columns:
        raise ValueError(f"Feature '{feature}' not found in dataset.")
    
    if len(groups) != 2:
        raise ValueError("Comparison requires exactly 2 groups.")
    
    group1, group2 = groups
    
    # Filter by task if specified
    if task_name is None or task_name.lower() == 'none':
        task_df = df
        task_label = "AllTasks"
    else:
        task_df = df[df['task'] == task_name]
        if task_df.empty:
            raise ValueError(f"Task '{task_name}' not found in dataset.")
        task_label = task_name
    
    # Get data for each group
    data1 = task_df[task_df['group'] == group1][feature].dropna().values
    data2 = task_df[task_df['group'] == group2][feature].dropna().values
    
    if len(data1) == 0 or len(data2) == 0:
        raise ValueError(f"No data found for groups {group1} or {group2} in task {task_name}")
    
    # Run t-test
    t_stat, p_val = ttest_ind(data1, data2, equal_var=False, nan_policy='omit')
    
    results = {
        'task': task_label,
        'feature': feature,
        'group1': group1,
        'group2': group2,
        'n_group1': len(data1),
        'n_group2': len(data2),
        'mean_group1': data1.mean(),
        'mean_group2': data2.mean(),
        'std_group1': data1.std(),
        'std_group2': data2.std(),
        't_statistic': t_stat,
        'p_value': p_val,
    }
    
    return results


def print_results(results):
    """Print t-test results in a simple format."""
    print(f"task={results['task']}, feature={results['feature']}")
    print(f"n({results['group1']})={results['n_group1']}, n({results['group2']})={results['n_group2']}")
    df = results['n_group1'] + results['n_group2'] - 2
    print(f"t({df}) = {results['t_statistic']:.3f}, p = {results['p_value']:.4f}")


def main():
    parser = argparse.ArgumentParser(
        description="Run unpaired t-tests comparing groups across tasks and features."
    )
    
    parser.add_argument('--xlsx', type=str, default='results/Fig S11G.xlsx',
                        help='Path to xlsx file (default: results/Fig S11G.xlsx)')
    
    parser.add_argument('--task-name', type=str, default=None,
                        help='Name of the task to analyze, or None to include all tasks (default: None)')
    
    parser.add_argument('--comparison', type=str, nargs=2, metavar=('GROUP1', 'GROUP2'), required=True,
                        help='Two groups to compare')
    
    parser.add_argument('--feature', type=str, required=True,
                        help='Feature to analyze')
    
    args = parser.parse_args()
    
    # Load data
    try:
        df = load_data(args.xlsx)
    except FileNotFoundError:
        print(f"Error: File '{args.xlsx}' not found.")
        return
    
    # Run analysis
    try:
        results = run_ttest(df, args.task_name, args.comparison, args.feature)
        print_results(results)
    except ValueError as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    main()
