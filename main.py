import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
import copy

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
STATE_SERVICES_DF = "services_df" # <-- Store services as a DataFrame
STATE_EDIT_TARGET_INDEX = "edit_target_index" # <-- Store index of row being edited
STATE_RESULTS_DF = "results_df"
STATE_TOTAL_FIXED_COST = "total_fixed_cost"
STATE_MARGIN = "margin"
STATE_CALCULATED = "calculated"

# --- Helper Functions ---

def initialize_session_state():
    """Initializes required keys in Streamlit's session state."""
    # Default data
    default_services_data = [
        {"name": "تنظيف الأسنان", "expected_cases": 80, "variable_cost": 150.0, "duration_hours": 1.0},
        {"name": "حشو الأسنان", "expected_cases": 60, "variable_cost": 250.0, "duration_hours": 1.0},
        {"name": "علاج جذور الأسنان", "expected_cases": 40, "variable_cost": 500.0, "duration_hours": 2.0},
        {"name": "تقويم الأسنان", "expected_cases": 20, "variable_cost": 1000.0, "duration_hours": 2.0},
        {"name": "تبييض الأسنان", "expected_cases": 50, "variable_cost": 350.0, "duration_hours": 1.0},
        {"name": "زراعة الأسنان", "expected_cases": 10, "variable_cost": 3000.0, "duration_hours": 3.0}
    ]
    if STATE_SERVICES_DF not in st.session_state:
        # Store as a DataFrame
        st.session_state[STATE_SERVICES_DF] = pd.DataFrame(default_services_data)

    if STATE_EDIT_TARGET_INDEX not in st.session_state:
        st.session_state[STATE_EDIT_TARGET_INDEX] = None # No row selected for edit initially

    if STATE_RESULTS_DF not in st.session_state:
        st.session_state[STATE_RESULTS_DF] = None
    if STATE_TOTAL_FIXED_COST not in st.session_state:
        st.session_state[STATE_TOTAL_FIXED_COST] = 0.0
    if STATE_MARGIN not in st.session_state:
        st.session_state[STATE_MARGIN] = 0.30
    if STATE_CALCULATED not in st.session_state:
        st.session_state[STATE_CALCULATED] = False

