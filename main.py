import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np # Needed for calculations like sumproduct, where, etc.
from typing import List, Dict, Any, Tuple, Optional
import copy

# --- Constants ---
# Define column names
COL_NAME = "name"
COL_NAME_EN = "name_en" # Added for consistent dropdown/plot labels if needed
COL_EXPECTED_CASES = "expected_cases"
COL_VAR_COST = "variable_cost"
COL_DURATION = "duration_hours"
COL_ALLOC_FIXED_COST = "allocated_fixed_cost"
COL_FIXED_COST_PER_CASE = "fixed_cost_per_case"
COL_TOTAL_COST_PER_CASE = "total_cost_per_case"
COL_PRICE_PER_CASE = "price_per_case"
COL_CONTRIB_MARGIN = "contribution_margin"
COL_CONTRIB_MARGIN_RATIO = "contribution_margin_ratio"
COL_BREAK_EVEN = "break_even_cases" # Renamed for clarity
COL_SERVICE_HOURS = "service_hours_total" # Renamed for clarity (total for the expected cases)
COL_REVENUE_EXPECTED = "revenue_expected"
COL_PROFIT_EXPECTED = "profit_expected"
COL_CM_PER_HOUR = "contribution_margin_per_hour"
COL_REVENUE_PER_HOUR = "revenue_per_hour"

# Define keys for session state
STATE_SERVICES_DF = "services_df" # Main DataFrame for service inputs
STATE_EDIT_TARGET_INDEX = "edit_target_index" # Index of row being edited
STATE_RESULTS_DF = "results_df" # DataFrame for calculated results
STATE_CALCULATED_FIXED_COST = "calculated_fixed_cost" # Store fixed cost used for last calc
STATE_CALCULATED_MARGIN = "calculated_margin" # Store margin used for last calc
STATE_CALCULATED = "calculated" # Flag
STATE_SIMULATION_PARAMS = "simulation_params" # Store overrides for scenario simulation


# --- Helper Functions ---

def initialize_session_state():
    """Initializes required keys in Streamlit's session state."""
    default_services_data = [
        # Added 'name_en' for consistency if original names are Arabic
        {"name": "تنظيف الأسنان", "name_en": "Dental Cleaning", "expected_cases": 80, "variable_cost": 150.0, "duration_hours": 1.0},
        {"name": "حشو الأسنان", "name_en": "Filling", "expected_cases": 60, "variable_cost": 250.0, "duration_hours": 1.0},
        {"name": "علاج جذور الأسنان", "name_en": "Root Canal Therapy", "expected_cases": 40, "variable_cost": 500.0, "duration_hours": 2.0},
        {"name": "تقويم الأسنان", "name_en": "Orthodontics Setup", "expected_cases": 20, "variable_cost": 1000.0, "duration_hours": 2.0},
        {"name": "تبييض الأسنان", "name_en": "Teeth Whitening", "expected_cases": 50, "variable_cost": 350.0, "duration_hours": 1.0},
        {"name": "زراعة الأسنان", "name_en": "Dental Implant", "expected_cases": 10, "variable_cost": 3000.0, "duration_hours": 3.0}
    ]
    if STATE_SERVICES_DF not in st.session_state:
        st.session_state[STATE_SERVICES_DF] = pd.DataFrame(default_services_data)
        # Ensure correct types on initialization
        for col, dtype in {COL_EXPECTED_CASES: int, COL_VAR_COST: float, COL_DURATION: float}.items():
             try:
                  st.session_state[STATE_SERVICES_DF][col] = st.session_state[STATE_SERVICES_DF][col].astype(dtype)
             except Exception as e:
                  st.warning(f"Initial data type issue for column {col}: {e}")
                  # Fallback or handle appropriately


    if STATE_EDIT_TARGET_INDEX not in st.session_state: st.session_state[STATE_EDIT_TARGET_INDEX] = None
    if STATE_RESULTS_DF not in st.session_state: st.session_state[STATE_RESULTS_DF] = None
    if STATE_CALCULATED_FIXED_COST not in st.session_state: st.session_state[STATE_CALCULATED_FIXED_COST] = 0.0
    if STATE_CALCULATED_MARGIN not in st.session_state: st.session_state[STATE_CALCULATED_MARGIN] = 0.30
    if STATE_CALCULATED not in st.session_state: st.session_state[STATE_CALCULATED] = False
    if STATE_SIMULATION_PARAMS not in st.session_state: st.session_state[STATE_SIMULATION_PARAMS] = {}


