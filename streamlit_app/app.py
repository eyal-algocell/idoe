"""
iDoE Planner - Streamlit Application

An easy, no-code app for planning intensified Design of Experiments (iDoE).
"""

import streamlit as st
import numpy as np
import pandas as pd
from src.parameter_manager import ParameterManager, create_example_parameters
from src.optimizer_wrapper import IDOEOptimizerWrapper, Constraints
from src.visualizations import (
    plot_usage_heatmap,
    plot_design_scatter_2d,
    plot_parallel_coordinates,
    plot_all_run_timelines
)
from src.table_generator import TableGenerator

# Page configuration
st.set_page_config(
    page_title="iDoE Planner",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'param_manager' not in st.session_state:
    st.session_state.param_manager = ParameterManager()
if 'optimization_result' not in st.session_state:
    st.session_state.optimization_result = None
if 'show_results' not in st.session_state:
    st.session_state.show_results = False


def reset_app():
    """Reset the application state."""
    st.session_state.param_manager = ParameterManager()
    st.session_state.optimization_result = None
    st.session_state.show_results = False


def load_example():
    """Load example parameter set."""
    st.session_state.param_manager = create_example_parameters()
    st.session_state.optimization_result = None
    st.session_state.show_results = False


# Sidebar
with st.sidebar:
    st.title("🧬 iDoE Planner")
    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🆕 New Plan", use_container_width=True):
            reset_app()
            st.rerun()

    with col2:
        if st.button("📋 Load Example", use_container_width=True):
            load_example()
            st.rerun()

    st.markdown("---")

    # Download button (appears after plan generation)
    if st.session_state.show_results and st.session_state.optimization_result:
        result = st.session_state.optimization_result
        if result.feasible:
            st.markdown("### 📥 Download")

            param_manager = st.session_state.param_manager
            combos = param_manager.generate_combinations()

            # Generate constraints info
            constraints_info = st.session_state.get('constraints_dict', {})

            table_gen = TableGenerator(
                assignments=result.assignments,
                combinations=combos,
                param_names=param_manager.get_parameter_names(),
                param_units=param_manager.get_parameter_units(),
                total_hours=st.session_state.get('total_hours', 30.0),
                num_stages=st.session_state.get('num_stages', 3),
                constraints_info=constraints_info
            )

            excel_file = table_gen.create_excel_workbook()

            st.download_button(
                label="📊 Download Excel",
                data=excel_file,
                file_name="iDoE_Plan.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    **iDoE Planner** helps you design intensified experiments that:
    - 🎯 Cover more design space
    - ⏱️ Use fewer total runs
    - 🔬 Respect biological constraints
    - 📊 Provide clear visualizations
    """)

# Main content
st.title("iDoE Planner")
st.markdown("Plan intensified Design of Experiments with ease")

# Section 1: Define Parameters
st.header("1. Define Parameters")
st.markdown("Add your experimental parameters and their possible values.")

param_manager = st.session_state.param_manager

# Display existing parameters
if len(param_manager.parameters) > 0:
    st.markdown("#### Current Parameters")

    for idx, param in enumerate(param_manager.parameters):
        col1, col2, col3, col4 = st.columns([3, 2, 4, 1])

        with col1:
            st.text_input(
                "Name",
                value=param.name,
                key=f"param_name_{idx}",
                disabled=True,
                label_visibility="collapsed"
            )

        with col2:
            st.text_input(
                "Units",
                value=param.units,
                key=f"param_units_{idx}",
                disabled=True,
                label_visibility="collapsed"
            )

        with col3:
            st.text_input(
                "Values",
                value=", ".join([str(v) for v in param.values]),
                key=f"param_values_{idx}",
                disabled=True,
                label_visibility="collapsed"
            )

        with col4:
            if st.button("🗑️", key=f"remove_param_{idx}"):
                param_manager.remove_parameter(idx)
                st.rerun()

# Add new parameter
with st.expander("➕ Add New Parameter", expanded=len(param_manager.parameters) == 0):
    col1, col2, col3 = st.columns([3, 2, 4])

    with col1:
        new_param_name = st.text_input(
            "Parameter Name",
            placeholder="e.g., Temperature",
            key="new_param_name"
        )

    with col2:
        new_param_units = st.text_input(
            "Units",
            placeholder="e.g., °C",
            key="new_param_units"
        )

    with col3:
        new_param_values = st.text_input(
            "Values (comma-separated)",
            placeholder="e.g., 29, 31, 33",
            key="new_param_values"
        )

    if st.button("➕ Add Parameter"):
        if new_param_name and new_param_values:
            try:
                values = [float(v.strip()) for v in new_param_values.split(',')]
                param_manager.add_parameter(new_param_name, new_param_units, values)
                st.success(f"Added parameter: {new_param_name}")
                st.rerun()
            except ValueError:
                st.error("Invalid values. Please enter numbers separated by commas.")
        else:
            st.error("Please provide parameter name and values.")

# Preview combinations
if len(param_manager.parameters) > 0:
    n_combos = param_manager.get_num_combinations()
    st.info(f"📊 Total combinations: **{n_combos}**")

    if n_combos > 100:
        st.warning("⚠️ Large number of combinations may make optimization slow or infeasible.")

    if n_combos <= 50:
        with st.expander("👁️ Preview Combinations"):
            combos_df = param_manager.get_combinations_dataframe()
            st.dataframe(combos_df, use_container_width=True)

# Section 2: Experiment Structure
st.header("2. Experiment Structure")
st.markdown("Configure the experimental runs and timing.")

col1, col2, col3 = st.columns(3)

with col1:
    num_runs = st.number_input(
        "Maximum Number of Runs",
        min_value=1,
        max_value=20,
        value=6,
        help="Maximum number of experimental runs to use"
    )

with col2:
    num_stages = st.number_input(
        "Stages per Run",
        min_value=2,
        max_value=6,
        value=3,
        help="Number of stages within each run"
    )

with col3:
    total_hours = st.number_input(
        "Run Duration (hours)",
        min_value=1.0,
        max_value=200.0,
        value=30.0,
        step=1.0,
        help="Total duration of each experimental run"
    )

per_stage_hours = total_hours / num_stages
st.info(f"⏱️ Each stage will be **{per_stage_hours:.1f} hours** long")

# Section 3: Limitations (C1-C8)
st.header("3. Limitations (Constraints C1-C8)")
st.markdown("Configure guardrails for your experimental plan.")

# C1
st.markdown("#### C1: One Condition Per Stage")
st.markdown("✅ **Always enforced** - Each stage can only have one combination active")

# C2
c2_enabled = st.checkbox(
    "C2: Avoid repeating same combination in same stage across runs",
    value=True,
    help="Promotes diversity by ensuring each combination appears in different stage positions"
)

# C3
c3_col1, c3_col2 = st.columns([3, 1])
with c3_col1:
    c3_enabled = st.checkbox(
        "C3: Limit repeats within same run",
        value=True,
        help="Prevents a combination from being used too many times in one run"
    )
with c3_col2:
    c3_max = st.number_input(
        "Max repeats",
        min_value=1,
        max_value=num_stages,
        value=2,
        key="c3_max",
        disabled=not c3_enabled
    )

# C4
c4_col1, c4_col2 = st.columns([3, 1])
with c4_col1:
    c4_enabled = st.checkbox(
        "C4: Limit total repeats across all runs",
        value=True,
        help="Prevents any combination from being overused globally"
    )
with c4_col2:
    c4_max = st.number_input(
        "Max global",
        min_value=1,
        max_value=10,
        value=2,
        key="c4_max",
        disabled=not c4_enabled
    )

# C5
c5_enabled = st.checkbox(
    "C5: Cover all combinations at least once",
    value=True,
    help="Ensures complete design space coverage"
)

# C6
c6_col1, c6_col2 = st.columns([3, 1])
with c6_col1:
    c6_enabled = st.checkbox(
        "C6: Target stages per combination",
        value=True,
        help="Encourages combinations to appear in multiple different stages"
    )
with c6_col2:
    c6_target = st.number_input(
        "Target stages",
        min_value=1,
        max_value=num_stages,
        value=2,
        key="c6_target",
        disabled=not c6_enabled
    )

# C7 - Per-parameter max changes
c7_enabled = st.checkbox(
    "C7: Limit maximum step change between consecutive stages",
    value=True,
    help="Prevents large jumps that could shock the culture"
)

c7_max_changes = {}
if c7_enabled and len(param_manager.parameters) > 0:
    st.markdown("**Set maximum allowed change per parameter:**")
    c7_cols = st.columns(min(3, len(param_manager.parameters)))

    for idx, param in enumerate(param_manager.parameters):
        with c7_cols[idx % 3]:
            param_range = max(param.values) - min(param.values)
            default_max = param_range * 0.5  # 50% of range as default

            max_change = st.number_input(
                f"{param.name} ({param.units})" if param.units else param.name,
                min_value=0.0,
                value=float(default_max),
                step=float(param_range / 10),
                key=f"c7_max_{idx}",
                format="%.4f"
            )
            c7_max_changes[param.name] = max_change

# C8 - Per-parameter min total changes
c8_enabled = st.checkbox(
    "C8: Ensure minimum total change within each run",
    value=True,
    help="Ensures runs actually vary conditions meaningfully"
)

c8_min_changes = {}
if c8_enabled and len(param_manager.parameters) > 0:
    st.markdown("**Set minimum required total change per parameter:**")
    c8_cols = st.columns(min(3, len(param_manager.parameters)))

    for idx, param in enumerate(param_manager.parameters):
        with c8_cols[idx % 3]:
            param_range = max(param.values) - min(param.values)
            default_min = param_range * 0.1  # 10% of range as default

            min_change = st.number_input(
                f"{param.name} ({param.units})" if param.units else param.name,
                min_value=0.0,
                value=float(default_min),
                step=float(param_range / 10),
                key=f"c8_min_{idx}",
                format="%.4f"
            )
            c8_min_changes[param.name] = min_change

# Validation and Planning
st.header("4. Generate Plan")

# Validate parameters
is_valid, error_msg = param_manager.validate()

if not is_valid:
    st.error(f"❌ {error_msg}")
else:
    # Show feasibility estimate
    n_combos = param_manager.get_num_combinations()
    total_slots = num_runs * num_stages

    if c5_enabled and n_combos > total_slots:
        st.warning(f"⚠️ You have {n_combos} combinations but only {total_slots} stage slots. Infeasible with C5 enabled. Try increasing runs or disabling C5.")

    # Generate button
    if st.button("🚀 Run Planner", type="primary", use_container_width=True):
        with st.spinner("Optimizing... This may take up to 30 seconds..."):
            # Build constraints object
            constraints = Constraints(
                c1_enabled=True,
                c2_enabled=c2_enabled,
                c3_enabled=c3_enabled,
                c3_max_per_run=c3_max if c3_enabled else num_stages,
                c4_enabled=c4_enabled,
                c4_max_global=c4_max if c4_enabled else 999,
                c5_enabled=c5_enabled,
                c6_enabled=c6_enabled,
                c6_target_stages=c6_target if c6_enabled else 1,
                c7_enabled=c7_enabled,
                c7_max_changes=c7_max_changes if c7_enabled else None,
                c8_enabled=c8_enabled,
                c8_min_changes=c8_min_changes if c8_enabled else None
            )

            # Store constraints for export
            st.session_state.constraints_dict = {
                "C1 (one combo per stage)": "Enabled",
                "C2 (unique per stage position)": "Enabled" if c2_enabled else "Disabled",
                "C3 (max per run)": f"{c3_max} repeats" if c3_enabled else "Disabled",
                "C4 (max global)": f"{c4_max} repeats" if c4_enabled else "Disabled",
                "C5 (cover all)": "Enabled" if c5_enabled else "Disabled",
                "C6 (target stages)": f"{c6_target} stages" if c6_enabled else "Disabled",
                "C7 (max step)": "Enabled" if c7_enabled else "Disabled",
                "C8 (min total change)": "Enabled" if c8_enabled else "Disabled"
            }

            # Run optimizer
            combinations = param_manager.generate_combinations()
            param_names = param_manager.get_parameter_names()

            optimizer = IDOEOptimizerWrapper(
                combinations=combinations,
                parameter_names=param_names,
                num_runs=num_runs,
                num_stages=num_stages,
                constraints=constraints
            )

            result = optimizer.optimize(time_limit=30)

            st.session_state.optimization_result = result
            st.session_state.show_results = True
            st.session_state.total_hours = total_hours
            st.session_state.num_stages = num_stages

        st.rerun()

# Section 5: Results
if st.session_state.show_results and st.session_state.optimization_result:
    result = st.session_state.optimization_result

    st.header("5. Results")

    if not result.feasible:
        st.error(f"❌ **Optimization failed: {result.status}**")
        st.markdown("### 💡 Suggestions:")
        for hint in result.infeasibility_hints:
            st.markdown(f"- {hint}")
    else:
        st.success(f"✅ **Optimization successful! Status: {result.status}**")

        # Summary stats
        param_manager = st.session_state.param_manager
        combos = param_manager.generate_combinations()

        table_gen = TableGenerator(
            assignments=result.assignments,
            combinations=combos,
            param_names=param_manager.get_parameter_names(),
            param_units=param_manager.get_parameter_units(),
            total_hours=st.session_state.total_hours,
            num_stages=st.session_state.num_stages
        )

        stats = table_gen.get_summary_stats()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Runs Used", stats['runs_used'])
        with col2:
            st.metric("Total Stages", stats['total_stages'])
        with col3:
            st.metric("Combos Covered", f"{stats['combos_covered']}/{stats['total_combos']}")
        with col4:
            st.metric("Coverage", f"{stats['coverage_percent']}%")

        # Tables
        st.subheader("📋 Experimental Plan")

        tab1, tab2 = st.tabs(["Combined Table", "Per-Run Tables"])

        with tab1:
            combined_df = table_gen.generate_combined_table()
            st.dataframe(combined_df, use_container_width=True, hide_index=True)

        with tab2:
            for run_idx in sorted(result.assignments.keys()):
                with st.expander(f"Run {run_idx + 1}", expanded=run_idx == 0):
                    run_df = table_gen.generate_run_table(run_idx)
                    st.dataframe(run_df, use_container_width=True, hide_index=True)

        # Visualizations
        st.subheader("📊 Visualizations")

        # Heatmap
        st.markdown("#### Combo Usage Heatmap")
        fig_heatmap = plot_usage_heatmap(result.assignments, len(combos))
        st.plotly_chart(fig_heatmap, use_container_width=True)

        # Design space visualization
        st.markdown("#### Design Space")
        n_params = len(param_manager.parameters)

        if n_params == 2:
            # 2D scatter plot
            fig_scatter = plot_design_scatter_2d(
                combinations=combos,
                assignments=result.assignments,
                param_x_idx=0,
                param_y_idx=1,
                param_names=param_manager.get_parameter_names(),
                param_units=param_manager.get_parameter_units()
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        elif n_params > 2:
            # Allow user to choose 2D plot or parallel coordinates
            viz_type = st.radio(
                "Visualization type:",
                ["2D Scatter (select 2 parameters)", "Parallel Coordinates (all parameters)"],
                horizontal=True
            )

            if viz_type.startswith("2D"):
                param_names = param_manager.get_parameter_names()
                col1, col2 = st.columns(2)
                with col1:
                    x_param = st.selectbox("X-axis parameter:", param_names, index=0)
                with col2:
                    y_param = st.selectbox("Y-axis parameter:", param_names, index=min(1, len(param_names)-1))

                x_idx = param_names.index(x_param)
                y_idx = param_names.index(y_param)

                fig_scatter = plot_design_scatter_2d(
                    combinations=combos,
                    assignments=result.assignments,
                    param_x_idx=x_idx,
                    param_y_idx=y_idx,
                    param_names=param_manager.get_parameter_names(),
                    param_units=param_manager.get_parameter_units()
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                fig_parallel = plot_parallel_coordinates(
                    combinations=combos,
                    assignments=result.assignments,
                    param_names=param_manager.get_parameter_names(),
                    param_units=param_manager.get_parameter_units()
                )
                st.plotly_chart(fig_parallel, use_container_width=True)

        # Timeline plots
        st.markdown("#### Run Timelines")

        # Parameter selection for timeline
        if n_params > 3:
            param_names = param_manager.get_parameter_names()
            selected_param_names = st.multiselect(
                "Select parameters to display:",
                param_names,
                default=param_names[:2]
            )
            selected_param_indices = [param_names.index(name) for name in selected_param_names]
        else:
            selected_param_indices = None

        timeline_figs = plot_all_run_timelines(
            assignments=result.assignments,
            combinations=combos,
            param_names=param_manager.get_parameter_names(),
            param_units=param_manager.get_parameter_units(),
            total_hours=st.session_state.total_hours,
            num_stages=st.session_state.num_stages,
            selected_params=selected_param_indices
        )

        for idx, fig in enumerate(timeline_figs):
            st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>iDoE Planner v1.0 | Built with Streamlit |
    Based on von Stosch & Willis (2017)</p>
</div>
""", unsafe_allow_html=True)
