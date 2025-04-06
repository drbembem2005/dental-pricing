import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
import copy
# import numpy as np # Uncomment if using numpy alternative for calculations

# --- Constants ---
# Define column names
COL_NAME = "name"
COL_EXPECTED_CASES = "expected_cases"
COL_VAR_COST = "variable_cost"
COL_DURATION = "duration_hours"
COL_ALLOC_FIXED_COST = "allocated_fixed_cost"
COL_FIXED_COST_PER_CASE = "fixed_cost_per_case"
COL_TOTAL_COST_PER_CASE = "total_cost_per_case"
COL_PRICE_PER_CASE = "price_per_case"
COL_CONTRIB_MARGIN = "contribution_margin"
COL_BREAK_EVEN = "break_even"
COL_SERVICE_HOURS = "service_hours"

# Define keys for session state
STATE_SERVICES_DF = "services_df" # Main DataFrame for service inputs
STATE_EDIT_TARGET_INDEX = "edit_target_index" # Index of row being edited
STATE_RESULTS_DF = "results_df" # DataFrame for calculated results
STATE_CALCULATED_FIXED_COST = "calculated_fixed_cost" # Store fixed cost used for last calc
STATE_CALCULATED_MARGIN = "calculated_margin" # Store margin used for last calc
STATE_CALCULATED = "calculated" # Flag

# --- Helper Functions (Implementations are the same as previous version) ---

def initialize_session_state():
    """Initializes required keys in Streamlit's session state."""
    default_services_data = [
        {"name": "Dental Cleaning", "expected_cases": 80, "variable_cost": 150.0, "duration_hours": 1.0},
        {"name": "Filling", "expected_cases": 60, "variable_cost": 250.0, "duration_hours": 1.0},
        {"name": "Root Canal Therapy", "expected_cases": 40, "variable_cost": 500.0, "duration_hours": 2.0},
        {"name": "Orthodontics (Braces Setup)", "expected_cases": 20, "variable_cost": 1000.0, "duration_hours": 2.0},
        {"name": "Teeth Whitening", "expected_cases": 50, "variable_cost": 350.0, "duration_hours": 1.0},
        {"name": "Dental Implant", "expected_cases": 10, "variable_cost": 3000.0, "duration_hours": 3.0}
    ]
    if STATE_SERVICES_DF not in st.session_state:
        st.session_state[STATE_SERVICES_DF] = pd.DataFrame(default_services_data)
        # Ensure correct types on initialization
        st.session_state[STATE_SERVICES_DF][COL_EXPECTED_CASES] = st.session_state[STATE_SERVICES_DF][COL_EXPECTED_CASES].astype(int)
        st.session_state[STATE_SERVICES_DF][COL_VAR_COST] = st.session_state[STATE_SERVICES_DF][COL_VAR_COST].astype(float)
        st.session_state[STATE_SERVICES_DF][COL_DURATION] = st.session_state[STATE_SERVICES_DF][COL_DURATION].astype(float)


    if STATE_EDIT_TARGET_INDEX not in st.session_state:
        st.session_state[STATE_EDIT_TARGET_INDEX] = None
    if STATE_RESULTS_DF not in st.session_state:
        st.session_state[STATE_RESULTS_DF] = None
    if STATE_CALCULATED_FIXED_COST not in st.session_state:
        st.session_state[STATE_CALCULATED_FIXED_COST] = 0.0
    if STATE_CALCULATED_MARGIN not in st.session_state:
        st.session_state[STATE_CALCULATED_MARGIN] = 0.30 # Default 30%
    if STATE_CALCULATED not in st.session_state:
        st.session_state[STATE_CALCULATED] = False