def calculate_detailed_pricing(services_df: pd.DataFrame, total_fixed_cost: float, margin: float) -> Optional[pd.DataFrame]:
    """Calculates detailed pricing and related metrics."""
    if services_df.empty:
        st.error("No service data available for calculation.")
        return None

    calc_df = services_df.copy()

    # --- Data Type Conversion and Validation ---
    try:
        calc_df[COL_EXPECTED_CASES] = pd.to_numeric(calc_df[COL_EXPECTED_CASES], errors='coerce').fillna(0).astype(int)
        calc_df[COL_VAR_COST] = pd.to_numeric(calc_df[COL_VAR_COST], errors='coerce').fillna(0.0).astype(float)
        calc_df[COL_DURATION] = pd.to_numeric(calc_df[COL_DURATION], errors='coerce').fillna(0.1).astype(float) # Default duration 0.1 if invalid

        if (calc_df[COL_EXPECTED_CASES] < 0).any() or \
           (calc_df[COL_VAR_COST] < 0).any() or \
           (calc_df[COL_DURATION] <= 0).any():
             st.error("Please ensure 'Expected Cases' & 'Variable Cost' >= 0, and 'Duration' > 0 for all services.")
             return None
    except Exception as e:
        st.error(f"Data type error in service data: {e}. Please check inputs.")
        return None

    # --- Core Calculations ---
    calc_df[COL_SERVICE_HOURS] = calc_df[COL_EXPECTED_CASES] * calc_df[COL_DURATION]
    total_service_hours = calc_df[COL_SERVICE_HOURS].sum()

    if total_service_hours <= 0:
        st.warning("Total weighted service hours is zero. Cannot allocate fixed costs. Fixed costs per case set to 0.")
        calc_df[COL_ALLOC_FIXED_COST] = 0.0
        calc_df[COL_FIXED_COST_PER_CASE] = 0.0
    else:
        calc_df[COL_ALLOC_FIXED_COST] = total_fixed_cost * (calc_df[COL_SERVICE_HOURS] / total_service_hours)
        calc_df[COL_FIXED_COST_PER_CASE] = np.where(calc_df[COL_EXPECTED_CASES] > 0, calc_df[COL_ALLOC_FIXED_COST] / calc_df[COL_EXPECTED_CASES], 0)

    calc_df[COL_TOTAL_COST_PER_CASE] = calc_df[COL_VAR_COST] + calc_df[COL_FIXED_COST_PER_CASE]
    calc_df[COL_PRICE_PER_CASE] = calc_df[COL_TOTAL_COST_PER_CASE] * (1 + margin)
    calc_df[COL_CONTRIB_MARGIN] = calc_df[COL_PRICE_PER_CASE] - calc_df[COL_VAR_COST]

    # --- Additional Metrics ---
    calc_df[COL_CONTRIB_MARGIN_RATIO] = np.where(calc_df[COL_PRICE_PER_CASE] > 0, calc_df[COL_CONTRIB_MARGIN] / calc_df[COL_PRICE_PER_CASE], 0)
    calc_df[COL_BREAK_EVEN] = np.where(calc_df[COL_CONTRIB_MARGIN] > 0, calc_df[COL_ALLOC_FIXED_COST] / calc_df[COL_CONTRIB_MARGIN], float('inf'))
    calc_df[COL_REVENUE_EXPECTED] = calc_df[COL_PRICE_PER_CASE] * calc_df[COL_EXPECTED_CASES]
    # Profit per service = (CM per case * Cases) - Allocated Fixed Cost for that service
    calc_df[COL_PROFIT_EXPECTED] = (calc_df[COL_CONTRIB_MARGIN] * calc_df[COL_EXPECTED_CASES]) - calc_df[COL_ALLOC_FIXED_COST]

    # Per Hour Metrics
    calc_df[COL_REVENUE_PER_HOUR] = np.where(calc_df[COL_DURATION] > 0, calc_df[COL_PRICE_PER_CASE] / calc_df[COL_DURATION], 0)
    calc_df[COL_CM_PER_HOUR] = np.where(calc_df[COL_DURATION] > 0, calc_df[COL_CONTRIB_MARGIN] / calc_df[COL_DURATION], 0)

    # Add English name if missing and original name exists
    if COL_NAME_EN not in calc_df.columns and COL_NAME in calc_df.columns:
         calc_df[COL_NAME_EN] = calc_df[COL_NAME] # Default to original name if EN is missing


    return calc_df

# --- Plotting Functions ---
def plot_bar_chart(df, x_col, y_col, title, xlabel, ylabel, sort_by_y=True, color='skyblue'):
    """Helper to create a formatted bar chart."""
    if df.empty: return None
    fig, ax = plt.subplots(figsize=(10, 6))
    data_to_plot = df.copy()
    if sort_by_y:
        data_to_plot = data_to_plot.sort_values(by=y_col, ascending=False)

    bars = ax.bar(data_to_plot[x_col], data_to_plot[y_col], color=color)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.tick_params(axis='x', rotation=45, labelsize=10)
    ax.tick_params(axis='y', labelsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    # Add data labels
    ax.bar_label(bars, fmt='{:,.0f}', fontsize=9, padding=3)
    fig.tight_layout()
    return fig

def plot_pie_chart(sizes, labels, title):
    """Helper to create a formatted pie chart."""
    if not sizes or not labels or len(sizes) != len(labels): return None
    fig, ax = plt.subplots(figsize=(8, 8))
    # Explode the largest slice slightly for emphasis
    explode = tuple([0.1 if s == max(sizes) else 0 for s in sizes])
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
                                      pctdistance=0.85, explode=explode,
                                      textprops={'fontsize': 10})
    # Style autopct labels
    plt.setp(autotexts, size=9, weight="bold", color="white")
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.axis('equal') # Equal aspect ratio ensures a circular pie chart
    # Add a legend (optional, can be crowded)
    # ax.legend(wedges, labels, title="Categories", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    return fig