# --- Calculation functions remain largely the same, but accept DataFrame ---
def calculate_detailed_pricing(
    services_df: pd.DataFrame, # <-- Accepts DataFrame directly
    total_fixed_cost: float,
    margin: float
) -> Optional[pd.DataFrame]:
    """
    Calculates detailed pricing, cost allocation, and break-even points for services.
    """
    if services_df.empty:
        st.error("لا توجد بيانات خدمات لإجراء الحسابات. يرجى إضافة خدمة واحدة على الأقل.")
        return None

    # Create a working copy to avoid modifying the original session state DataFrame directly
    calc_df = services_df.copy()

    # Data type conversion and validation
    try:
        # Use pd.to_numeric for robust conversion, fill errors with 0 or NaN then handle
        calc_df[COL_EXPECTED_CASES] = pd.to_numeric(calc_df[COL_EXPECTED_CASES], errors='coerce').fillna(0).astype(int)
        calc_df[COL_VAR_COST] = pd.to_numeric(calc_df[COL_VAR_COST], errors='coerce').fillna(0.0).astype(float)
        calc_df[COL_DURATION] = pd.to_numeric(calc_df[COL_DURATION], errors='coerce').fillna(0.0).astype(float)

        # Check for invalid values after conversion
        if (calc_df[COL_EXPECTED_CASES] < 0).any() or \
           (calc_df[COL_VAR_COST] < 0).any() or \
           (calc_df[COL_DURATION] <= 0).any():
             st.error("يرجى التأكد من أن عدد الحالات والتكلفة المتغيرة ليست سالبة، وأن مدة الخدمة أكبر من صفر في جميع الصفوف.")
             return None
    except Exception as e:
        st.error(f"خطأ في تحويل أنواع بيانات الخدمات: {e}. يرجى التحقق من الإدخالات.")
        return None

    # --- Calculations ---
    calc_df[COL_SERVICE_HOURS] = calc_df[COL_EXPECTED_CASES] * calc_df[COL_DURATION]
    total_service_hours = calc_df[COL_SERVICE_HOURS].sum()

    if total_service_hours <= 0:
        st.warning("إجمالي ساعات الخدمة (الوزن) هو صفر أو أقل. لا يمكن توزيع التكاليف الثابتة بشكل فعال.")
        calc_df[COL_ALLOC_FIXED_COST] = 0.0
        calc_df[COL_FIXED_COST_PER_CASE] = 0.0
    else:
        calc_df[COL_ALLOC_FIXED_COST] = total_fixed_cost * (calc_df[COL_SERVICE_HOURS] / total_service_hours)
        # Use .loc for safer assignment and division by zero handling
        calc_df[COL_FIXED_COST_PER_CASE] = calc_df.apply(
             lambda row: row[COL_ALLOC_FIXED_COST] / row[COL_EXPECTED_CASES] if row[COL_EXPECTED_CASES] > 0 else 0,
             axis=1
         )
        # Alternative using numpy.where for potential speedup on large DFs
        # calc_df[COL_FIXED_COST_PER_CASE] = np.where(
        #     calc_df[COL_EXPECTED_CASES] > 0,
        #     calc_df[COL_ALLOC_FIXED_COST] / calc_df[COL_EXPECTED_CASES],
        #     0
        # )


    calc_df[COL_TOTAL_COST_PER_CASE] = calc_df[COL_VAR_COST] + calc_df[COL_FIXED_COST_PER_CASE]
    calc_df[COL_PRICE_PER_CASE] = calc_df[COL_TOTAL_COST_PER_CASE] * (1 + margin)
    calc_df[COL_CONTRIB_MARGIN] = calc_df[COL_PRICE_PER_CASE] - calc_df[COL_VAR_COST]

    # Use .loc for safer assignment and division by zero handling for BE
    calc_df[COL_BREAK_EVEN] = calc_df.apply(
         lambda row: row[COL_ALLOC_FIXED_COST] / row[COL_CONTRIB_MARGIN] if row[COL_CONTRIB_MARGIN] > 0 else float('inf'),
         axis=1
     )
    # Alternative using numpy.where
    # calc_df[COL_BREAK_EVEN] = np.where(
    #     calc_df[COL_CONTRIB_MARGIN] > 0,
    #     calc_df[COL_ALLOC_FIXED_COST] / calc_df[COL_CONTRIB_MARGIN],
    #     float('inf')
    # )

    return calc_df

# Sensitivity calculation function remains the same
def calculate_sensitivity(
    variable_cost: float, allocated_fixed_cost: float, margin: float, cases_range: range
) -> Tuple[List[float], List[float]]:
    # ... (implementation is identical to previous versions) ...
    prices = []
    break_evens = []
    for cases in cases_range:
        if cases <= 0:
            price = float('inf')
            be = float('inf')
        else:
            fixed_cost_per_case = allocated_fixed_cost / cases
            total_cost = variable_cost + fixed_cost_per_case
            price = total_cost * (1 + margin)
            contribution_margin = price - variable_cost
            if contribution_margin <= 0:
                be = float('inf')
            else:
                be = allocated_fixed_cost / contribution_margin
        prices.append(price)
        break_evens.append(be)
    return prices, break_evens


# Plotting function with English labels remains the same
def plot_sensitivity(cases_range: List[int], prices: List[float], break_evens: List[float]) -> plt.Figure:
    # ... (implementation is identical to previous versions with English labels) ...
    fig, axs = plt.subplots(1, 2, figsize=(12, 5))

    # Plot Price Sensitivity
    axs[0].plot(cases_range, prices, marker='o', linestyle='-', color='royalblue')
    axs[0].set_title("Price Sensitivity vs. Number of Cases") # English
    axs[0].set_xlabel("Number of Cases") # English
    axs[0].set_ylabel("Calculated Price per Case (EGP)") # English
    axs[0].grid(True, linestyle='--', alpha=0.6)
    axs[0].ticklabel_format(style='plain', axis='y')

    # Plot Break-even Sensitivity
    axs[1].plot(cases_range, break_evens, marker='x', linestyle='--', color='crimson')
    axs[1].set_title("Break-Even Point vs. Number of Cases") # English
    axs[1].set_xlabel("Number of Cases") # English
    axs[1].set_ylabel("Calculated Break-Even Point (Cases)") # English
    axs[1].grid(True, linestyle='--', alpha=0.6)
    finite_bes = [be for be in break_evens if be != float('inf')]
    if finite_bes:
        axs[1].set_ylim(bottom=0, top=max(finite_bes) * 1.1 if finite_bes else 10)
    else:
        axs[1].set_ylim(bottom=0)
    axs[1].ticklabel_format(style='plain', axis='y')

    fig.tight_layout(pad=3.0)
    return fig