def calculate_detailed_pricing(services_df: pd.DataFrame, total_fixed_cost: float, margin: float) -> Optional[pd.DataFrame]:
    """Calculates detailed pricing, cost allocation, and break-even points."""
    if services_df.empty:
        st.error("No service data available for calculation. Please add at least one service.")
        return None

    calc_df = services_df.copy() # Work on a copy

    # --- Data Type Conversion and Validation ---
    try:
        calc_df[COL_EXPECTED_CASES] = pd.to_numeric(calc_df[COL_EXPECTED_CASES], errors='coerce').fillna(0).astype(int)
        calc_df[COL_VAR_COST] = pd.to_numeric(calc_df[COL_VAR_COST], errors='coerce').fillna(0.0).astype(float)
        calc_df[COL_DURATION] = pd.to_numeric(calc_df[COL_DURATION], errors='coerce').fillna(0.0).astype(float)

        if (calc_df[COL_EXPECTED_CASES] < 0).any() or \
           (calc_df[COL_VAR_COST] < 0).any() or \
           (calc_df[COL_DURATION] <= 0).any():
             st.error("Please ensure 'Expected Cases' and 'Variable Cost' are not negative, and 'Duration' is greater than zero for all services.")
             return None
    except Exception as e:
        st.error(f"Data type error in service data: {e}. Please check inputs.")
        return None

    # --- Calculations ---
    calc_df[COL_SERVICE_HOURS] = calc_df[COL_EXPECTED_CASES] * calc_df[COL_DURATION]
    total_service_hours = calc_df[COL_SERVICE_HOURS].sum()

    if total_service_hours <= 0:
        st.warning("Total weighted service hours is zero or negative. Cannot allocate fixed costs effectively. Fixed costs per case set to 0.")
        calc_df[COL_ALLOC_FIXED_COST] = 0.0
        calc_df[COL_FIXED_COST_PER_CASE] = 0.0
    else:
        calc_df[COL_ALLOC_FIXED_COST] = total_fixed_cost * (calc_df[COL_SERVICE_HOURS] / total_service_hours)
        calc_df[COL_FIXED_COST_PER_CASE] = calc_df.apply(
             lambda row: row[COL_ALLOC_FIXED_COST] / row[COL_EXPECTED_CASES] if row[COL_EXPECTED_CASES] > 0 else 0, axis=1)

    calc_df[COL_TOTAL_COST_PER_CASE] = calc_df[COL_VAR_COST] + calc_df[COL_FIXED_COST_PER_CASE]
    calc_df[COL_PRICE_PER_CASE] = calc_df[COL_TOTAL_COST_PER_CASE] * (1 + margin)
    calc_df[COL_CONTRIB_MARGIN] = calc_df[COL_PRICE_PER_CASE] - calc_df[COL_VAR_COST]
    calc_df[COL_BREAK_EVEN] = calc_df.apply(
        lambda row: row[COL_ALLOC_FIXED_COST] / row[COL_CONTRIB_MARGIN] if row[COL_CONTRIB_MARGIN] > 0 else float('inf'), axis=1)

    # Add service name in English if original is Arabic for analysis tab dropdown
    # This assumes the initial names might be Arabic. Adjust if needed.
    # calc_df['name_en'] = calc_df[COL_NAME].apply(lambda x: f"Service_{x}" if isinstance(x, str) and any('\u0600' <= c <= '\u06FF' for c in x) else x)


    return calc_df

def calculate_sensitivity(variable_cost: float, allocated_fixed_cost: float, margin: float, cases_range: range) -> Tuple[List[float], List[float]]:
    """Calculates price and break-even sensitivity based on varying case numbers."""
    # ... (Implementation is identical to previous versions) ...
    prices = []
    break_evens = []
    for cases in cases_range:
        if cases <= 0:
            price = float('inf'); be = float('inf')
        else:
            fixed_cost_per_case = allocated_fixed_cost / cases
            total_cost = variable_cost + fixed_cost_per_case
            price = total_cost * (1 + margin)
            contribution_margin = price - variable_cost
            be = allocated_fixed_cost / contribution_margin if contribution_margin > 0 else float('inf')
        prices.append(price)
        break_evens.append(be)
    return prices, break_evens

