"""Visualization functions for the iDoE Streamlit app using Plotly."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Tuple


def plot_usage_heatmap(
    assignments: Dict[int, List[int]],
    n_combos: int
) -> go.Figure:
    """
    Create heatmap showing how many times each combo is used in each run.

    Args:
        assignments: Dict mapping run_idx -> [combo_idx per stage]
        n_combos: Total number of combinations

    Returns:
        Plotly Figure object
    """
    n_runs = len(assignments)

    # Build usage matrix
    usage = np.zeros((n_combos, n_runs), dtype=int)

    for run_idx, combo_list in assignments.items():
        for combo_idx in combo_list:
            usage[combo_idx, run_idx] += 1

    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=usage,
        x=[f"Run {i+1}" for i in range(n_runs)],
        y=[f"Combo {i+1}" for i in range(n_combos)],
        colorscale='Blues',
        zmin=0,
        zmax=2,
        colorbar=dict(title="Usage Count"),
        hovertemplate='%{y}<br>%{x}<br>Used %{z} times<extra></extra>'
    ))

    fig.update_layout(
        title="Combo Usage Heatmap",
        xaxis_title="Runs",
        yaxis_title="Design Combinations",
        height=max(400, n_combos * 30),
        font=dict(size=12)
    )

    return fig


def plot_design_scatter_2d(
    combinations: np.ndarray,
    assignments: Dict[int, List[int]],
    param_x_idx: int,
    param_y_idx: int,
    param_names: List[str],
    param_units: List[str]
) -> go.Figure:
    """
    Create 2D scatter plot of design space with experimental paths.

    Args:
        combinations: Array of shape (n_combos, n_params)
        assignments: Dict mapping run_idx -> [combo_idx per stage]
        param_x_idx: Index of parameter for x-axis
        param_y_idx: Index of parameter for y-axis
        param_names: List of parameter names
        param_units: List of parameter units

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    # Plot all design points
    x_vals = combinations[:, param_x_idx]
    y_vals = combinations[:, param_y_idx]

    fig.add_trace(go.Scatter(
        x=x_vals,
        y=y_vals,
        mode='markers',
        marker=dict(size=12, symbol='diamond', line=dict(width=2, color='black')),
        name='Design Points',
        text=[f"Combo {i+1}" for i in range(len(combinations))],
        hovertemplate='%{text}<br>%{x:.4f}, %{y:.4f}<extra></extra>'
    ))

    # Plot experimental paths
    colors = px.colors.qualitative.Plotly
    for run_idx, combo_list in sorted(assignments.items()):
        path_x = [combinations[c, param_x_idx] for c in combo_list]
        path_y = [combinations[c, param_y_idx] for c in combo_list]

        color = colors[run_idx % len(colors)]

        fig.add_trace(go.Scatter(
            x=path_x,
            y=path_y,
            mode='lines+markers',
            line=dict(width=2, color=color),
            marker=dict(size=8, color=color),
            name=f'Run {run_idx+1}',
            hovertemplate=f'Run {run_idx+1}<br>Stage %{{pointNumber}}<br>%{{x:.4f}}, %{{y:.4f}}<extra></extra>'
        ))

    # Labels
    x_label = f"{param_names[param_x_idx]}"
    if param_units[param_x_idx]:
        x_label += f" ({param_units[param_x_idx]})"

    y_label = f"{param_names[param_y_idx]}"
    if param_units[param_y_idx]:
        y_label += f" ({param_units[param_y_idx]})"

    fig.update_layout(
        title="Design Space and Experimental Paths",
        xaxis_title=x_label,
        yaxis_title=y_label,
        height=600,
        hovermode='closest',
        legend=dict(x=1.02, y=1)
    )

    return fig


