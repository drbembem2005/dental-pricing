import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import copy

# --- Constants ---
# Column names (using constants prevents typos)
COL_NAME = "Service Name (Original)"
COL_NAME_EN = "Service Name (Display)"
COL_EXPECTED_CASES = "Exp. Cases/Month"
COL_VAR_COST = "Var. Cost/Case (EGP)"
COL_DURATION = "Duration (hr)"
COL_ALLOC_FIXED_COST = "Alloc. Fixed Cost (EGP)"
COL_FIXED_COST_PER_CASE = "Fixed Cost/Case (EGP)"
COL_TOTAL_COST_PER_CASE = "Total Cost/Case (EGP)"
COL_PRICE_PER_CASE = "Suggested Price/Case (EGP)"
COL_CONTRIB_MARGIN = "Contrib. Margin/Case (EGP)"
COL_CONTRIB_MARGIN_RATIO = "Contrib. Margin Ratio (%)"
COL_BREAK_EVEN = "Break-Even (Cases)"
COL_SERVICE_HOURS = "Total Service Hours"
COL_REVENUE_EXPECTED = "Exp. Revenue (EGP)"
COL_PROFIT_EXPECTED = "Exp. Profit (EGP)"
COL_CM_PER_HOUR = "Contrib. Margin/Hour (EGP)"
COL_REVENUE_PER_HOUR = "Revenue/Hour (EGP)"

# Session State Keys
STATE_SERVICES_DF_INPUT = "services_df_input" # DataFrame being edited by user
STATE_RESULTS_DF = "results_df"
STATE_CALCULATED_FIXED_COST = "calculated_fixed_cost"
STATE_CALCULATED_MARGIN = "calculated_margin"
STATE_CALCULATED = "calculated"
STATE_SIMULATION_RESULTS_DF = "simulation_results_df" # Store sim results separately


# --- Helper Functions ---

def initialize_session_state():
    """Initializes session state with defaults."""
    default_services_data = [
        {COL_NAME: "تنظيف الأسنان", COL_NAME_EN: "Dental Cleaning", COL_EXPECTED_CASES: 80, COL_VAR_COST: 150.0, COL_DURATION: 1.0},
        {COL_NAME: "حشو الأسنان", COL_NAME_EN: "Filling", COL_EXPECTED_CASES: 60, COL_VAR_COST: 250.0, COL_DURATION: 1.0},
        {COL_NAME: "علاج جذور الأسنان", COL_NAME_EN: "Root Canal Therapy", COL_EXPECTED_CASES: 40, COL_VAR_COST: 500.0, COL_DURATION: 2.0},
        {COL_NAME: "تقويم الأسنان", COL_NAME_EN: "Orthodontics Setup", COL_EXPECTED_CASES: 20, COL_VAR_COST: 1000.0, COL_DURATION: 2.0},
        {COL_NAME: "تبييض الأسنان", COL_NAME_EN: "Teeth Whitening", COL_EXPECTED_CASES: 50, COL_VAR_COST: 350.0, COL_DURATION: 1.0},
        {COL_NAME: "زراعة الأسنان", COL_NAME_EN: "Dental Implant", COL_EXPECTED_CASES: 10, COL_VAR_COST: 3000.0, COL_DURATION: 3.0}
    ]
    if STATE_SERVICES_DF_INPUT not in st.session_state:
        st.session_state[STATE_SERVICES_DF_INPUT] = pd.DataFrame(default_services_data)
        # Ensure types on load
        for col, dtype in {COL_EXPECTED_CASES: int, COL_VAR_COST: float, COL_DURATION: float}.items():
             try: st.session_state[STATE_SERVICES_DF_INPUT][col] = st.session_state[STATE_SERVICES_DF_INPUT][col].astype(dtype)
             except: pass # Ignore errors if column doesn't exist or type fails initially

    if STATE_RESULTS_DF not in st.session_state: st.session_state[STATE_RESULTS_DF] = None
    if STATE_CALCULATED_FIXED_COST not in st.session_state: st.session_state[STATE_CALCULATED_FIXED_COST] = 0.0
    if STATE_CALCULATED_MARGIN not in st.session_state: st.session_state[STATE_CALCULATED_MARGIN] = 0.30
    if STATE_CALCULATED not in st.session_state: st.session_state[STATE_CALCULATED] = False
    if STATE_SIMULATION_RESULTS_DF not in st.session_state: st.session_state[STATE_SIMULATION_RESULTS_DF] = None