def plot_sensitivity(cases_range: List[int], prices: List[float], break_evens: List[float]) -> plt.Figure:
    """Generates Matplotlib plots for sensitivity analysis with ENGLISH labels."""
    # ... (Implementation is identical to previous versions with English labels) ...
    fig, axs = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)

    # Plot Price Sensitivity
    axs[0].plot(cases_range, prices, marker='o', linestyle='-', color='royalblue')
    axs[0].set_title("Price Sensitivity vs. Number of Cases")
    axs[0].set_xlabel("Number of Cases")
    axs[0].set_ylabel("Calculated Price per Case (EGP)")
    axs[0].grid(True, linestyle='--', alpha=0.6)
    axs[0].ticklabel_format(style='plain', axis='y')

    # Plot Break-even Sensitivity
    axs[1].plot(cases_range, break_evens, marker='x', linestyle='--', color='crimson')
    axs[1].set_title("Break-Even Point vs. Number of Cases")
    axs[1].set_xlabel("Number of Cases")
    axs[1].set_ylabel("Calculated Break-Even Point (Cases)")
    axs[1].grid(True, linestyle='--', alpha=0.6)
    finite_bes = [be for be in break_evens if be != float('inf')]
    if finite_bes:
        axs[1].set_ylim(bottom=0, top=max(finite_bes) * 1.15 if finite_bes else 10) # Added bit more padding
    else:
        axs[1].set_ylim(bottom=0)
    axs[1].ticklabel_format(style='plain', axis='y')

    # fig.tight_layout(pad=3.0) # constrained_layout=True is often better
    return fig

# --- Streamlit App Layout ---

st.set_page_config(layout="wide", page_title="Dental Pricing Analysis")
# Initialize state first
initialize_session_state()

# --- Sidebar ---
with st.sidebar:
    st.image("https://img.icons8.com/external-flaticons-lineal-color-flat-icons/64/external-dental-clinic-dental-flaticons-lineal-color-flat-icons-3.png", width=64) # Example icon
    st.title("Clinic Settings")
    st.header("1. Monthly Fixed Costs (EGP)")
    st.caption("Costs not directly tied to procedures.")
    rent = st.number_input("Rent", min_value=0.0, value=15000.0, step=500.0, key="rent_sb")
    salaries = st.number_input("Staff Salaries", min_value=0.0, value=20000.0, step=500.0, key="salaries_sb")
    utilities = st.number_input("Utilities (Elec, Water, Net)", min_value=0.0, value=5000.0, step=200.0, key="utilities_sb")
    insurance = st.number_input("Insurance & Maintenance", min_value=0.0, value=2000.0, step=100.0, key="insurance_sb")
    marketing = st.number_input("Marketing & Advertising", min_value=0.0, value=1000.0, step=100.0, key="marketing_sb")
    other_fixed = st.number_input("Other Fixed Costs", min_value=0.0, value=0.0, step=100.0, key="other_fixed_sb")

    # Calculate and display total fixed cost IN THE SIDEBAR
    current_total_fixed_cost = rent + salaries + utilities + insurance + marketing + other_fixed
    st.metric(label="**Total Monthly Fixed Costs**", value=f"{current_total_fixed_cost:,.2f} EGP")
    st.divider()

    st.header("2. Target Profit Margin")
    st.caption("Desired profit as a percentage over total cost.")
    # Read default from state, but slider directly controls the current value
    current_margin_percentage = st.slider(
        "Profit Margin (%)",
        min_value=0, max_value=200,
        value=int(st.session_state.get(STATE_CALCULATED_MARGIN, 0.30) * 100), # Default to last calculated or 30%
        step=5,
        key="margin_slider_sb"
    )
    current_margin = current_margin_percentage / 100.0
    st.info(f"Target Margin: {current_margin_percentage}%")

# --- Main Content Tabs ---
tab1, tab2 = st.tabs(["📁 Service Management & Pricing", "📊 Sensitivity Analysis"])