# Sensitivity calculation and plot functions remain the same
def calculate_sensitivity(variable_cost: float, allocated_fixed_cost: float, margin: float, cases_range: range) -> Tuple[List[float], List[float]]:
    # ... (Implementation is identical to previous versions) ...
    prices = []
    break_evens = []
    for cases in cases_range:
        if cases <= 0: price, be = float('inf'), float('inf')
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
    axs[0].plot(cases_range, prices, marker='o', linestyle='-', color='royalblue'); axs[0].set_title("Price Sensitivity vs. Number of Cases"); axs[0].set_xlabel("Number of Cases"); axs[0].set_ylabel("Calculated Price per Case (EGP)"); axs[0].grid(True, linestyle='--', alpha=0.6); axs[0].ticklabel_format(style='plain', axis='y')
    axs[1].plot(cases_range, break_evens, marker='x', linestyle='--', color='crimson'); axs[1].set_title("Break-Even Point vs. Number of Cases"); axs[1].set_xlabel("Number of Cases"); axs[1].set_ylabel("Calculated Break-Even Point (Cases)"); axs[1].grid(True, linestyle='--', alpha=0.6); finite_bes = [be for be in break_evens if be != float('inf')]; axs[1].set_ylim(bottom=0, top=max(finite_bes) * 1.15 if finite_bes else 10); axs[1].ticklabel_format(style='plain', axis='y')
    return fig


# --- Streamlit App ---
st.set_page_config(layout="wide", page_title="Advanced Dental Pricing Dashboard")
initialize_session_state()

# --- Sidebar ---
with st.sidebar:
    # ... (Fixed cost inputs remain the same) ...
    st.image("https://img.icons8.com/external-flaticons-lineal-color-flat-icons/64/external-dental-clinic-dental-flaticons-lineal-color-flat-icons-3.png", width=64)
    st.title("Clinic Settings")
    st.header("1. Monthly Fixed Costs (EGP)")
    rent = st.number_input("Rent", min_value=0.0, value=15000.0, step=500.0, key="rent_sb")
    salaries = st.number_input("Staff Salaries", min_value=0.0, value=20000.0, step=500.0, key="salaries_sb")
    utilities = st.number_input("Utilities", min_value=0.0, value=5000.0, step=200.0, key="utilities_sb")
    insurance = st.number_input("Insurance & Maintenance", min_value=0.0, value=2000.0, step=100.0, key="insurance_sb")
    marketing = st.number_input("Marketing", min_value=0.0, value=1000.0, step=100.0, key="marketing_sb")
    other_fixed = st.number_input("Other Fixed Costs", min_value=0.0, value=0.0, step=100.0, key="other_fixed_sb")
    current_total_fixed_cost = rent + salaries + utilities + insurance + marketing + other_fixed
    st.metric(label="**Total Monthly Fixed Costs**", value=f"{current_total_fixed_cost:,.2f} EGP")
    st.divider()

    st.header("2. Base Target Profit Margin")
    current_margin_percentage = st.slider(
        "Base Profit Margin (%)", 0, 200,
        int(st.session_state.get(STATE_CALCULATED_MARGIN, 0.30) * 100), 5,
        key="margin_slider_sb", help="Default margin applied during calculation. Can be overridden in Scenario Simulation.")
    current_margin = current_margin_percentage / 100.0
    st.info(f"Base Target Margin: {current_margin_percentage}%")


# --- Main Content Tabs ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📁 Setup & Pricing",
    "💰 Profitability Analysis",
    "⏱️ Time & Efficiency",
    "⚙️ Scenario Simulation"
])