def validate_service_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validates the service data DataFrame before calculation."""
    errors = []
    if df.empty:
        errors.append("Service data is empty. Please add at least one service.")
        return False, errors

    required_cols = [COL_NAME_EN, COL_EXPECTED_CASES, COL_VAR_COST, COL_DURATION]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")

    # Check for null/empty names
    if df[COL_NAME_EN].isnull().any() or (df[COL_NAME_EN] == '').any():
        errors.append("Service Name (Display) cannot be empty.")

    # Check for duplicate display names
    duplicates = df[df.duplicated(subset=[COL_NAME_EN], keep=False)][COL_NAME_EN].unique()
    if len(duplicates) > 0:
        errors.append(f"Duplicate Service Names (Display) found: {', '.join(duplicates)}. Names must be unique.")

    # Convert to numeric, coercing errors, then check
    for col in [COL_EXPECTED_CASES, COL_VAR_COST, COL_DURATION]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce') # Convert first

    if COL_EXPECTED_CASES in df.columns and df[COL_EXPECTED_CASES].isnull().any(): errors.append(f"'{COL_EXPECTED_CASES}' contains non-numeric values.")
    if COL_VAR_COST in df.columns and df[COL_VAR_COST].isnull().any(): errors.append(f"'{COL_VAR_COST}' contains non-numeric values.")
    if COL_DURATION in df.columns and df[COL_DURATION].isnull().any(): errors.append(f"'{COL_DURATION}' contains non-numeric values.")

    # Check for negative values AFTER potential coercion/filling
    if COL_EXPECTED_CASES in df.columns and (df[COL_EXPECTED_CASES].fillna(0) < 0).any(): errors.append(f"'{COL_EXPECTED_CASES}' cannot be negative.")
    if COL_VAR_COST in df.columns and (df[COL_VAR_COST].fillna(0) < 0).any(): errors.append(f"'{COL_VAR_COST}' cannot be negative.")
    if COL_DURATION in df.columns and (df[COL_DURATION].fillna(0.1) <= 0).any(): errors.append(f"'{COL_DURATION}' must be greater than zero.")

    return not errors, errors


def calculate_detailed_pricing(services_df_input: pd.DataFrame, total_fixed_cost: float, margin: float) -> Optional[pd.DataFrame]:
    """Calculates detailed pricing and related metrics AFTER validation."""
    # Assumes validation has already passed
    calc_df = services_df_input.copy()

    # Ensure correct dtypes for calculation after potential edits
    try:
        calc_df[COL_EXPECTED_CASES] = calc_df[COL_EXPECTED_CASES].astype(int)
        calc_df[COL_VAR_COST] = calc_df[COL_VAR_COST].astype(float)
        calc_df[COL_DURATION] = calc_df[COL_DURATION].astype(float)
    except Exception as e:
         st.error(f"Internal Error: Failed data type conversion during calculation: {e}")
         return None # Should not happen if validation is correct

    # --- Core Calculations ---
    calc_df[COL_SERVICE_HOURS] = calc_df[COL_EXPECTED_CASES] * calc_df[COL_DURATION]
    total_service_hours = calc_df[COL_SERVICE_HOURS].sum()

    if total_service_hours <= 0:
        # This case should ideally be caught by validation (duration > 0), but handle defensively
        calc_df[COL_ALLOC_FIXED_COST] = 0.0
        calc_df[COL_FIXED_COST_PER_CASE] = 0.0
    else:
        calc_df[COL_ALLOC_FIXED_COST] = total_fixed_cost * (calc_df[COL_SERVICE_HOURS] / total_service_hours)
        calc_df[COL_FIXED_COST_PER_CASE] = np.where(calc_df[COL_EXPECTED_CASES] > 0, calc_df[COL_ALLOC_FIXED_COST] / calc_df[COL_EXPECTED_CASES], 0)

    calc_df[COL_TOTAL_COST_PER_CASE] = calc_df[COL_VAR_COST] + calc_df[COL_FIXED_COST_PER_CASE]
    calc_df[COL_PRICE_PER_CASE] = calc_df[COL_TOTAL_COST_PER_CASE] * (1 + margin)
    calc_df[COL_CONTRIB_MARGIN] = calc_df[COL_PRICE_PER_CASE] - calc_df[COL_VAR_COST]

    # --- Additional Metrics ---
    calc_df[COL_CONTRIB_MARGIN_RATIO] = np.where(calc_df[COL_PRICE_PER_CASE] > 0, (calc_df[COL_CONTRIB_MARGIN] / calc_df[COL_PRICE_PER_CASE])*100, 0) # In %
    calc_df[COL_BREAK_EVEN] = np.where(calc_df[COL_CONTRIB_MARGIN] > 0, calc_df[COL_ALLOC_FIXED_COST] / calc_df[COL_CONTRIB_MARGIN], float('inf'))
    calc_df[COL_REVENUE_EXPECTED] = calc_df[COL_PRICE_PER_CASE] * calc_df[COL_EXPECTED_CASES]
    calc_df[COL_PROFIT_EXPECTED] = (calc_df[COL_CONTRIB_MARGIN] * calc_df[COL_EXPECTED_CASES]) - calc_df[COL_ALLOC_FIXED_COST]
    calc_df[COL_REVENUE_PER_HOUR] = np.where(calc_df[COL_DURATION] > 0, calc_df[COL_PRICE_PER_CASE] / calc_df[COL_DURATION], 0)
    calc_df[COL_CM_PER_HOUR] = np.where(calc_df[COL_DURATION] > 0, calc_df[COL_CONTRIB_MARGIN] / calc_df[COL_DURATION], 0)

    return calc_df


# --- Plotting Functions (with Tooltips/Explanations) ---
def plot_bar_chart(df, x_col, y_col, title, xlabel, ylabel, tooltip, sort_by_y=True, color='skyblue'):
    """Helper to create a formatted bar chart with explanation."""
    if df.empty: return None
    fig, ax = plt.subplots(figsize=(10, 6))
    data_to_plot = df.copy()
    if sort_by_y: data_to_plot = data_to_plot.sort_values(by=y_col, ascending=False)

    bars = ax.bar(data_to_plot[x_col], data_to_plot[y_col], color=color)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.tick_params(axis='x', rotation=45, labelsize=10, ha='right') # Adjust rotation alignment
    ax.tick_params(axis='y', labelsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.bar_label(bars, fmt='{:,.0f}', fontsize=9, padding=3)
    fig.text(0.5, -0.15, tooltip, ha='center', va='center', fontsize=10, style='italic', wrap=True, transform=ax.transAxes) # Add tooltip below chart
    fig.tight_layout(rect=[0, 0.05, 1, 1]) # Adjust layout to make space for tooltip
    return fig

def plot_pie_chart(sizes, labels, title, tooltip):
    """Helper to create a formatted pie chart with explanation."""
    if not sizes or not labels or len(sizes) != len(labels): return None
    fig, ax = plt.subplots(figsize=(8, 8))
    # Filter out zero sizes to avoid issues with explode/labels
    non_zero_data = [(s, l) for s, l in zip(sizes, labels) if s > 0]
    if not non_zero_data: return None # Nothing to plot
    sizes_nz, labels_nz = zip(*non_zero_data)

    explode = tuple([0.1 if s == max(sizes_nz) else 0 for s in sizes_nz])
    wedges, texts, autotexts = ax.pie(sizes_nz, labels=labels_nz, autopct='%1.1f%%', startangle=90,
                                      pctdistance=0.85, explode=explode, textprops={'fontsize': 10})
    plt.setp(autotexts, size=9, weight="bold", color="white")
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    # fig.text(0.5, 0.01, tooltip, ha='center', va='center', fontsize=10, style='italic', wrap=True) # Tooltip below
    # Add tooltip inside the plot area if space allows
    ax.text(0, -1.2, tooltip, ha='center', va='center', fontsize=10, style='italic', wrap=True)

    ax.axis('equal')
    # fig.tight_layout(rect=[0, 0.05, 1, 0.95]) # Adjust layout for tooltip
    return fig

# Sensitivity calculation and plot functions remain the same
# ... (calculate_sensitivity and plot_sensitivity function code - no changes needed) ...
def calculate_sensitivity(variable_cost: float, allocated_fixed_cost: float, margin: float, cases_range: range) -> Tuple[List[float], List[float]]:
    prices = []; break_evens = []
    for cases in cases_range:
        if cases <= 0: price, be = float('inf'), float('inf')
        else:
            fixed_cost_per_case = allocated_fixed_cost / cases
            total_cost = variable_cost + fixed_cost_per_case
            price = total_cost * (1 + margin)
            contribution_margin = price - variable_cost
            be = allocated_fixed_cost / contribution_margin if contribution_margin > 0 else float('inf')
        prices.append(price); break_evens.append(be)
    return prices, break_evens

def plot_sensitivity(cases_range: List[int], prices: List[float], break_evens: List[float]) -> plt.Figure:
    fig, axs = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    axs[0].plot(cases_range, prices, marker='o', linestyle='-', color='royalblue'); axs[0].set_title("Price Sensitivity vs. Number of Cases"); axs[0].set_xlabel("Number of Cases"); axs[0].set_ylabel("Calculated Price per Case (EGP)"); axs[0].grid(True, linestyle='--', alpha=0.6); axs[0].ticklabel_format(style='plain', axis='y')
    axs[1].plot(cases_range, break_evens, marker='x', linestyle='--', color='crimson'); axs[1].set_title("Break-Even Point vs. Number of Cases"); axs[1].set_xlabel("Number of Cases"); axs[1].set_ylabel("Calculated Break-Even Point (Cases)"); axs[1].grid(True, linestyle='--', alpha=0.6); finite_bes = [be for be in break_evens if be != float('inf')]; axs[1].set_ylim(bottom=0, top=max(finite_bes) * 1.15 if finite_bes else 10); axs[1].ticklabel_format(style='plain', axis='y')
    fig.suptitle("Sensitivity Analysis: Impact of Case Volume Changes", fontsize=14)
    # fig.tight_layout(rect=[0, 0, 1, 0.96]) # Adjust layout if suptitle overlaps
    return fig


# --- Streamlit App ---
st.set_page_config(layout="wide", page_title="Dental Pricing Dashboard V2")
initialize_session_state() # MUST be called before accessing session_state

# --- Sidebar ---
with st.sidebar:
    st.image("https://img.icons8.com/?size=100&id=p8J6hLVdN_V9&format=png&color=000000", width=64) # Tooth icon
    st.title("Clinic Settings")
    st.header("1. Monthly Fixed Costs")
    rent = st.number_input("Rent (EGP)", min_value=0.0, value=15000.0, step=500.0, key="rent_sb", help="Monthly rent cost for the clinic premises.")
    salaries = st.number_input("Staff Salaries (EGP)", min_value=0.0, value=20000.0, step=500.0, key="salaries_sb", help="Total monthly salaries for all staff (dentists, assistants, admin).")
    utilities = st.number_input("Utilities (EGP)", min_value=0.0, value=5000.0, step=200.0, key="utilities_sb", help="Monthly cost for electricity, water, internet, etc.")
    insurance = st.number_input("Insurance & Maintenance (EGP)", min_value=0.0, value=2000.0, step=100.0, key="insurance_sb", help="Monthly cost for liability/property insurance and equipment maintenance contracts.")
    marketing = st.number_input("Marketing (EGP)", min_value=0.0, value=1000.0, step=100.0, key="marketing_sb", help="Monthly expenses for advertising, website, social media, etc.")
    other_fixed = st.number_input("Other Fixed Costs (EGP)", min_value=0.0, value=0.0, step=100.0, key="other_fixed_sb", help="Any other recurring monthly costs not tied to procedure volume (e.g., software subscriptions, loan payments).")
    current_total_fixed_cost = rent + salaries + utilities + insurance + marketing + other_fixed
    st.metric(label="**Total Monthly Fixed Costs**", value=f"{current_total_fixed_cost:,.0f} EGP", help="Sum of all fixed costs entered above. This amount will be allocated across services based on time.")
    st.divider()

    st.header("2. Base Target Profit Margin")
    # Read default from state, but slider directly controls the current value
    current_margin_percentage = st.slider(
        "Base Profit Margin (%)", 0, 200,
        int(st.session_state.get(STATE_CALCULATED_MARGIN, 0.30) * 100), 5, # Default to last calculated or 30%
        key="margin_slider_sb",
        help="Desired profit as a percentage *markup* on the calculated Total Cost per Case (Variable + Allocated Fixed). E.g., 30% means Price = Total Cost * 1.30.")
    current_margin = current_margin_percentage / 100.0
    st.info(f"Base Target Margin: {current_margin_percentage}%", icon="🎯")

# --- Main Content Tabs ---
tab1, tab2 = st.tabs([
    "⚙️ Setup & Calculate",
    "📊 Analysis & Simulation"
])

# === TAB 1: Setup & Calculate ===
with tab1:
    st.header("Step 1: Setup Services & Costs")
    st.markdown("Define the services your clinic offers and review the fixed costs from the sidebar.")

    # Display Fixed Costs from Sidebar (read-only confirmation)
    st.subheader("Monthly Fixed Costs Summary")
    st.json({
        "Rent": f"{rent:,.0f}", "Salaries": f"{salaries:,.0f}", "Utilities": f"{utilities:,.0f}",
        "Insurance/Maint.": f"{insurance:,.0f}", "Marketing": f"{marketing:,.0f}", "Other": f"{other_fixed:,.0f}",
        "**TOTAL**": f"**{current_total_fixed_cost:,.0f} EGP**"
    }, expanded=False) # Show collapsed by default
    st.caption("Total Fixed Costs are allocated based on service duration.")
    st.divider()

    # --- Service Management using data_editor ---
    st.subheader("Manage Services List")
    st.markdown("""
    Use the table below to add, edit, or remove services.
    - **Double-click a cell to edit.**
    - **Click '+' at the bottom to add a new row.** Fill in required fields (*).
    - **Select rows and press `Delete` key to remove.**
    - Ensure 'Service Name (Display)' is unique for each service.
    - `Duration (hr)` is critical for fixed cost allocation.
    """)

    # Configure columns for the editor with tooltips
    column_config_editor = {
        COL_NAME: st.column_config.TextColumn("Service Name (Original)", help="Optional: Name in original language or internal code."),
        COL_NAME_EN: st.column_config.TextColumn("Service Name (Display)*", required=True, help="Unique name used for display and analysis (e.g., English). **Required**."),
        COL_EXPECTED_CASES: st.column_config.NumberColumn("Exp. Cases/Month*", required=True, min_value=0, format="%d", help="Estimated number of times this service is performed per month. **Required**."),
        COL_VAR_COST: st.column_config.NumberColumn("Var. Cost/Case (EGP)*", required=True, min_value=0.0, format="%.2f", help="Direct cost per procedure (materials, lab fees). **Required**."),
        COL_DURATION: st.column_config.NumberColumn("Duration (hr)*", required=True, min_value=0.1, format="%.2f", help="Average chair time in hours needed for the procedure (e.g., 1.5). **Required & > 0**.")
    }

    # The data_editor directly modifies the DataFrame in session state
    edited_df = st.data_editor(
        st.session_state[STATE_SERVICES_DF_INPUT],
        num_rows="dynamic", # Allow adding/deleting rows
        column_config=column_config_editor,
        use_container_width=True,
        key="service_editor", # Assign a key
        hide_index=True
    )

    # Store the potentially edited DataFrame back into session state immediately
    # This makes the state reflect the UI before validation/calculation
    st.session_state[STATE_SERVICES_DF_INPUT] = edited_df

    # --- Validation Feedback ---
    is_valid, errors = validate_service_data(edited_df)
    if not is_valid:
        for error in errors:
            st.warning(f"Input Validation Error: {error}", icon="⚠️")
    else:
        st.success("Service data looks valid.", icon="✅")

    st.divider()

    # --- Calculation Trigger ---
    st.header("Step 2: Calculate Pricing")
    st.markdown("Click below to calculate prices, costs, and KPIs based on the current setup.")

    # Disable button if data is invalid
    calculate_button = st.button("💰 Calculate Detailed Pricing & KPIs", type="primary", use_container_width=True, disabled=not is_valid)

    if calculate_button:
        if not is_valid:
            st.error("Cannot calculate. Please fix the validation errors listed above.")
        else:
            # Perform calculation using the validated data from the editor
            results = calculate_detailed_pricing(
                edited_df, # Use the data currently in the editor
                current_total_fixed_cost,
                current_margin
            )
            if results is not None:
                # Store results and parameters used
                st.session_state[STATE_RESULTS_DF] = results
                st.session_state[STATE_CALCULATED_FIXED_COST] = current_total_fixed_cost
                st.session_state[STATE_CALCULATED_MARGIN] = current_margin
                st.session_state[STATE_CALCULATED] = True
                st.session_state[STATE_SIMULATION_RESULTS_DF] = None # Reset simulation results
                st.success("Pricing calculated successfully! View results below and in the Analysis tab.")
                # st.balloons()
            else:
                 st.session_state[STATE_CALCULATED] = False
                 st.error("Calculation failed. Check data and logs if possible.")


    # --- Display Results & KPIs (if calculated) ---
    st.divider()
    st.header("Step 3: Review Base Results")
    if st.session_state[STATE_CALCULATED] and st.session_state[STATE_RESULTS_DF] is not None:
        results_df = st.session_state[STATE_RESULTS_DF]

        # --- Display KPIs ---
        st.subheader("📊 Key Performance Indicators (Base Calculation)")
        # ... (KPI calculation logic - identical to previous version) ...
        total_revenue = results_df[COL_REVENUE_EXPECTED].sum()
        total_profit = results_df[COL_PROFIT_EXPECTED].sum()
        total_var_cost = (results_df[COL_VAR_COST] * results_df[COL_EXPECTED_CASES]).sum()
        total_fixed_cost_used = st.session_state[STATE_CALCULATED_FIXED_COST]
        total_cost = total_var_cost + total_fixed_cost_used
        overall_margin_pct = (total_profit / total_revenue * 100) if total_revenue else 0
        # Weighted Average CM Ratio
        total_cm = (results_df[COL_CONTRIB_MARGIN] * results_df[COL_EXPECTED_CASES]).sum()
        weighted_avg_cm_ratio = (total_cm / total_revenue) if total_revenue else 0
        total_break_even_revenue = (total_fixed_cost_used / weighted_avg_cm_ratio) if weighted_avg_cm_ratio > 0 else float('inf')
        total_hours = results_df[COL_SERVICE_HOURS].sum()
        avg_revenue_per_hour = total_revenue / total_hours if total_hours else 0
        avg_cm_per_hour = total_cm / total_hours if total_hours else 0 # Use total CM for avg calc


        kp_cols = st.columns(4)
        kp_cols[0].metric("Total Projected Revenue", f"{total_revenue:,.0f} EGP", help="Sum of (Price/Case * Exp. Cases) for all services.")
        kp_cols[1].metric("Total Projected Profit", f"{total_profit:,.0f} EGP", help="Total Revenue - Total Variable Costs - Total Fixed Costs.")
        kp_cols[2].metric("Overall Profit Margin", f"{overall_margin_pct:.1f}%", help="(Total Profit / Total Revenue) * 100.")
        be_revenue_text = f"{total_break_even_revenue:,.0f} EGP" if np.isfinite(total_break_even_revenue) else "N/A (Loss)"
        kp_cols[3].metric("Overall Break-Even Revenue", be_revenue_text, help="Total revenue needed to cover all fixed and variable costs (Total Fixed Costs / Weighted Avg CM Ratio). 'N/A' if overall CM is zero or negative.")

        kp_cols2 = st.columns(4)
        kp_cols2[0].metric("Avg. Revenue per Hour", f"{avg_revenue_per_hour:,.0f} EGP", help="Total Revenue / Total Service Hours.")
        kp_cols2[1].metric("Avg. Contribution Margin / Hour", f"{avg_cm_per_hour:,.0f} EGP", help="Total Contribution Margin / Total Service Hours. Shows profit generation relative to time before fixed costs.")
        kp_cols2[2].metric("Total Hours Projected", f"{total_hours:,.1f} hrs", help="Sum of (Exp. Cases * Duration) for all services.")
        kp_cols2[3].metric("Number of Services Priced", f"{len(results_df)}")

        # --- Display Detailed Results Table ---
        st.subheader("📋 Detailed Pricing per Service (Base Calculation)")
        # Define tooltips for the results table columns
        results_tooltips = {
            COL_NAME_EN: "Display name of the service.",
            COL_EXPECTED_CASES: "Expected number of cases per month.",
            COL_VAR_COST: "Direct variable cost per case.",
            COL_DURATION: "Average duration per case in hours.",
            COL_ALLOC_FIXED_COST: "Portion of total fixed costs allocated to this service based on its share of total service hours.",
            COL_FIXED_COST_PER_CASE: "Allocated Fixed Cost / Expected Cases.",
            COL_TOTAL_COST_PER_CASE: "Variable Cost/Case + Fixed Cost/Case.",
            COL_PRICE_PER_CASE: "Calculated Price = Total Cost/Case * (1 + Base Profit Margin %).",
            COL_CONTRIB_MARGIN: "Contribution Margin per Case = Price/Case - Variable Cost/Case. Amount available to cover fixed costs and generate profit.",
            COL_CONTRIB_MARGIN_RATIO: "Contribution Margin / Price per Case * 100. Profitability percentage before fixed costs.",
            COL_BREAK_EVEN: "Break-Even Point (Cases) = Allocated Fixed Cost / Contribution Margin per Case. Cases needed for *this service* to cover *its allocated* fixed costs."
        }
        # Rename for display and apply formatting/tooltips within dataframe call if possible (or use markdown table)
        display_df_final = results_df.copy()
        # Format and display
        st.dataframe(display_df_final[[ # Select columns in desired order
            COL_NAME_EN, COL_EXPECTED_CASES, COL_VAR_COST, COL_DURATION,
            COL_ALLOC_FIXED_COST, COL_FIXED_COST_PER_CASE, COL_TOTAL_COST_PER_CASE,
            COL_PRICE_PER_CASE, COL_CONTRIB_MARGIN, COL_CONTRIB_MARGIN_RATIO, COL_BREAK_EVEN
        ]].style.format({
            COL_EXPECTED_CASES: "{:,.0f}", COL_VAR_COST: "{:,.0f}", COL_DURATION: "{:.1f}",
            COL_ALLOC_FIXED_COST: "{:,.0f}", COL_FIXED_COST_PER_CASE: "{:,.0f}",
            COL_TOTAL_COST_PER_CASE: "{:,.0f}", COL_PRICE_PER_CASE: "{:,.0f}",
            COL_CONTRIB_MARGIN: "{:,.0f}", COL_CONTRIB_MARGIN_RATIO: "{:.1f}%",
            COL_BREAK_EVEN: "{:.1f}"
        }).set_tooltips(pd.DataFrame([results_tooltips]), # Pass tooltips as a DataFrame
                      props='visibility: hidden; position: absolute; background-color: #f9f9f9; border: 1px solid #ccc; padding: 5px; z-index: 1;' # Basic CSS for tooltip styling
                     ).background_gradient(cmap='Greens', subset=[COL_CONTRIB_MARGIN, COL_CONTRIB_MARGIN_RATIO]),
         use_container_width=True)


    elif not st.session_state[STATE_CALCULATED]:
        st.info("Click 'Calculate Detailed Pricing & KPIs' after setting up services to view results here.", icon="👆")


# === TAB 2: Analysis & Simulation ===
with tab2:
    st.header("Analysis & Simulation")

    if not st.session_state[STATE_CALCULATED] or st.session_state[STATE_RESULTS_DF] is None:
        st.warning("Please calculate pricing on the 'Setup & Calculate' tab first to enable analysis and simulation.", icon="⚠️")
    else:
        base_results_df = st.session_state[STATE_RESULTS_DF]
        base_fixed_cost = st.session_state[STATE_CALCULATED_FIXED_COST]
        base_margin = st.session_state[STATE_CALCULATED_MARGIN]
        # Use the input DF that *led* to the results for simulation base
        base_services_df_input = st.session_state[STATE_SERVICES_DF_INPUT]


        analysis_tab1, analysis_tab2, analysis_tab3 = st.tabs(["📈 Visual Analysis", "💡 Scenario Simulation", "📉 Sensitivity Analysis"])

        # --- Visual Analysis Sub-Tab ---
        with analysis_tab1:
            st.subheader("Profitability Visuals")
            profit_tooltip = "Compares the estimated total monthly profit generated by each service (Revenue - Variable Costs - Allocated Fixed Costs)."
            profit_fig = plot_bar_chart(base_results_df, COL_NAME_EN, COL_PROFIT_EXPECTED,
                                        "Total Expected Profit by Service", "Service", "Expected Profit (EGP)", profit_tooltip, color='mediumseagreen')
            if profit_fig: st.pyplot(profit_fig)
            else: st.caption("No data to plot.")

            cm_tooltip = "Compares the Contribution Margin per Case (Price - Variable Cost) for each service. Higher values contribute more towards covering fixed costs and generating profit per procedure."
            cm_fig = plot_bar_chart(base_results_df, COL_NAME_EN, COL_CONTRIB_MARGIN,
                                    "Contribution Margin per Case by Service", "Service", "Contribution Margin (EGP)", cm_tooltip, color='lightcoral')
            if cm_fig: st.pyplot(cm_fig)
            else: st.caption("No data to plot.")

            st.subheader("Time & Efficiency Visuals")
            time_tooltip = "Shows the total estimated chair time (hours) required per month for each service based on expected cases and duration per case."
            time_fig = plot_bar_chart(base_results_df, COL_NAME_EN, COL_SERVICE_HOURS,
                                      "Total Expected Chair Time by Service", "Service", "Total Hours", time_tooltip, color='lightblue')
            if time_fig: st.pyplot(time_fig)
            else: st.caption("No data to plot.")

            cm_hr_tooltip = "Compares the Contribution Margin generated per hour of chair time (CM per Case / Duration per Case). Services with high CM/hour are very efficient profit generators."
            cm_hr_fig = plot_bar_chart(base_results_df, COL_NAME_EN, COL_CM_PER_HOUR,
                                       "Contribution Margin per Hour by Service", "Service", "CM per Hour (EGP)", cm_hr_tooltip, color='lightgreen')
            if cm_hr_fig: st.pyplot(cm_hr_fig)
            else: st.caption("No data to plot.")


        # --- Scenario Simulation Sub-Tab ---
        with analysis_tab2:
            st.subheader("Scenario Simulation ('What-If')")
            st.markdown("Adjust parameters below to simulate changes based on the **last calculated results**. This does **not** change your saved setup.")

            # --- Simulation Inputs ---
            with st.form("simulation_form"):
                st.markdown("**Global Adjustments:**")
                sim_cols = st.columns(2)
                sim_fixed_cost = sim_cols[0].number_input("Simulated Total Fixed Costs (EGP)", value=float(base_fixed_cost), step=1000.0, help=f"Adjust total fixed costs. Base was {base_fixed_cost:,.0f}.")
                sim_margin_pct = sim_cols[1].slider("Simulated Profit Margin (%)", 0, 200, int(base_margin * 100), 5, help=f"Adjust overall profit margin. Base was {base_margin*100:.0f}%.")
                sim_margin = sim_margin_pct / 100.0

                st.markdown("**Specific Service Adjustment (Optional):**")
                service_options = ["(None)"] + base_results_df[COL_NAME_EN].tolist()
                # Use unique key for selectbox inside form
                selected_service_sim = st.selectbox("Select Service to Modify:", options=service_options, key="sim_service_select_in_form", index=0)

                sim_var_cost_override = None
                sim_cases_override = None
                sim_duration_override = None
                modified_service_idx = None # Use index from the INPUT df

                if selected_service_sim != "(None)":
                    # Find the corresponding row in the *input* DataFrame
                    service_input_row = base_services_df_input[base_services_df_input[COL_NAME_EN] == selected_service_sim]
                    if not service_input_row.empty:
                        modified_service_idx = service_input_row.index[0]
                        sim_spec_cols = st.columns(3)
                        sim_var_cost_override = sim_spec_cols[0].number_input(f"Sim Var Cost", value=float(service_input_row[COL_VAR_COST].iloc[0]), format="%.2f", key="sim_vc", min_value=0.0)
                        sim_cases_override = sim_spec_cols[1].number_input(f"Sim Exp Cases", value=int(service_input_row[COL_EXPECTED_CASES].iloc[0]), key="sim_ec", min_value=0)
                        sim_duration_override = sim_spec_cols[2].number_input(f"Sim Duration", value=float(service_input_row[COL_DURATION].iloc[0]), format="%.2f", key="sim_dur", min_value=0.1)
                    else:
                        st.warning("Selected service not found in original input data for simulation.")


                submitted_sim = st.form_submit_button("🚀 Run Simulation", type="primary")

            # --- Simulation Results ---
            if submitted_sim:
                # Prepare the input DataFrame for simulation
                sim_services_df = base_services_df_input.copy()
                if modified_service_idx is not None and selected_service_sim != "(None)":
                    # Apply overrides safely using .loc
                    if sim_var_cost_override is not None: sim_services_df.loc[modified_service_idx, COL_VAR_COST] = sim_var_cost_override
                    if sim_cases_override is not None: sim_services_df.loc[modified_service_idx, COL_EXPECTED_CASES] = sim_cases_override
                    if sim_duration_override is not None: sim_services_df.loc[modified_service_idx, COL_DURATION] = sim_duration_override

                # Validate the simulated input data
                sim_is_valid, sim_errors = validate_service_data(sim_services_df)
                if not sim_is_valid:
                    st.error("Simulation Input Data Invalid:")
                    for err in sim_errors: st.error(f"- {err}")
                else:
                    # Run calculation with simulated inputs
                    simulated_results = calculate_detailed_pricing(sim_services_df, sim_fixed_cost, sim_margin)

                    if simulated_results is not None:
                        st.session_state[STATE_SIMULATION_RESULTS_DF] = simulated_results # Store results
                        st.success("Simulation complete!")
                    else:
                        st.error("Simulation calculation failed.")
                        st.session_state[STATE_SIMULATION_RESULTS_DF] = None

            # Display simulation results if they exist in state
            if st.session_state[STATE_SIMULATION_RESULTS_DF] is not None:
                 sim_results_df = st.session_state[STATE_SIMULATION_RESULTS_DF]
                 st.divider()
                 st.subheader("Simulation Results vs. Base Calculation")
                 # ... (KPI Comparison Logic - identical to previous version) ...
                 # Calculate Base KPIs again for comparison
                 base_total_revenue = base_results_df[COL_REVENUE_EXPECTED].sum()
                 base_total_profit = base_results_df[COL_PROFIT_EXPECTED].sum()
                 base_overall_margin_pct = (base_total_profit / base_total_revenue * 100) if base_total_revenue else 0
                 base_total_hours = base_results_df[COL_SERVICE_HOURS].sum()
                 base_avg_revenue_per_hour = base_total_revenue / base_total_hours if base_total_hours else 0

                 # Calculate Simulated KPIs
                 sim_total_revenue = sim_results_df[COL_REVENUE_EXPECTED].sum()
                 sim_total_profit = sim_results_df[COL_PROFIT_EXPECTED].sum()
                 sim_overall_margin_pct = (sim_total_profit / sim_total_revenue * 100) if sim_total_revenue else 0
                 sim_total_hours = sim_results_df[COL_SERVICE_HOURS].sum()
                 sim_avg_revenue_per_hour = sim_total_revenue / sim_total_hours if sim_total_hours else 0

                 st.markdown("**Overall KPI Comparison:**")
                 sim_kp_cols = st.columns(4)
                 sim_kp_cols[0].metric("Total Revenue", f"{sim_total_revenue:,.0f} EGP", f"{sim_total_revenue-base_total_revenue:,.0f}")
                 sim_kp_cols[1].metric("Total Profit", f"{sim_total_profit:,.0f} EGP", f"{sim_total_profit-base_total_profit:,.0f}")
                 sim_kp_cols[2].metric("Overall Margin", f"{sim_overall_margin_pct:.1f}%", f"{sim_overall_margin_pct-base_overall_margin_pct:.1f}% pts")
                 sim_kp_cols[3].metric("Avg Rev/Hour", f"{sim_avg_revenue_per_hour:,.0f} EGP", f"{sim_avg_revenue_per_hour-base_avg_revenue_per_hour:,.0f}")

                 # ... (Service Detail Comparison if applicable - identical to previous version) ...
                 if selected_service_sim != "(None)":
                     # Ensure service still exists in results (it should if validation passed)
                     if selected_service_sim in base_results_df[COL_NAME_EN].values and selected_service_sim in sim_results_df[COL_NAME_EN].values:
                         st.markdown(f"**Detailed Comparison for: {selected_service_sim}**")
                         sim_comp_cols = st.columns(4)
                         base_service_res = base_results_df[base_results_df[COL_NAME_EN] == selected_service_sim].iloc[0]
                         sim_service_res = sim_results_df[sim_results_df[COL_NAME_EN] == selected_service_sim].iloc[0]
                         # Compare Price, CM, BEP, Profit
                         sim_comp_cols[0].metric("Price/Case", f"{sim_service_res[COL_PRICE_PER_CASE]:,.0f}", f"{sim_service_res[COL_PRICE_PER_CASE]-base_service_res[COL_PRICE_PER_CASE]:,.0f}")
                         sim_comp_cols[1].metric("CM/Case", f"{sim_service_res[COL_CONTRIB_MARGIN]:,.0f}", f"{sim_service_res[COL_CONTRIB_MARGIN]-base_service_res[COL_CONTRIB_MARGIN]:,.0f}")
                         bep_delta = sim_service_res[COL_BREAK_EVEN] - base_service_res[COL_BREAK_EVEN] if np.isfinite(sim_service_res[COL_BREAK_EVEN]) and np.isfinite(base_service_res[COL_BREAK_EVEN]) else "N/A"
                         bep_delta_str = f"{bep_delta:.1f}" if isinstance(bep_delta, (int, float)) else bep_delta
                         sim_comp_cols[2].metric("BEP (Cases)", f"{sim_service_res[COL_BREAK_EVEN]:.1f}", bep_delta_str )
                         sim_comp_cols[3].metric("Exp. Profit (Service)", f"{sim_service_res[COL_PROFIT_EXPECTED]:,.0f}", f"{sim_service_res[COL_PROFIT_EXPECTED]-base_service_res[COL_PROFIT_EXPECTED]:,.0f}")


                 # --- Display Full Simulated Results Table ---
                 st.markdown("**Full Simulated Pricing Details:**")
                 # ... (DataFrame formatting - identical to previous version) ...
                 st.dataframe(sim_results_df[[ # Select/Rename/Format
                     COL_NAME_EN, COL_EXPECTED_CASES, COL_VAR_COST, COL_DURATION, COL_ALLOC_FIXED_COST,
                     COL_FIXED_COST_PER_CASE, COL_TOTAL_COST_PER_CASE, COL_PRICE_PER_CASE, COL_CONTRIB_MARGIN,
                     COL_CONTRIB_MARGIN_RATIO, COL_BREAK_EVEN
                 ]].rename(columns={ # Rename cols
                     COL_NAME_EN:"Service", COL_EXPECTED_CASES:"Cases", COL_VAR_COST:"Var Cost", COL_DURATION:"Hrs",
                     COL_ALLOC_FIXED_COST:"Alloc FixCost", COL_FIXED_COST_PER_CASE:"FixCost/Case", COL_TOTAL_COST_PER_CASE:"TotalCost/Case",
                     COL_PRICE_PER_CASE:"Price/Case", COL_CONTRIB_MARGIN:"CM/Case", COL_CONTRIB_MARGIN_RATIO:"CM Ratio %",
                     COL_BREAK_EVEN:"BEP (Cases)"
                 }).style.format({ # Format cols
                     "Cases":"{:,.0f}", "Var Cost":"{:,.0f}", "Hrs":"{:.1f}", "Alloc FixCost":"{:,.0f}",
                     "FixCost/Case":"{:,.0f}", "TotalCost/Case":"{:,.0f}", "Price/Case":"{:,.0f}", "CM/Case":"{:,.0f}",
                     "CM Ratio %":"{:.1f}%", "BEP (Cases)":"{:.1f}"
                 }).set_tooltips(pd.DataFrame([results_tooltips])), # Use same tooltips
                 use_container_width=True)


        # --- Sensitivity Analysis Sub-Tab ---
        with analysis_tab3:
            st.subheader("Sensitivity Analysis (Case Volume Impact)")
            st.markdown("Analyze how **Price** and **Break-Even Point** change for one service if its case volume varies, using the **base calculated** allocation and margin.")

            service_names_options_sens = base_results_df[COL_NAME_EN].tolist()
            if not service_names_options_sens:
                 st.info("No services available in base results to analyze.")
            else:
                selected_service_sens = st.selectbox("Select Service for Sensitivity Analysis:", options=service_names_options_sens, key="sens_select")

                if selected_service_sens:
                     service_data_sens = base_results_df[base_results_df[COL_NAME_EN] == selected_service_sens].iloc[0]
                     st.markdown(f"Analyzing: **{selected_service_sens}**")
                     expected_cases_display = int(service_data_sens[COL_EXPECTED_CASES])

                     sens_cols = st.columns(3)
                     min_cases = sens_cols[0].number_input("Min Cases", 1, value=max(1, int(expected_cases_display * 0.2)), step=1, key="sens_min", help="Lowest number of cases to test.")
                     max_cases = sens_cols[1].number_input("Max Cases", int(min_cases)+1, value=int(expected_cases_display * 2.0), step=5, key="sens_max", help="Highest number of cases to test.")
                     step_cases = sens_cols[2].number_input("Step", 1, value=max(1, int((max_cases - min_cases)/10) if (max_cases - min_cases)>0 else 1), step=1, key="sens_step", help="Increment between min and max cases.")

                     if max_cases <= min_cases: st.error("Max Cases must be > Min Cases.")
                     else:
                         cases_range_list = list(range(int(min_cases), int(max_cases) + 1, int(step_cases)))
                         if not cases_range_list: st.warning("Invalid range/step.")
                         else:
                             prices, break_evens = calculate_sensitivity(
                                 variable_cost=service_data_sens[COL_VAR_COST],
                                 allocated_fixed_cost=service_data_sens[COL_ALLOC_FIXED_COST], # Use base allocated cost
                                 margin=base_margin, # Use base margin
                                 cases_range=cases_range_list
                             )
                             sensitivity_fig = plot_sensitivity(cases_range_list, prices, break_evens)
                             st.pyplot(sensitivity_fig)