with tab1:
    st.header("Service Management and Pricing Calculation")
    st.markdown("""
    Here you can manage the list of dental services offered. Add new services, edit existing ones, or remove them.
    The `Duration (hours)` is crucial as it's used to allocate the **Total Fixed Costs** you set in the sidebar.
    """)

    # --- Display Current Services DataFrame ---
    st.subheader("Current Services List")
    if st.session_state[STATE_SERVICES_DF].empty:
        st.info("No services added yet. Use the 'Add New Service' form below.")
    else:
        st.dataframe(
            st.session_state[STATE_SERVICES_DF],
            hide_index=True,
            use_container_width=True,
            column_config={ # Define formatting and user-friendly names for display
                 COL_NAME: st.column_config.TextColumn("Service Name", help="Name of the dental procedure"),
                 COL_EXPECTED_CASES: st.column_config.NumberColumn("Expected Cases / Month", help="Estimated monthly volume", format="%d", min_value=0),
                 COL_VAR_COST: st.column_config.NumberColumn("Variable Cost / Case (EGP)", help="Direct material/lab cost per procedure", format="%.2f", min_value=0.0),
                 COL_DURATION: st.column_config.NumberColumn("Duration (hours)", help="Average chair time in hours (e.g., 1.5)", format="%.2f", min_value=0.1),
            },
            key="service_display_df" # Add key for stability if needed
            )

        # --- Edit/Delete Actions ---
        st.markdown("--- **Modify Services** ---")
        services_df_display = st.session_state[STATE_SERVICES_DF] # Get reference
        indices_to_delete = []

        # Create columns for buttons for better layout
        num_services = len(services_df_display)
        cols_per_row = 3 # Adjust how many edit/delete combos fit per row
        col_idx = 0

        for index in services_df_display.index:
            service_name = services_df_display.loc[index, COL_NAME]

            # Create layout columns dynamically
            if col_idx % cols_per_row == 0:
                cols = st.columns(cols_per_row)

            with cols[col_idx % cols_per_row]:
                 st.markdown(f"**{service_name}**") # Display name clearly
                 sub_cols = st.columns(2) # Columns for Edit/Delete buttons side-by-side

                 # Edit Button
                 edit_key = f"edit_{index}_{service_name.replace(' ', '_')}" # Make key safer
                 if sub_cols[0].button("✏️ Edit", key=edit_key, help=f"Edit details for {service_name}"):
                     st.session_state[STATE_EDIT_TARGET_INDEX] = index
                     st.rerun()

                 # Delete Button
                 delete_key = f"delete_{index}_{service_name.replace(' ', '_')}"
                 if sub_cols[1].button("🗑️ Delete", key=delete_key, help=f"Remove {service_name}"):
                     indices_to_delete.append(index)
                     if st.session_state[STATE_EDIT_TARGET_INDEX] == index:
                         st.session_state[STATE_EDIT_TARGET_INDEX] = None # Clear edit if deleting target

            col_idx += 1 # Move to the next column position

        # Process deletions after the loop
        if indices_to_delete:
            st.session_state[STATE_SERVICES_DF] = services_df_display.drop(indices_to_delete).reset_index(drop=True)
            st.rerun()

    # --- Conditional Edit Form (Placed below Add/Edit/Delete buttons) ---
    if st.session_state[STATE_EDIT_TARGET_INDEX] is not None:
        edit_index = st.session_state[STATE_EDIT_TARGET_INDEX]
        if edit_index in st.session_state[STATE_SERVICES_DF].index:
            st.divider()
            st.subheader(f"📝 Editing Service (Row: {edit_index})")
            service_data = st.session_state[STATE_SERVICES_DF].loc[edit_index]

            with st.form(f"edit_service_form_{edit_index}"):
                st.markdown(f"Editing: **{service_data[COL_NAME]}**")
                # Generally safer not to edit name easily, could break lookups.
                # If needed, add uniqueness checks.
                # edited_name = st.text_input("Service Name", value=service_data[COL_NAME], key=f"edit_name_{edit_index}")

                cols_edit = st.columns(3)
                with cols_edit[0]:
                    edited_cases = st.number_input("Expected Cases / Month", min_value=0, step=1, key=f"edit_cases_{edit_index}", value=int(service_data[COL_EXPECTED_CASES]))
                with cols_edit[1]:
                    edited_var_cost = st.number_input("Variable Cost / Case (EGP)", min_value=0.0, step=10.0, format="%.2f", key=f"edit_var_cost_{edit_index}", value=float(service_data[COL_VAR_COST]))
                with cols_edit[2]:
                     edited_duration = st.number_input("Duration (hours)", min_value=0.1, step=0.25, format="%.2f", key=f"edit_duration_{edit_index}", value=float(service_data[COL_DURATION]))

                # Buttons for Save/Cancel side-by-side
                col_btn1, col_btn2, _ = st.columns([1,1,4]) # Adjust ratios
                submitted_edit = col_btn1.form_submit_button("💾 Save Changes", type="primary")
                submitted_cancel = col_btn2.form_submit_button("❌ Cancel Edit")

                if submitted_edit:
                     if edited_duration <= 0:
                          st.warning("Duration must be greater than zero.")
                     else:
                        # Update the DataFrame
                        st.session_state[STATE_SERVICES_DF].loc[edit_index, COL_EXPECTED_CASES] = edited_cases
                        st.session_state[STATE_SERVICES_DF].loc[edit_index, COL_VAR_COST] = edited_var_cost
                        st.session_state[STATE_SERVICES_DF].loc[edit_index, COL_DURATION] = edited_duration
                        # Name update if enabled:
                        # st.session_state[STATE_SERVICES_DF].loc[edit_index, COL_NAME] = edited_name

                        st.session_state[STATE_EDIT_TARGET_INDEX] = None # Clear edit state
                        st.success(f"Service '{service_data[COL_NAME]}' updated.")
                        st.rerun()
                if submitted_cancel:
                     st.session_state[STATE_EDIT_TARGET_INDEX] = None
                     st.rerun()
        else:
            # Index no longer valid, clear state and inform user
             st.session_state[STATE_EDIT_TARGET_INDEX] = None
             st.warning("The service you were editing seems to have been removed.")
             st.rerun()


    # --- Add New Service Form (in an expander) ---
    st.divider()
    with st.expander("➕ Add New Service", expanded=(st.session_state[STATE_EDIT_TARGET_INDEX] is None and st.session_state[STATE_SERVICES_DF].empty)):
        with st.form("add_service_form", clear_on_submit=True):
            new_name = st.text_input("New Service Name*")
            cols_add = st.columns(3)
            with cols_add[0]:
                new_expected_cases = st.number_input("Expected Cases / Month*", min_value=0, step=1, key="add_cases")
            with cols_add[1]:
                new_variable_cost = st.number_input("Variable Cost / Case (EGP)*", min_value=0.0, step=10.0, format="%.2f", key="add_var_cost")
            with cols_add[2]:
                new_duration = st.number_input("Duration (hours)*", min_value=0.1, step=0.25, format="%.2f", key="add_duration", help="Average chair time in hours")

            submitted_add = st.form_submit_button("✨ Add Service to List")
            if submitted_add:
                if not new_name:
                    st.warning("Please enter a name for the new service.")
                elif new_duration <= 0:
                    st.warning("Duration must be greater than zero.")
                elif new_name in st.session_state[STATE_SERVICES_DF][COL_NAME].tolist():
                    st.warning(f"A service named '{new_name}' already exists. Please choose a unique name.")
                else:
                    new_service_data = pd.DataFrame([{
                        COL_NAME: new_name,
                        COL_EXPECTED_CASES: new_expected_cases,
                        COL_VAR_COST: new_variable_cost,
                        COL_DURATION: new_duration
                    }])
                    st.session_state[STATE_SERVICES_DF] = pd.concat(
                        [st.session_state[STATE_SERVICES_DF], new_service_data],
                        ignore_index=True
                    )
                    # Ensure types are correct after adding
                    st.session_state[STATE_SERVICES_DF][COL_EXPECTED_CASES] = st.session_state[STATE_SERVICES_DF][COL_EXPECTED_CASES].astype(int)
                    st.session_state[STATE_SERVICES_DF][COL_VAR_COST] = st.session_state[STATE_SERVICES_DF][COL_VAR_COST].astype(float)
                    st.session_state[STATE_SERVICES_DF][COL_DURATION] = st.session_state[STATE_SERVICES_DF][COL_DURATION].astype(float)

                    st.success(f"Service '{new_name}' added.")
                    st.rerun()

    st.divider()

    # --- Calculation Trigger ---
    st.header("Pricing Calculation")
    st.markdown("Click the button below to calculate the detailed pricing based on the current services, fixed costs, and target margin set in the sidebar.")
    if st.button("💰 Calculate Pricing & Update Analysis", type="primary", use_container_width=True):
        current_services_df = st.session_state[STATE_SERVICES_DF]
        # Read fixed cost and margin directly from sidebar widgets for calculation
        fixed_cost_for_calc = current_total_fixed_cost
        margin_for_calc = current_margin

        if not current_services_df.empty:
            results = calculate_detailed_pricing(
                current_services_df,
                fixed_cost_for_calc,
                margin_for_calc
            )
            if results is not None:
                # Store results and the parameters used for calculation in state
                st.session_state[STATE_RESULTS_DF] = results
                st.session_state[STATE_CALCULATED_FIXED_COST] = fixed_cost_for_calc
                st.session_state[STATE_CALCULATED_MARGIN] = margin_for_calc
                st.session_state[STATE_CALCULATED] = True
                st.success("Pricing calculated successfully!")
                # st.balloons() # Optional fun feedback
            else:
                 st.session_state[STATE_CALCULATED] = False # Indicate calculation failed
                 st.error("Calculation failed. Please check service data and fixed costs.")
        else:
            st.warning("Cannot calculate pricing. Please add at least one service.")
            st.session_state[STATE_CALCULATED] = False


    # --- Display Results Table (if calculated) ---
    if st.session_state[STATE_CALCULATED] and st.session_state[STATE_RESULTS_DF] is not None:
        st.divider()
        st.subheader("📋 Detailed Pricing Results")
        results_df_display = st.session_state[STATE_RESULTS_DF]

        # Prepare display dataframe
        display_df_final = results_df_display[[
            COL_NAME, COL_EXPECTED_CASES, COL_VAR_COST, COL_DURATION,
            COL_FIXED_COST_PER_CASE, COL_TOTAL_COST_PER_CASE, COL_PRICE_PER_CASE,
            COL_CONTRIB_MARGIN, COL_BREAK_EVEN
        ]].rename(columns={ # Rename for better readability in the table
            COL_NAME: "Service Name", COL_EXPECTED_CASES: "Expected Cases",
            COL_VAR_COST: "Variable Cost/Case", COL_DURATION: "Duration (hr)",
            COL_FIXED_COST_PER_CASE: "Alloc. Fixed Cost/Case", COL_TOTAL_COST_PER_CASE: "Total Cost/Case",
            COL_PRICE_PER_CASE: "Suggested Price/Case", COL_CONTRIB_MARGIN: "Contribution Margin/Case",
            COL_BREAK_EVEN: "Break-Even (Cases)"
        })

        st.dataframe(display_df_final.style.format({
            "Variable Cost/Case": "{:,.2f} EGP",
            "Duration (hr)": "{:.2f}",
            "Alloc. Fixed Cost/Case": "{:,.2f} EGP",
            "Total Cost/Case": "{:,.2f} EGP",
            "Suggested Price/Case": "{:,.2f} EGP",
            "Contribution Margin/Case": "{:,.2f} EGP",
            "Break-Even (Cases)": "{:.1f}"
        }), use_container_width=True)

        # --- Overall Summary Metrics ---
        st.subheader("📈 Overall Monthly Projections")
        total_expected_revenue = (results_df_display[COL_PRICE_PER_CASE] * results_df_display[COL_EXPECTED_CASES]).sum()
        total_expected_variable_cost = (results_df_display[COL_VAR_COST] * results_df_display[COL_EXPECTED_CASES]).sum()
        # Use fixed cost that was actually used in calculation
        total_fixed_cost_used = st.session_state[STATE_CALCULATED_FIXED_COST]
        total_expected_profit = total_expected_revenue - total_expected_variable_cost - total_fixed_cost_used

        summary_cols = st.columns(3)
        summary_cols[0].metric("Projected Revenue", f"{total_expected_revenue:,.2f} EGP")
        summary_cols[1].metric("Projected Total Costs", f"{(total_expected_variable_cost + total_fixed_cost_used):,.2f} EGP")
        summary_cols[2].metric("Projected Profit", f"{total_expected_profit:,.2f} EGP")

    # Show message if calculation hasn't run yet
    elif not st.session_state[STATE_CALCULATED]:
         st.info("Please manage your services and click 'Calculate Pricing' to see the results here.")