# === TAB 1: Setup & Pricing ===
with tab1:
    st.header("Service Setup & Pricing Calculation")
    st.markdown("Manage services, set global costs/margin in the sidebar, then calculate pricing.")

    # --- Service Management Section ---
    st.subheader("Manage Services List")
    # ... (DataFrame display, Edit/Delete buttons, Edit Form, Add Form - Code is similar to previous version, ensure keys are unique) ...
    # Display DataFrame
    if st.session_state[STATE_SERVICES_DF].empty: st.info("No services added yet.")
    else:
         st.dataframe(st.session_state[STATE_SERVICES_DF], hide_index=True, use_container_width=True,
                      column_config={ COL_NAME: st.column_config.TextColumn("Service Name (Original)"), COL_NAME_EN: st.column_config.TextColumn("Service Name (Display)"), COL_EXPECTED_CASES: st.column_config.NumberColumn("Exp. Cases/Month", format="%d"), COL_VAR_COST: st.column_config.NumberColumn("Var. Cost/Case (EGP)", format="%.2f"), COL_DURATION: st.column_config.NumberColumn("Duration (hr)", format="%.2f")})

    # Edit/Delete Actions
    st.markdown("--- **Modify Services** ---")
    # ... (Edit/Delete button logic - similar implementation as before, using unique keys) ...
    services_df_display = st.session_state[STATE_SERVICES_DF]
    indices_to_delete = []
    num_services = len(services_df_display)
    cols_per_row = 3
    col_idx = 0
    if not services_df_display.empty:
        for index in services_df_display.index:
            service_name_display = services_df_display.loc[index, COL_NAME_EN] # Use English name for display if available
            if col_idx % cols_per_row == 0: cols = st.columns(cols_per_row)
            with cols[col_idx % cols_per_row]:
                 st.markdown(f"**{service_name_display}**")
                 sub_cols = st.columns(2)
                 edit_key = f"edit_{index}_{service_name_display.replace(' ', '_')}"
                 if sub_cols[0].button("✏️ Edit", key=edit_key): st.session_state[STATE_EDIT_TARGET_INDEX] = index; st.rerun()
                 delete_key = f"delete_{index}_{service_name_display.replace(' ', '_')}"
                 if sub_cols[1].button("🗑️ Delete", key=delete_key): indices_to_delete.append(index); st.rerun() # Rerun needed here to prevent index issues if multiple deleted quickly
            col_idx += 1
        if indices_to_delete:
             st.session_state[STATE_SERVICES_DF] = services_df_display.drop(indices_to_delete).reset_index(drop=True)
             if st.session_state[STATE_EDIT_TARGET_INDEX] in indices_to_delete: st.session_state[STATE_EDIT_TARGET_INDEX] = None
             st.rerun() # Rerun to reflect changes


    # Conditional Edit Form
    if st.session_state[STATE_EDIT_TARGET_INDEX] is not None:
         # ... (Edit form logic - similar to previous, ensure using unique keys, add name_en field) ...
        edit_index = st.session_state[STATE_EDIT_TARGET_INDEX]
        if edit_index in st.session_state[STATE_SERVICES_DF].index:
            st.divider()
            st.subheader(f"📝 Editing Service")
            service_data = st.session_state[STATE_SERVICES_DF].loc[edit_index]
            with st.form(f"edit_service_form_{edit_index}"):
                st.markdown(f"Editing: **{service_data[COL_NAME_EN]}** (Original: {service_data[COL_NAME]})")
                edited_name_orig = st.text_input("Service Name (Original)", value=service_data[COL_NAME])
                edited_name_en = st.text_input("Service Name (Display/English)", value=service_data[COL_NAME_EN])
                cols_edit = st.columns(3)
                with cols_edit[0]: edited_cases = st.number_input("Exp. Cases/Month", 0, value=int(service_data[COL_EXPECTED_CASES]))
                with cols_edit[1]: edited_var_cost = st.number_input("Var. Cost/Case (EGP)", 0.0, value=float(service_data[COL_VAR_COST]), format="%.2f")
                with cols_edit[2]: edited_duration = st.number_input("Duration (hr)", 0.1, value=float(service_data[COL_DURATION]), format="%.2f")
                col_btn1, col_btn2, _ = st.columns([1,1,4])
                submitted_edit = col_btn1.form_submit_button("💾 Save", type="primary")
                submitted_cancel = col_btn2.form_submit_button("❌ Cancel")
                if submitted_edit:
                    if edited_duration <= 0 or not edited_name_orig or not edited_name_en: st.warning("Please fill all fields and ensure duration > 0.")
                    else:
                        st.session_state[STATE_SERVICES_DF].loc[edit_index, COL_NAME] = edited_name_orig
                        st.session_state[STATE_SERVICES_DF].loc[edit_index, COL_NAME_EN] = edited_name_en
                        st.session_state[STATE_SERVICES_DF].loc[edit_index, COL_EXPECTED_CASES] = edited_cases
                        st.session_state[STATE_SERVICES_DF].loc[edit_index, COL_VAR_COST] = edited_var_cost
                        st.session_state[STATE_SERVICES_DF].loc[edit_index, COL_DURATION] = edited_duration
                        st.session_state[STATE_EDIT_TARGET_INDEX] = None; st.success("Service updated."); st.rerun()
                if submitted_cancel: st.session_state[STATE_EDIT_TARGET_INDEX] = None; st.rerun()
        else: st.session_state[STATE_EDIT_TARGET_INDEX] = None; st.warning("Edited service removed."); st.rerun()


    # Add New Service Form Expander
    with st.expander("➕ Add New Service"):
         # ... (Add form logic - similar to previous, ensure using unique keys, add name_en field) ...
         with st.form("add_service_form", clear_on_submit=True):
            new_name = st.text_input("New Service Name (Original)*")
            new_name_en = st.text_input("New Service Name (Display/English)*", value=new_name) # Default to original
            cols_add = st.columns(3)
            with cols_add[0]: new_expected_cases = st.number_input("Exp. Cases/Month*", 0, key="add_cases")
            with cols_add[1]: new_variable_cost = st.number_input("Var. Cost/Case (EGP)*", 0.0, format="%.2f", key="add_var_cost")
            with cols_add[2]: new_duration = st.number_input("Duration (hr)*", 0.1, format="%.2f", key="add_duration")
            submitted_add = st.form_submit_button("✨ Add Service")
            if submitted_add:
                if not new_name or not new_name_en or new_duration <= 0: st.warning("Please fill all required fields (*) and ensure duration > 0.")
                elif new_name_en in st.session_state[STATE_SERVICES_DF][COL_NAME_EN].tolist(): st.warning(f"Service '{new_name_en}' already exists (display name). Choose unique names.")
                else:
                    new_data = {COL_NAME: new_name, COL_NAME_EN: new_name_en, COL_EXPECTED_CASES: new_expected_cases, COL_VAR_COST: new_variable_cost, COL_DURATION: new_duration}
                    st.session_state[STATE_SERVICES_DF] = pd.concat([st.session_state[STATE_SERVICES_DF], pd.DataFrame([new_data])], ignore_index=True)
                    st.success(f"Service '{new_name_en}' added."); st.rerun()


    st.divider()
    # --- Calculation Trigger ---
    st.header("Calculate Pricing")
    if st.button("💰 Calculate Detailed Pricing & KPIs", type="primary", use_container_width=True):
        # ... (Calculation logic - same as before, reads from sidebar, stores results) ...
        fixed_cost_for_calc = current_total_fixed_cost
        margin_for_calc = current_margin
        current_services_df = st.session_state[STATE_SERVICES_DF]
        if not current_services_df.empty:
            results = calculate_detailed_pricing(current_services_df, fixed_cost_for_calc, margin_for_calc)
            if results is not None:
                st.session_state[STATE_RESULTS_DF] = results
                st.session_state[STATE_CALCULATED_FIXED_COST] = fixed_cost_for_calc
                st.session_state[STATE_CALCULATED_MARGIN] = margin_for_calc
                st.session_state[STATE_CALCULATED] = True
                st.success("Pricing calculated successfully!")
            else: st.session_state[STATE_CALCULATED] = False; st.error("Calculation failed.")
        else: st.warning("Add services before calculating."); st.session_state[STATE_CALCULATED] = False


    # --- Display Results & KPIs (if calculated) ---
    if st.session_state[STATE_CALCULATED] and st.session_state[STATE_RESULTS_DF] is not None:
        st.divider()
        st.header("Calculation Results")
        results_df_display = st.session_state[STATE_RESULTS_DF]

        # --- Display KPIs ---
        st.subheader("📊 Key Performance Indicators (KPIs)")
        kp_cols = st.columns(4)
        total_revenue = results_df_display[COL_REVENUE_EXPECTED].sum()
        total_profit = results_df_display[COL_PROFIT_EXPECTED].sum() # Sum of individual profits should equal overall
        total_var_cost = (results_df_display[COL_VAR_COST] * results_df_display[COL_EXPECTED_CASES]).sum()
        total_fixed_cost_used = st.session_state[STATE_CALCULATED_FIXED_COST]
        total_cost = total_var_cost + total_fixed_cost_used
        overall_margin_pct = (total_profit / total_revenue * 100) if total_revenue else 0

        # Calculate overall Break-Even Revenue
        total_cm_ratio = np.average(results_df_display[COL_CONTRIB_MARGIN_RATIO], weights=results_df_display[COL_REVENUE_EXPECTED]) if total_revenue else 0
        total_break_even_revenue = (total_fixed_cost_used / total_cm_ratio) if total_cm_ratio > 0 else float('inf')

        # Per Hour KPIs
        total_hours = results_df_display[COL_SERVICE_HOURS].sum()
        avg_revenue_per_hour = total_revenue / total_hours if total_hours else 0
        avg_cm_per_hour = (total_revenue - total_var_cost) / total_hours if total_hours else 0


        kp_cols[0].metric("Total Projected Revenue", f"{total_revenue:,.0f} EGP")
        kp_cols[1].metric("Total Projected Profit", f"{total_profit:,.0f} EGP")
        kp_cols[2].metric("Overall Profit Margin", f"{overall_margin_pct:.1f}%")
        if total_break_even_revenue == float('inf'):
             kp_cols[3].metric("Overall Break-Even Revenue", "N/A (Loss)", delta_color="inverse")
        else:
             kp_cols[3].metric("Overall Break-Even Revenue", f"{total_break_even_revenue:,.0f} EGP")

        kp_cols2 = st.columns(4)
        kp_cols2[0].metric("Avg. Revenue per Hour", f"{avg_revenue_per_hour:,.0f} EGP")
        kp_cols2[1].metric("Avg. Contribution Margin / Hour", f"{avg_cm_per_hour:,.0f} EGP")
        kp_cols2[2].metric("Total Hours Projected", f"{total_hours:,.1f} hrs")


        # --- Display Detailed Results Table ---
        st.subheader("📋 Detailed Pricing per Service")
        # ... (DataFrame formatting - similar to previous, but use new column names) ...
        display_df_final = results_df_display[[
            COL_NAME_EN, COL_EXPECTED_CASES, COL_VAR_COST, COL_DURATION,
            COL_ALLOC_FIXED_COST, COL_FIXED_COST_PER_CASE, COL_TOTAL_COST_PER_CASE,
            COL_PRICE_PER_CASE, COL_CONTRIB_MARGIN, COL_CONTRIB_MARGIN_RATIO, COL_BREAK_EVEN
        ]].rename(columns={
             COL_NAME_EN: "Service", COL_EXPECTED_CASES: "Cases",
             COL_VAR_COST: "Var Cost", COL_DURATION: "Hrs",
             COL_ALLOC_FIXED_COST: "Alloc FixCost", COL_FIXED_COST_PER_CASE: "FixCost/Case",
             COL_TOTAL_COST_PER_CASE: "TotalCost/Case", COL_PRICE_PER_CASE: "Price/Case",
             COL_CONTRIB_MARGIN: "CM/Case", COL_CONTRIB_MARGIN_RATIO: "CM Ratio",
             COL_BREAK_EVEN: "BEP (Cases)"
         })
        st.dataframe(display_df_final.style.format({
            "Var Cost": "{:,.0f}", "Hrs": "{:.1f}", "Alloc FixCost": "{:,.0f}",
            "FixCost/Case": "{:,.0f}", "TotalCost/Case": "{:,.0f}", "Price/Case": "{:,.0f}",
            "CM/Case": "{:,.0f}", "CM Ratio": "{:.1%}", "BEP (Cases)": "{:.1f}"
        }).background_gradient(cmap='Greens', subset=['CM/Case', 'CM Ratio']), use_container_width=True)


    elif not st.session_state[STATE_CALCULATED]: st.info("Calculate pricing to view results.")