# --- Streamlit App Layout ---

st.set_page_config(layout="wide")
st.title("تحليل تسعير مفصل لعيادة الأسنان مع وزن الوقت 📊🦷")
st.markdown("...") # Keep intro markdown

initialize_session_state()

# --- Tabs ---
tab1, tab2 = st.tabs(["🎛️ إدخال البيانات وحساب التسعير", "📈 التحليلات والرسوم البيانية"])

# --- Tab 1: Data Input and Calculation ---
with tab1:
    st.header("1. إدخال التكاليف الثابتة الشهرية")
    # ... (Fixed cost input fields remain the same) ...
    col1_fixed, col2_fixed = st.columns(2)
    with col1_fixed:
        rent = st.number_input("إيجار العيادة (جنيه)", min_value=0.0, value=15000.0, step=500.0, key="rent")
        salaries = st.number_input("رواتب العاملين (جنيه)", min_value=0.0, value=20000.0, step=500.0, key="salaries")
        utilities = st.number_input("فواتير الخدمات (كهرباء، ماء، إنترنت) (جنيه)", min_value=0.0, value=5000.0, step=200.0, key="utilities")
    with col2_fixed:
        insurance = st.number_input("تأمين وصيانة ومصاريف إدارية (جنيه)", min_value=0.0, value=2000.0, step=100.0, key="insurance")
        marketing = st.number_input("تكاليف تسويق وإعلان (جنيه)", min_value=0.0, value=1000.0, step=100.0, key="marketing")
        other_fixed = st.number_input("تكاليف ثابتة أخرى (جنيه)", min_value=0.0, value=0.0, step=100.0, key="other_fixed")

    current_total_fixed_cost = rent + salaries + utilities + insurance + marketing + other_fixed
    st.metric(label="**إجمالي التكاليف الثابتة الشهرية**", value=f"{current_total_fixed_cost:,.2f} جنيه")
    st.divider()


    st.header("2. إدارة بيانات الخدمات")
    st.caption("عرض وتعديل وإضافة الخدمات المقدمة.")

    # --- Display Current Services DataFrame ---
    st.subheader("الخدمات الحالية:")
    if st.session_state[STATE_SERVICES_DF].empty:
        st.info("لا توجد خدمات مدرجة حالياً. يرجى استخدام نموذج الإضافة أدناه.")
    else:
        # Display the DataFrame - make it non-editable here
        st.dataframe(
            st.session_state[STATE_SERVICES_DF],
            hide_index=True, # Often cleaner without the default index
            use_container_width=True,
            column_config={ # Define formatting for display
                 COL_EXPECTED_CASES: st.column_config.NumberColumn(format="%d"),
                 COL_VAR_COST: st.column_config.NumberColumn(format="%.2f ج"),
                 COL_DURATION: st.column_config.NumberColumn(format="%.2f ساعة"),
            }
            )

        # --- Add Edit/Delete buttons iterating outside the dataframe ---
        st.write("--- إجراءات التعديل والحذف ---")
        services_df = st.session_state[STATE_SERVICES_DF] # Get reference
        indices_to_delete = []

        for index in services_df.index:
            service_name = services_df.loc[index, COL_NAME]
            cols = st.columns([4, 1, 1]) # Adjust column ratios as needed
            cols[0].write(f"**{service_name}** (صف رقم: {index})") # Show index for reference

            # Edit Button
            edit_key = f"edit_{index}_{service_name}"
            if cols[1].button("✏️ تعديل", key=edit_key):
                st.session_state[STATE_EDIT_TARGET_INDEX] = index # Set index to edit
                st.rerun() # Rerun to show the edit form

            # Delete Button
            delete_key = f"delete_{index}_{service_name}"
            if cols[2].button("🗑️ حذف", key=delete_key):
                indices_to_delete.append(index)
                # Clear edit target if the row being edited is deleted
                if st.session_state[STATE_EDIT_TARGET_INDEX] == index:
                    st.session_state[STATE_EDIT_TARGET_INDEX] = None

        # Process deletions after the loop
        if indices_to_delete:
            st.session_state[STATE_SERVICES_DF] = services_df.drop(indices_to_delete).reset_index(drop=True)
            # If we deleted the row being edited, ensure the edit state is cleared
            if st.session_state[STATE_EDIT_TARGET_INDEX] in indices_to_delete:
                 st.session_state[STATE_EDIT_TARGET_INDEX] = None
            st.rerun() # Rerun to reflect deletions


    # --- Conditional Edit Form ---
    if st.session_state[STATE_EDIT_TARGET_INDEX] is not None:
        edit_index = st.session_state[STATE_EDIT_TARGET_INDEX]
        # Check if index still exists after potential deletions
        if edit_index in st.session_state[STATE_SERVICES_DF].index:
            st.subheader(f"📝 تعديل بيانات الخدمة (صف رقم: {edit_index})")
            service_data = st.session_state[STATE_SERVICES_DF].loc[edit_index]

            with st.form(f"edit_service_form_{edit_index}"):
                st.info(f"التعديل على: **{service_data[COL_NAME]}**") # Show which service is being edited
                # Note: Don't allow editing the name easily here, as it might break lookups if used elsewhere.
                # If name editing is needed, add careful checks for uniqueness.

                edited_cases = st.number_input("عدد الحالات المتوقعة/شهر", min_value=0, step=1, key=f"edit_cases_{edit_index}", value=int(service_data[COL_EXPECTED_CASES]))
                edited_var_cost = st.number_input("التكلفة المتغيرة للحالة (جنيه)", min_value=0.0, step=10.0, format="%.2f", key=f"edit_var_cost_{edit_index}", value=float(service_data[COL_VAR_COST]))
                edited_duration = st.number_input("مدة الخدمة (ساعات)", min_value=0.1, step=0.25, format="%.2f", key=f"edit_duration_{edit_index}", value=float(service_data[COL_DURATION]))

                submitted_edit = st.form_submit_button("💾 حفظ التعديلات")
                if submitted_edit:
                     if edited_duration <= 0:
                          st.warning("يرجى إدخال مدة خدمة أكبر من صفر.")
                     else:
                        # Update the DataFrame in session state
                        st.session_state[STATE_SERVICES_DF].loc[edit_index, COL_EXPECTED_CASES] = edited_cases
                        st.session_state[STATE_SERVICES_DF].loc[edit_index, COL_VAR_COST] = edited_var_cost
                        st.session_state[STATE_SERVICES_DF].loc[edit_index, COL_DURATION] = edited_duration

                        st.session_state[STATE_EDIT_TARGET_INDEX] = None # Clear edit state
                        st.success("تم حفظ التعديلات.")
                        st.rerun() # Rerun to show updated table and hide form
        else:
            # Index doesn't exist anymore (e.g., deleted), clear the edit state
             st.session_state[STATE_EDIT_TARGET_INDEX] = None
             st.warning("الخدمة التي كنت تحاول تعديلها لم تعد موجودة.")
             st.rerun()


    # --- Add New Service Form ---
    # Place it clearly separated, maybe within an expander
    with st.expander("➕ إضافة خدمة جديدة", expanded=(st.session_state[STATE_EDIT_TARGET_INDEX] is None)): # Keep open if not editing
        with st.form("add_service_form", clear_on_submit=True):
            new_name = st.text_input("اسم الخدمة الجديدة")
            col1_add, col2_add, col3_add = st.columns(3)
            with col1_add:
                new_expected_cases = st.number_input("عدد الحالات المتوقعة/شهر", min_value=0, step=1, key="add_cases")
            with col2_add:
                new_variable_cost = st.number_input("التكلفة المتغيرة للحالة (جنيه)", min_value=0.0, step=10.0, format="%.2f", key="add_var_cost")
            with col3_add:
                new_duration = st.number_input("مدة الخدمة (ساعات)", min_value=0.1, step=0.25, format="%.2f", key="add_duration", help="متوسط وقت الكرسي الفعلي")

            submitted_add = st.form_submit_button("➕ إضافة الخدمة")
            if submitted_add:
                if not new_name:
                    st.warning("يرجى إدخال اسم للخدمة الجديدة.")
                elif new_duration <= 0:
                    st.warning("يرجى إدخال مدة خدمة أكبر من صفر.")
                # Check for duplicate service names
                elif new_name in st.session_state[STATE_SERVICES_DF][COL_NAME].tolist():
                    st.warning(f"الخدمة باسم '{new_name}' موجودة بالفعل. يرجى اختيار اسم فريد.")
                else:
                    new_service_data = pd.DataFrame([{
                        COL_NAME: new_name,
                        COL_EXPECTED_CASES: new_expected_cases,
                        COL_VAR_COST: new_variable_cost,
                        COL_DURATION: new_duration
                    }])
                    # Use pd.concat to append the new row
                    st.session_state[STATE_SERVICES_DF] = pd.concat(
                        [st.session_state[STATE_SERVICES_DF], new_service_data],
                        ignore_index=True # Reset index after adding
                    )
                    st.success(f"تمت إضافة خدمة '{new_name}'.")
                    st.rerun() # Rerun to update the main dataframe display

    st.divider()

    st.header("3. تحديد هامش الربح المستهدف")
    # ... (Margin slider remains the same) ...
    current_margin_percentage = st.slider(
        "هامش الربح المطلوب فوق التكلفة الإجمالية (%)",
        min_value=0, max_value=200, value=int(st.session_state[STATE_MARGIN] * 100), step=5,
        key="margin_slider"
    )
    current_margin = current_margin_percentage / 100.0
    st.info(f"...") # Keep info text

    # --- Calculation Trigger ---
    if st.button("✅ حساب التسعير التفصيلي وتحديث التحليلات", type="primary"):
        # Read the potentially modified DataFrame from session state
        current_services_df = st.session_state[STATE_SERVICES_DF]

        if not current_services_df.empty:
            results = calculate_detailed_pricing(
                current_services_df, # Pass the DataFrame directly
                current_total_fixed_cost,
                current_margin
            )
            if results is not None:
                st.session_state[STATE_RESULTS_DF] = results
                st.session_state[STATE_TOTAL_FIXED_COST] = current_total_fixed_cost
                st.session_state[STATE_MARGIN] = current_margin
                st.session_state[STATE_CALCULATED] = True
                st.success("تم حساب التسعير بنجاح! يمكنك الآن عرض النتائج أدناه وفي تبويب التحليلات.")
            else:
                 st.session_state[STATE_CALCULATED] = False
        else:
            st.warning("لا يمكن إجراء الحسابات. يرجى إضافة بيانات خدمة واحدة على الأقل.")
            st.session_state[STATE_CALCULATED] = False


    # --- Display Results Table (if calculated) ---
    if st.session_state[STATE_CALCULATED] and st.session_state[STATE_RESULTS_DF] is not None:
        st.subheader("📋 نتائج التحليل التفصيلي لكل خدمة")
        # ... (Display logic for results_df remains the same) ...
        display_df = st.session_state[STATE_RESULTS_DF]
        display_df_final = display_df[[
            COL_NAME, COL_EXPECTED_CASES, COL_VAR_COST, COL_DURATION,
            COL_FIXED_COST_PER_CASE, COL_TOTAL_COST_PER_CASE, COL_PRICE_PER_CASE,
            COL_CONTRIB_MARGIN, COL_BREAK_EVEN
        ]].rename(columns={ # Renaming columns for Arabic display
            COL_NAME: "اسم الخدمة", COL_EXPECTED_CASES: "الحالات المتوقعة",
            COL_VAR_COST: "التكلفة المتغيرة/حالة", COL_DURATION: "مدة (ساعة)",
            COL_FIXED_COST_PER_CASE: "تكلفة ثابتة/حالة", COL_TOTAL_COST_PER_CASE: "تكلفة إجمالية/حالة",
            COL_PRICE_PER_CASE: "السعر المقترح/حالة", COL_CONTRIB_MARGIN: "هامش المساهمة/حالة",
            COL_BREAK_EVEN: "نقطة التعادل (عدد حالات)"
        })

        st.dataframe(display_df_final.style.format({
            "التكلفة المتغيرة/حالة": "{:,.2f} ج", "مدة (ساعة)": "{:.2f}",
            "تكلفة ثابتة/حالة": "{:,.2f} ج", "تكلفة إجمالية/حالة": "{:,.2f} ج",
            "السعر المقترح/حالة": "{:,.2f} ج", "هامش المساهمة/حالة": "{:,.2f} ج",
            "نقطة التعادل (عدد حالات)": "{:.1f}"
        }), use_container_width=True)

        # --- Totals Summary ---
        total_expected_revenue = (display_df[COL_PRICE_PER_CASE] * display_df[COL_EXPECTED_CASES]).sum()
        total_expected_variable_cost = (display_df[COL_VAR_COST] * display_df[COL_EXPECTED_CASES]).sum()
        total_expected_profit = total_expected_revenue - total_expected_variable_cost - st.session_state[STATE_TOTAL_FIXED_COST]
        st.subheader("📊 ملخص التوقعات الإجمالية")
        col_rev, col_cost, col_profit = st.columns(3)
        col_rev.metric("إجمالي الإيرادات المتوقعة", f"{total_expected_revenue:,.2f} ج")
        col_cost.metric("إجمالي التكاليف المتوقعة", f"{(total_expected_variable_cost + st.session_state[STATE_TOTAL_FIXED_COST]):,.2f} ج")
        col_profit.metric("إجمالي الربح المتوقع", f"{total_expected_profit:,.2f} ج", delta_color="normal")

    elif not st.session_state[STATE_CALCULATED]:
        st.info("يرجى إدخال/تعديل بيانات الخدمات والتكاليف الثابتة، ثم الضغط على زر 'حساب التسعير' لعرض النتائج.")