# --- Tab 2: Sensitivity Analysis ---
with tab2:
    st.header("Sensitivity Analysis")
    st.markdown("""
    Analyze how the **Suggested Price** and **Break-Even Point** for a specific service change
    if the actual number of cases differs from your initial expectation.
    This uses the fixed cost allocation and margin calculated in the previous step.
    """)

    if not st.session_state[STATE_CALCULATED] or st.session_state[STATE_RESULTS_DF] is None:
        st.warning("Please run the pricing calculation on the 'Service Management & Pricing' tab first.")
    else:
        results_df_analysis = st.session_state[STATE_RESULTS_DF]
        if results_df_analysis.empty or COL_NAME not in results_df_analysis.columns:
             st.warning("No valid calculation results found for analysis.")
        else:
            # Use English name if available, otherwise default name
            service_names_options = results_df_analysis[COL_NAME].tolist() # Assuming names are suitable for display

            if not service_names_options:
                st.warning("No services available in the calculated results.")
            else:
                selected_service_name = st.selectbox(
                    "Select Service for Analysis:",
                    options=service_names_options,
                    index=0,
                    key="service_select_analysis"
                )

                if selected_service_name and selected_service_name in results_df_analysis[COL_NAME].values:
                    service_data = results_df_analysis[results_df_analysis[COL_NAME] == selected_service_name].iloc[0]

                    st.markdown(f"#### Analysis for: **{selected_service_name}**")
                    expected_cases_display = int(service_data[COL_EXPECTED_CASES])
                    allocated_fc_display = service_data[COL_ALLOC_FIXED_COST]
                    st.caption(f"Based on initial expectation of **{expected_cases_display} cases/month** and allocated fixed costs of **{allocated_fc_display:,.2f} EGP**.")


                    st.markdown("##### Define Analysis Range:")
                    sens_cols = st.columns(3)
                    with sens_cols[0]:
                        min_cases = st.number_input("Min Cases", min_value=1, value=max(1, int(expected_cases_display * 0.2)), step=1, key="min_cases_sens")
                    with sens_cols[1]:
                        max_cases = st.number_input("Max Cases", min_value=int(min_cases)+1, value=int(expected_cases_display * 2.0), step=5, key="max_cases_sens")
                    with sens_cols[2]:
                        step_cases = st.number_input("Step", min_value=1, value=max(1, int((max_cases - min_cases)/10) if (max_cases - min_cases)>0 else 1), step=1, key="step_cases_sens")

                    if max_cases <= min_cases:
                        st.error("Max Cases must be greater than Min Cases.")
                    else:
                        cases_range_list = list(range(int(min_cases), int(max_cases) + 1, int(step_cases)))
                        if not cases_range_list:
                             st.warning("The specified range and step result in no cases to analyze.")
                        else:
                            # Perform sensitivity analysis using the stored calculated margin
                            margin_used = st.session_state[STATE_CALCULATED_MARGIN]
                            prices, break_evens = calculate_sensitivity(
                                variable_cost=service_data[COL_VAR_COST],
                                allocated_fixed_cost=service_data[COL_ALLOC_FIXED_COST], # Key: use the allocated cost
                                margin=margin_used,
                                cases_range=cases_range_list
                            )

                            # Generate and display plots
                            st.markdown("##### Analysis Results:")
                            sensitivity_fig = plot_sensitivity(cases_range_list, prices, break_evens)
                            st.pyplot(sensitivity_fig)

                            # Optional: Display data table for sensitivity
                            # sens_data = pd.DataFrame({ ... })
                            # st.dataframe(sens_data...)
                else:
                    st.error(f"Selected service '{selected_service_name}' not found in the current results. Please recalculate.")