# === TAB 2: Profitability Analysis ===
with tab2:
    st.header("Profitability Analysis")
    if not st.session_state[STATE_CALCULATED] or st.session_state[STATE_RESULTS_DF] is None:
        st.warning("Run calculation on 'Setup & Pricing' tab first.")
    else:
        results_df = st.session_state[STATE_RESULTS_DF]
        if results_df.empty: st.warning("No results to analyze.")
        else:
            st.subheader("Contribution Margin Analysis")
            cm_fig = plot_bar_chart(results_df, COL_NAME_EN, COL_CONTRIB_MARGIN,
                                    "Contribution Margin per Case by Service",
                                    "Service", "Contribution Margin (EGP)", color='lightcoral')
            if cm_fig: st.pyplot(cm_fig)

            st.subheader("Expected Profit Analysis")
            profit_fig = plot_bar_chart(results_df, COL_NAME_EN, COL_PROFIT_EXPECTED,
                                        "Total Expected Profit by Service (Monthly)",
                                        "Service", "Expected Profit (EGP)", color='mediumseagreen')
            if profit_fig: st.pyplot(profit_fig)

            st.subheader("Cost Structure Overview")
            # Calculate total variable and fixed costs from results
            total_var = (results_df[COL_VAR_COST] * results_df[COL_EXPECTED_CASES]).sum()
            total_fixed = results_df[COL_ALLOC_FIXED_COST].sum() # Should match input fixed cost
            cost_structure_fig = plot_pie_chart([total_var, total_fixed],
                                                 ['Total Variable Costs', 'Total Fixed Costs'],
                                                 "Overall Cost Structure")
            if cost_structure_fig: st.pyplot(cost_structure_fig)