def plot_parallel_coordinates(
    combinations: np.ndarray,
    assignments: Dict[int, List[int]],
    param_names: List[str],
    param_units: List[str]
) -> go.Figure:
    """
    Create parallel coordinates plot for multi-parameter visualization.

    Args:
        combinations: Array of shape (n_combos, n_params)
        assignments: Dict mapping run_idx -> [combo_idx per stage]
        param_names: List of parameter names
        param_units: List of parameter units

    Returns:
        Plotly Figure object
    """
    # Create dataframe with all combo data
    n_params = combinations.shape[1]

    # Collect data for plot
    data_rows = []
    for run_idx, combo_list in sorted(assignments.items()):
        for stage_idx, combo_idx in enumerate(combo_list):
            row = {
                'Run': run_idx + 1,
                'Stage': stage_idx + 1,
                'Combo': combo_idx + 1
            }
            for p_idx in range(n_params):
                col_name = param_names[p_idx]
                row[col_name] = combinations[combo_idx, p_idx]
            data_rows.append(row)

    df = pd.DataFrame(data_rows)

    # Create dimensions for parallel coordinates
    dimensions = []
    for p_idx, name in enumerate(param_names):
        dim = dict(
            label=f"{name} ({param_units[p_idx]})" if param_units[p_idx] else name,
            values=df[name]
        )
        dimensions.append(dim)

    fig = go.Figure(data=
        go.Parcoords(
            line=dict(
                color=df['Run'],
                colorscale='Viridis',
                showscale=True,
                cmin=df['Run'].min(),
                cmax=df['Run'].max(),
                colorbar=dict(title="Run #")
            ),
            dimensions=dimensions
        )
    )

    fig.update_layout(
        title="Parallel Coordinates Plot - All Parameters",
        height=500
    )

    return fig


def plot_run_timeline(
    run_idx: int,
    combo_list: List[int],
    combinations: np.ndarray,
    param_names: List[str],
    param_units: List[str],
    total_hours: float,
    num_stages: int,
    selected_params: List[int] = None
) -> go.Figure:
    """
    Create timeline plot showing parameter profiles for a single run.

    Args:
        run_idx: Run index
        combo_list: List of combo indices for each stage
        combinations: Array of shape (n_combos, n_params)
        param_names: List of parameter names
        param_units: List of parameter units
        total_hours: Total run duration in hours
        num_stages: Number of stages
        selected_params: List of parameter indices to plot (None = all)

    Returns:
        Plotly Figure object
    """
    if selected_params is None:
        selected_params = list(range(len(param_names)))

    per_stage_hours = total_hours / num_stages

    fig = go.Figure()

    colors = px.colors.qualitative.Plotly

    for p_idx in selected_params:
        # Build step function
        time_points = []
        param_values = []

        for stage_idx, combo_idx in enumerate(combo_list):
            t_start = stage_idx * per_stage_hours
            t_end = (stage_idx + 1) * per_stage_hours
            value = combinations[combo_idx, p_idx]

            time_points.extend([t_start, t_end])
            param_values.extend([value, value])

        param_label = param_names[p_idx]
        if param_units[p_idx]:
            param_label += f" ({param_units[p_idx]})"

        fig.add_trace(go.Scatter(
            x=time_points,
            y=param_values,
            mode='lines',
            line=dict(width=3, color=colors[p_idx % len(colors)]),
            name=param_label,
            hovertemplate=f'{param_label}<br>Time: %{{x:.1f}} h<br>Value: %{{y:.4f}}<extra></extra>'
        ))

    fig.update_layout(
        title=f"Run {run_idx+1}: Parameter Timeline",
        xaxis_title="Time (h)",
        yaxis_title="Parameter Values",
        height=400,
        hovermode='x unified',
        legend=dict(x=1.02, y=1)
    )

    return fig


def plot_all_run_timelines(
    assignments: Dict[int, List[int]],
    combinations: np.ndarray,
    param_names: List[str],
    param_units: List[str],
    total_hours: float,
    num_stages: int,
    selected_params: List[int] = None
) -> List[go.Figure]:
    """
    Create timeline plots for all runs.

    Args:
        assignments: Dict mapping run_idx -> [combo_idx per stage]
        combinations: Array of shape (n_combos, n_params)
        param_names: List of parameter names
        param_units: List of parameter units
        total_hours: Total run duration in hours
        num_stages: Number of stages
        selected_params: List of parameter indices to plot

    Returns:
        List of Plotly Figure objects, one per run
    """
    figures = []

    for run_idx in sorted(assignments.keys()):
        combo_list = assignments[run_idx]
        fig = plot_run_timeline(
            run_idx,
            combo_list,
            combinations,
            param_names,
            param_units,
            total_hours,
            num_stages,
            selected_params
        )
        figures.append(fig)

    return figures