# --- Tab 2: Analysis and Plots ---
with tab2:
    st.header("📈 تحليل الحساسية للخدمات (Sensitivity Analysis)")
    # ... (Analysis tab logic remains exactly the same, using results from session state) ...
    if not st.session_state[STATE_CALCULATED] or st.session_state[STATE_RESULTS_DF] is None:
        st.warning("يرجى الضغط على زر 'حساب التسعير' في التبويب الأول لعرض التحليلات.")
    else:
        results_df = st.session_state[STATE_RESULTS_DF]
        if results_df.empty or COL_NAME not in results_df.columns:
             st.warning("لا توجد نتائج تحليل متاحة أو أن النتائج غير مكتملة.")
        else:
            service_names = results_df[COL_NAME].tolist()
            if not service_names:
                st.warning("لا توجد خدمات متاحة للتحليل في النتائج المحسوبة.")
            else:
                selected_service_name = st.selectbox(
                    "اختر الخدمة لتحليل حساسيتها لتغير عدد الحالات:",
                    options=service_names, index=0, key="service_select"
                )

                if selected_service_name and selected_service_name in results_df[COL_NAME].values:
                    service_data = results_df[results_df[COL_NAME] == selected_service_name].iloc[0]
                    st.markdown(f"#### تحليل حساسية الخدمة: **{selected_service_name}**")
                    st.caption(f"""...""") # Keep caption

                    col_sens1, col_sens2, col_sens3 = st.columns(3)
                    with col_sens1:
                        min_cases = st.number_input("أقل عدد للحالات في التحليل (Min Cases)", ...)
                    with col_sens2:
                        max_cases = st.number_input("أعلى عدد للحالات في التحليل (Max Cases)", ...)
                    with col_sens3:
                        step_cases = st.number_input("الخطوة (Step)", ...)

                    if max_cases <= min_cases:
                        st.error("...")
                    else:
                        cases_range_list = list(range(int(min_cases), int(max_cases) + 1, int(step_cases)))
                        if not cases_range_list:
                             st.warning("...")
                        else:
                            prices, break_evens = calculate_sensitivity(...)
                            sensitivity_fig = plot_sensitivity(cases_range_list, prices, break_evens)
                            st.pyplot(sensitivity_fig)
                else:
                    st.error(f"...")