# === TAB 3: Time & Efficiency Analysis ===
with tab3:
    st.header("Time & Efficiency Analysis")
    if not st.session_state[STATE_CALCULATED] or st.session_state[STATE_RESULTS_DF] is None:
        st.warning("Run calculation on 'Setup & Pricing' tab first.")
    else:
        results_df = st.session_state[STATE_RESULTS_DF]
        if results_df.empty: st.warning("No results to analyze.")
        else:
            st.subheader("Resource Utilization")
            time_fig = plot_bar_chart(results_df, COL_NAME_EN, COL_SERVICE_HOURS,
                                      "Total Expected Chair Time by Service (Monthly)",
                                      "Service", "Total Hours", color='lightblue')
            if time_fig: st.pyplot(time_fig)

            st.subheader("Revenue per Hour")
            rev_hr_fig = plot_bar_chart(results_df, COL_NAME_EN, COL_REVENUE_PER_HOUR,
                                        "Average Revenue per Hour by Service",
                                        "Service", "Revenue per Hour (EGP)", color='gold')
            if rev_hr_fig: st.pyplot(rev_hr_fig)

            st.subheader("Contribution Margin per Hour")
            st.markdown("*(Price per Hour - Variable Cost per Hour)* - A key metric for profitability relative to time.")
            cm_hr_fig = plot_bar_chart(results_df, COL_NAME_EN, COL_CM_PER_HOUR,
                                       "Average Contribution Margin per Hour by Service",
                                       "Service", "Contribution Margin per Hour (EGP)", color='lightgreen')
            if cm_hr_fig: st.pyplot(cm_hr_fig)


# === TAB 4: Scenario Simulation ===
with tab4:
    st.header("Scenario Simulation ('What-If')")
    st.markdown("""
    Adjust key parameters **based on the last calculation** to see the potential impact on pricing and profitability
    for the entire clinic or specific services **without** permanently changing your setup data.
    """)

    if not st.session_state[STATE_CALCULATED] or st.session_state[STATE_RESULTS_DF] is None:
        st.warning("Run calculation on 'Setup & Pricing' tab first to establish a baseline.")
    else:
        base_results_df = st.session_state[STATE_RESULTS_DF]
        base_fixed_cost = st.session_state[STATE_CALCULATED_FIXED_COST]
        base_margin = st.session_state[STATE_CALCULATED_MARGIN]
        base_services_df = st.session_state[STATE_SERVICES_DF] # Get the input df used

        st.subheader("Simulation Adjustments")

        # --- Global Overrides ---
        sim_cols = st.columns(2)
        with sim_cols[0]:
            sim_fixed_cost = st.number_input("Simulated Total Fixed Costs (EGP)",
                                             min_value=0.0,
                                             value=float(st.session_state[STATE_SIMULATION_PARAMS].get('fixed_cost', base_fixed_cost)),
                                             step=1000.0, key="sim_fc",
                                             help=f"Base calculated value: {base_fixed_cost:,.0f} EGP")
        with sim_cols[1]:
            sim_margin_pct = st.slider("Simulated Profit Margin (%)", 0, 200,
                                      int(st.session_state[STATE_SIMULATION_PARAMS].get('margin', base_margin) * 100), 5,
                                      key="sim_margin",
                                      help=f"Base calculated value: {base_margin*100:.0f}%")
        sim_margin = sim_margin_pct / 100.0

        # --- Service Specific Overrides ---
        st.markdown("**Optional: Adjust Specific Service Parameters**")
        service_options = ["(None - Apply Global Changes Only)"] + base_results_df[COL_NAME_EN].tolist()
        selected_service_sim = st.selectbox("Select Service to Modify in Simulation:", options=service_options, key="sim_select_service")

        sim_var_cost = None
        sim_cases = None
        sim_duration = None
        modified_service_index = None

        if selected_service_sim != "(None - Apply Global Changes Only)":
            service_row = base_services_df[base_services_df[COL_NAME_EN] == selected_service_sim].iloc[0]
            modified_service_index = service_row.name # Get the original index

            sim_spec_cols = st.columns(3)
            with sim_spec_cols[0]:
                sim_var_cost = st.number_input(f"Simulated Var Cost for {selected_service_sim}",
                                                min_value=0.0, value=float(service_row[COL_VAR_COST]), format="%.2f", key=f"sim_vc_{selected_service_sim}")
            with sim_spec_cols[1]:
                sim_cases = st.number_input(f"Simulated Exp. Cases for {selected_service_sim}",
                                              min_value=0, value=int(service_row[COL_EXPECTED_CASES]), key=f"sim_ec_{selected_service_sim}")
            with sim_spec_cols[2]:
                 sim_duration = st.number_input(f"Simulated Duration for {selected_service_sim}",
                                              min_value=0.1, value=float(service_row[COL_DURATION]), format="%.2f", key=f"sim_dur_{selected_service_sim}")


        # --- Run Simulation Button ---
        if st.button("🚀 Run Simulation", key="run_sim_btn"):
            # Store current sim params for persistence if needed
            st.session_state[STATE_SIMULATION_PARAMS] = {'fixed_cost': sim_fixed_cost, 'margin': sim_margin}

            # Create a temporary DataFrame based on the *original inputs* but with overrides
            sim_services_df = base_services_df.copy()
            if modified_service_index is not None and selected_service_sim != "(None - Apply Global Changes Only)":
                if sim_var_cost is not None: sim_services_df.loc[modified_service_index, COL_VAR_COST] = sim_var_cost
                if sim_cases is not None: sim_services_df.loc[modified_service_index, COL_EXPECTED_CASES] = sim_cases
                if sim_duration is not None: sim_services_df.loc[modified_service_index, COL_DURATION] = sim_duration


            # Re-run the *entire* pricing calculation with the simulated inputs
            st.info("Running simulation calculation...")
            simulated_results_df = calculate_detailed_pricing(
                sim_services_df,
                sim_fixed_cost,
                sim_margin
            )

            if simulated_results_df is not None:
                st.subheader("Simulation Results vs. Base Calculation")

                # --- Compare KPIs ---
                st.markdown("**Overall KPI Comparison:**")
                sim_kp_cols = st.columns(4)

                # Base KPIs (recalculate quickly or retrieve from Tab 1 if stored more granularly)
                base_total_revenue = base_results_df[COL_REVENUE_EXPECTED].sum()
                base_total_profit = base_results_df[COL_PROFIT_EXPECTED].sum()
                base_overall_margin_pct = (base_total_profit / base_total_revenue * 100) if base_total_revenue else 0
                base_total_hours = base_results_df[COL_SERVICE_HOURS].sum()
                base_avg_revenue_per_hour = base_total_revenue / base_total_hours if base_total_hours else 0


                # Simulated KPIs
                sim_total_revenue = simulated_results_df[COL_REVENUE_EXPECTED].sum()
                sim_total_profit = simulated_results_df[COL_PROFIT_EXPECTED].sum()
                sim_overall_margin_pct = (sim_total_profit / sim_total_revenue * 100) if sim_total_revenue else 0
                sim_total_hours = simulated_results_df[COL_SERVICE_HOURS].sum()
                sim_avg_revenue_per_hour = sim_total_revenue / sim_total_hours if sim_total_hours else 0

                sim_kp_cols[0].metric("Total Revenue", f"{sim_total_revenue:,.0f} EGP", f"{sim_total_revenue-base_total_revenue:,.0f}")
                sim_kp_cols[1].metric("Total Profit", f"{sim_total_profit:,.0f} EGP", f"{sim_total_profit-base_total_profit:,.0f}")
                sim_kp_cols[2].metric("Overall Margin", f"{sim_overall_margin_pct:.1f}%", f"{sim_overall_margin_pct-base_overall_margin_pct:.1f}%")
                sim_kp_cols[3].metric("Avg Revenue/Hour", f"{sim_avg_revenue_per_hour:,.0f} EGP", f"{sim_avg_revenue_per_hour-base_avg_revenue_per_hour:,.0f}")


                # --- Compare Service Details (if one was modified) ---
                if selected_service_sim != "(None - Apply Global Changes Only)":
                     st.markdown(f"**Detailed Comparison for: {selected_service_sim}**")
                     sim_comp_cols = st.columns(4)
                     base_service_res = base_results_df[base_results_df[COL_NAME_EN] == selected_service_sim].iloc[0]
                     sim_service_res = simulated_results_df[simulated_results_df[COL_NAME_EN] == selected_service_sim].iloc[0]

                     sim_comp_cols[0].metric("Suggested Price/Case", f"{sim_service_res[COL_PRICE_PER_CASE]:,.0f}", f"{sim_service_res[COL_PRICE_PER_CASE]-base_service_res[COL_PRICE_PER_CASE]:,.0f}")
                     sim_comp_cols[1].metric("CM/Case", f"{sim_service_res[COL_CONTRIB_MARGIN]:,.0f}", f"{sim_service_res[COL_CONTRIB_MARGIN]-base_service_res[COL_CONTRIB_MARGIN]:,.0f}")
                     # Handle infinity for BEP delta
                     bep_delta = sim_service_res[COL_BREAK_EVEN] - base_service_res[COL_BREAK_EVEN] if np.isfinite(sim_service_res[COL_BREAK_EVEN]) and np.isfinite(base_service_res[COL_BREAK_EVEN]) else "N/A"
                     bep_delta_str = f"{bep_delta:.1f}" if isinstance(bep_delta, (int, float)) else bep_delta
                     sim_comp_cols[2].metric("BEP (Cases)", f"{sim_service_res[COL_BREAK_EVEN]:.1f}", bep_delta_str )
                     sim_comp_cols[3].metric("Expected Profit (Service)", f"{sim_service_res[COL_PROFIT_EXPECTED]:,.0f}", f"{sim_service_res[COL_PROFIT_EXPECTED]-base_service_res[COL_PROFIT_EXPECTED]:,.0f}")


                # --- Display Full Simulated Results Table ---
                st.markdown("**Full Simulated Pricing Details:**")
                # Reuse formatting logic from Tab 1 display
                sim_display_df_final = simulated_results_df[[ # Select and rename columns for display
                    COL_NAME_EN, COL_EXPECTED_CASES, COL_VAR_COST, COL_DURATION,
                    COL_ALLOC_FIXED_COST, COL_FIXED_COST_PER_CASE, COL_TOTAL_COST_PER_CASE,
                    COL_PRICE_PER_CASE, COL_CONTRIB_MARGIN, COL_CONTRIB_MARGIN_RATIO, COL_BREAK_EVEN
                ]].rename(columns={ # Rename columns
                     COL_NAME_EN: "Service", COL_EXPECTED_CASES: "Cases", COL_VAR_COST: "Var Cost", COL_DURATION: "Hrs",
                     COL_ALLOC_FIXED_COST: "Alloc FixCost", COL_FIXED_COST_PER_CASE: "FixCost/Case", COL_TOTAL_COST_PER_CASE: "TotalCost/Case",
                     COL_PRICE_PER_CASE: "Price/Case", COL_CONTRIB_MARGIN: "CM/Case", COL_CONTRIB_MARGIN_RATIO: "CM Ratio", COL_BREAK_EVEN: "BEP (Cases)"
                })
                st.dataframe(sim_display_df_final.style.format({ # Apply formatting
                    "Var Cost": "{:,.0f}", "Hrs": "{:.1f}", "Alloc FixCost": "{:,.0f}", "FixCost/Case": "{:,.0f}",
                    "TotalCost/Case": "{:,.0f}", "Price/Case": "{:,.0f}", "CM/Case": "{:,.0f}", "CM Ratio": "{:.1%}",
                    "BEP (Cases)": "{:.1f}" }).background_gradient(cmap='Blues', subset=['Price/Case', 'CM/Case']), use_container_width=True)


            else:
                st.error("Simulation failed. Please check the adjusted parameters.")
