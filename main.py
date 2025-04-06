import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
import copy # Needed for deep copying service dictionaries

# --- Constants ---
# Define column names (remain useful even if input is list of dicts)
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
STATE_SERVICES_LIST = "services_list" # <-- New: Store services as a list of dicts
STATE_RESULTS_DF = "results_df"
STATE_TOTAL_FIXED_COST = "total_fixed_cost"
STATE_MARGIN = "margin"
STATE_CALCULATED = "calculated"

# --- Helper Functions ---

def initialize_session_state():
    """Initializes required keys in Streamlit's session state."""
    # Default data (now loaded into the list)
    default_services_data = [
        {"name": "تنظيف الأسنان", "expected_cases": 80, "variable_cost": 150.0, "duration_hours": 1.0},
        {"name": "حشو الأسنان", "expected_cases": 60, "variable_cost": 250.0, "duration_hours": 1.0},
        {"name": "علاج جذور الأسنان", "expected_cases": 40, "variable_cost": 500.0, "duration_hours": 2.0},
        {"name": "تقويم الأسنان", "expected_cases": 20, "variable_cost": 1000.0, "duration_hours": 2.0},
        {"name": "تبييض الأسنان", "expected_cases": 50, "variable_cost": 350.0, "duration_hours": 1.0},
        {"name": "زراعة الأسنان", "expected_cases": 10, "variable_cost": 3000.0, "duration_hours": 3.0}
    ]
    if STATE_SERVICES_LIST not in st.session_state:
        # Store as a list of dictionaries
        st.session_state[STATE_SERVICES_LIST] = copy.deepcopy(default_services_data)

    if STATE_RESULTS_DF not in st.session_state:
        st.session_state[STATE_RESULTS_DF] = None
    if STATE_TOTAL_FIXED_COST not in st.session_state:
        st.session_state[STATE_TOTAL_FIXED_COST] = 0.0
    if STATE_MARGIN not in st.session_state:
        st.session_state[STATE_MARGIN] = 0.30 # Default 30%
    if STATE_CALCULATED not in st.session_state:
        st.session_state[STATE_CALCULATED] = False

def calculate_detailed_pricing(
    services_list: List[Dict[str, Any]], # <-- Accepts list of dicts
    total_fixed_cost: float,
    margin: float
) -> Optional[pd.DataFrame]:
    """
    Calculates detailed pricing, cost allocation, and break-even points for services.
    Converts list of dicts to DataFrame internally.
    """
    if not services_list:
        st.error("لا توجد بيانات خدمات لإجراء الحسابات. يرجى إضافة خدمة واحدة على الأقل.")
        return None

    # Convert list of dicts to DataFrame for easier calculation
    try:
        services_df = pd.DataFrame(services_list)
        # Ensure required columns exist, handle potential missing keys from manual input
        required_cols = [COL_NAME, COL_EXPECTED_CASES, COL_VAR_COST, COL_DURATION]
        if not all(col in services_df.columns for col in required_cols):
             st.error("بعض بيانات الخدمات المدخلة غير مكتملة (اسم، حالات متوقعة، تكلفة متغيرة، مدة).")
             return None
    except Exception as e:
        st.error(f"خطأ في تحويل بيانات الخدمات إلى جدول: {e}")
        return None

    # Data type conversion and validation (same as before)
    try:
        services_df[COL_EXPECTED_CASES] = pd.to_numeric(services_df[COL_EXPECTED_CASES], errors='coerce').fillna(0).astype(int)
        services_df[COL_VAR_COST] = pd.to_numeric(services_df[COL_VAR_COST], errors='coerce').fillna(0.0).astype(float)
        services_df[COL_DURATION] = pd.to_numeric(services_df[COL_DURATION], errors='coerce').fillna(0.0).astype(float)

        if (services_df[COL_EXPECTED_CASES] < 0).any() or \
           (services_df[COL_VAR_COST] < 0).any() or \
           (services_df[COL_DURATION] <= 0).any():
             st.error("يرجى التأكد من أن عدد الحالات والتكلفة المتغيرة ليست سالبة، وأن مدة الخدمة أكبر من صفر.")
             return None
    except Exception as e:
        st.error(f"خطأ في تحويل أنواع بيانات الخدمات: {e}. يرجى التحقق من الإدخالات.")
        return None

    # --- Calculations (same logic as before, operating on the DataFrame) ---
    services_df[COL_SERVICE_HOURS] = services_df[COL_EXPECTED_CASES] * services_df[COL_DURATION]
    total_service_hours = services_df[COL_SERVICE_HOURS].sum()

    if total_service_hours <= 0:
        st.warning("إجمالي ساعات الخدمة (الوزن) هو صفر أو أقل. لا يمكن توزيع التكاليف الثابتة بشكل فعال.")
        services_df[COL_ALLOC_FIXED_COST] = 0.0
        services_df[COL_FIXED_COST_PER_CASE] = 0.0
    else:
        services_df[COL_ALLOC_FIXED_COST] = total_fixed_cost * (services_df[COL_SERVICE_HOURS] / total_service_hours)
        services_df[COL_FIXED_COST_PER_CASE] = services_df.apply(
            lambda row: row[COL_ALLOC_FIXED_COST] / row[COL_EXPECTED_CASES] if row[COL_EXPECTED_CASES] > 0 else 0,
            axis=1
        )

    services_df[COL_TOTAL_COST_PER_CASE] = services_df[COL_VAR_COST] + services_df[COL_FIXED_COST_PER_CASE]
    services_df[COL_PRICE_PER_CASE] = services_df[COL_TOTAL_COST_PER_CASE] * (1 + margin)
    services_df[COL_CONTRIB_MARGIN] = services_df[COL_PRICE_PER_CASE] - services_df[COL_VAR_COST]
    services_df[COL_BREAK_EVEN] = services_df.apply(
        lambda row: row[COL_ALLOC_FIXED_COST] / row[COL_CONTRIB_MARGIN] if row[COL_CONTRIB_MARGIN] > 0 else float('inf'),
        axis=1
    )
    # Add original list index if needed later, though name is likely the better identifier
    # services_df['original_index'] = services_df.index
    return services_df

# Sensitivity calculation function remains the same
def calculate_sensitivity(
    variable_cost: float,
    allocated_fixed_cost: float,
    margin: float,
    cases_range: range
) -> Tuple[List[float], List[float]]:
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

# Plotting function updated with English labels
def plot_sensitivity(cases_range: List[int], prices: List[float], break_evens: List[float]) -> plt.Figure:
    """Generates Matplotlib plots for sensitivity analysis with ENGLISH labels."""
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
    # Handle potential infinity values in break-even for plotting limits
    finite_bes = [be for be in break_evens if be != float('inf')]
    if finite_bes:
        axs[1].set_ylim(bottom=0, top=max(finite_bes) * 1.1 if finite_bes else 10) # Adjust ylim dynamically
    else:
        axs[1].set_ylim(bottom=0)
    axs[1].ticklabel_format(style='plain', axis='y')


    fig.tight_layout(pad=3.0)
    return fig


# --- Streamlit App Layout ---

st.set_page_config(layout="wide")
st.title("تحليل تسعير مفصل لعيادة الأسنان مع وزن الوقت 📊🦷")
st.markdown("""
هذه الأداة تساعد في تحديد أسعار خدمات عيادة الأسنان بناءً على التكاليف الثابتة والمتغيرة،
مع الأخذ في الاعتبار **الوقت المستغرق لكل خدمة** كأساس لتوزيع التكاليف الثابتة.
""")

# Initialize session state (essential for this input method)
initialize_session_state()

# --- Tabs ---
tab1, tab2 = st.tabs(["🎛️ إدخال البيانات وحساب التسعير", "📈 التحليلات والرسوم البيانية"])

# --- Tab 1: Data Input and Calculation ---
with tab1:
    st.header("1. إدخال التكاليف الثابتة الشهرية")
    st.caption("أدخل التكاليف التي لا تتغير مباشرة بتغير عدد الحالات (مثل الإيجار، الرواتب الأساسية).")
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

    st.header("2. إدارة الخدمات (إضافة / حذف)")
    st.caption("""
    أضف الخدمات التي تقدمها العيادة هنا، مع تحديد تكلفتها المتغيرة المباشرة ومدة تنفيذها وعدد الحالات المتوقع شهرياً.
    """)

    # --- Display existing services with Remove buttons ---
    st.subheader("الخدمات الحالية:")
    if not st.session_state[STATE_SERVICES_LIST]:
        st.info("لم يتم إضافة أي خدمات بعد.")

    services_to_remove_indices = []
    for i, service in enumerate(st.session_state[STATE_SERVICES_LIST]):
        col1_disp, col2_disp, col3_disp, col4_disp, col5_disp = st.columns([3, 2, 2, 2, 1])
        with col1_disp:
            st.write(f"**{i+1}. {service.get(COL_NAME, 'N/A')}**")
        with col2_disp:
            st.write(f"حالات: {service.get(COL_EXPECTED_CASES, 0)}")
        with col3_disp:
            st.write(f"تكلفة متغيرة: {service.get(COL_VAR_COST, 0.0):.2f} ج")
        with col4_disp:
            st.write(f"مدة: {service.get(COL_DURATION, 0.0):.2f} ساعة")
        with col5_disp:
            # Generate a unique key for each button
            if st.button("🗑️ حذف", key=f"remove_service_{i}_{service.get(COL_NAME, '')}"):
                # Don't modify list while iterating, mark for removal
                services_to_remove_indices.append(i)

    # Process removals after iteration
    if services_to_remove_indices:
        # Remove items in reverse index order to avoid shifting issues
        for index in sorted(services_to_remove_indices, reverse=True):
            del st.session_state[STATE_SERVICES_LIST][index]
        st.rerun() # Rerun immediately to update the displayed list

    # --- Form to Add New Service ---
    st.subheader("إضافة خدمة جديدة:")
    # Use a form to batch input fields
    with st.form("add_service_form", clear_on_submit=True):
        new_name = st.text_input("اسم الخدمة الجديدة", key="new_name")
        col1_add, col2_add, col3_add = st.columns(3)
        with col1_add:
            new_expected_cases = st.number_input("عدد الحالات المتوقعة/شهر", min_value=0, step=1, key="new_cases")
        with col2_add:
            new_variable_cost = st.number_input("التكلفة المتغيرة للحالة (جنيه)", min_value=0.0, step=10.0, format="%.2f", key="new_var_cost")
        with col3_add:
            new_duration = st.number_input("مدة الخدمة (ساعات)", min_value=0.1, step=0.25, format="%.2f", help="أدخل متوسط وقت الكرسي الفعلي بالساعات (مثال: 1.5 يعني ساعة ونصف)", key="new_duration")

        submitted = st.form_submit_button("➕ إضافة الخدمة")
        if submitted:
            if not new_name:
                st.warning("يرجى إدخال اسم للخدمة الجديدة.")
            elif new_duration <= 0:
                 st.warning("يرجى إدخال مدة خدمة أكبر من صفر.")
            else:
                # Check for duplicate service names (optional but good practice)
                existing_names = [s.get(COL_NAME) for s in st.session_state[STATE_SERVICES_LIST]]
                if new_name in existing_names:
                     st.warning(f"الخدمة باسم '{new_name}' موجودة بالفعل. إذا أردت التعديل، احذف القديمة وأضف الجديدة.")
                else:
                    new_service_data = {
                        COL_NAME: new_name,
                        COL_EXPECTED_CASES: new_expected_cases,
                        COL_VAR_COST: new_variable_cost,
                        COL_DURATION: new_duration
                    }
                    st.session_state[STATE_SERVICES_LIST].append(new_service_data)
                    st.success(f"تمت إضافة خدمة '{new_name}'.")
                    # Rerun to show the new service in the list immediately
                    st.rerun()

    st.divider()

    st.header("3. تحديد هامش الربح المستهدف")
    current_margin_percentage = st.slider(
        "هامش الربح المطلوب فوق التكلفة الإجمالية (%)",
        min_value=0, max_value=200, value=int(st.session_state[STATE_MARGIN] * 100), step=5,
        key="margin_slider"
    )
    current_margin = current_margin_percentage / 100.0

    st.info(f"""
    سيتم حساب السعر كـ: (التكلفة المتغيرة للحالة + [نصيب الحالة من التكاليف الثابتة الموزعة بالوقت]) * (1 + {current_margin_percentage}%)
    """)

    # --- Calculation Trigger ---
    if st.button("✅ حساب التسعير التفصيلي وتحديث التحليلات", type="primary"):
        # Read data directly from the session state list
        current_services_list = st.session_state[STATE_SERVICES_LIST]

        if current_services_list: # Check if the list is not empty
            results = calculate_detailed_pricing(
                copy.deepcopy(current_services_list), # Pass a deep copy to avoid side effects
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
                 st.session_state[STATE_CALCULATED] = False # Calculation failed
                 # Error messages are shown within calculate_detailed_pricing
        else:
            st.warning("لا يمكن إجراء الحسابات. يرجى إضافة بيانات خدمة واحدة على الأقل باستخدام النموذج أعلاه.")
            st.session_state[STATE_CALCULATED] = False

    # --- Display Results Table (if calculated) ---
    if st.session_state[STATE_CALCULATED] and st.session_state[STATE_RESULTS_DF] is not None:
        st.subheader("📋 نتائج التحليل التفصيلي لكل خدمة")
        display_df = st.session_state[STATE_RESULTS_DF]

        # Select and rename columns for display (same as before)
        display_df_final = display_df[[
            COL_NAME,
            COL_EXPECTED_CASES,
            COL_VAR_COST,
            COL_DURATION,
            COL_FIXED_COST_PER_CASE,
            COL_TOTAL_COST_PER_CASE,
            COL_PRICE_PER_CASE,
            COL_CONTRIB_MARGIN,
            COL_BREAK_EVEN
        ]].rename(columns={
            COL_NAME: "اسم الخدمة",
            COL_EXPECTED_CASES: "الحالات المتوقعة",
            COL_VAR_COST: "التكلفة المتغيرة/حالة",
            COL_DURATION: "مدة (ساعة)",
            COL_FIXED_COST_PER_CASE: "تكلفة ثابتة/حالة",
            COL_TOTAL_COST_PER_CASE: "تكلفة إجمالية/حالة",
            COL_PRICE_PER_CASE: "السعر المقترح/حالة",
            COL_CONTRIB_MARGIN: "هامش المساهمة/حالة",
            COL_BREAK_EVEN: "نقطة التعادل (عدد حالات)"
        })

        st.dataframe(display_df_final.style.format({
            "التكلفة المتغيرة/حالة": "{:,.2f} ج",
            "مدة (ساعة)": "{:.2f}",
            "تكلفة ثابتة/حالة": "{:,.2f} ج",
            "تكلفة إجمالية/حالة": "{:,.2f} ج",
            "السعر المقترح/حالة": "{:,.2f} ج",
            "هامش المساهمة/حالة": "{:,.2f} ج",
            "نقطة التعادل (عدد حالات)": "{:.1f}" # Keep BE format reasonable
        }), use_container_width=True)

        # Optional: Display total potential revenue/profit (same as before)
        total_expected_revenue = (display_df[COL_PRICE_PER_CASE] * display_df[COL_EXPECTED_CASES]).sum()
        total_expected_variable_cost = (display_df[COL_VAR_COST] * display_df[COL_EXPECTED_CASES]).sum()
        total_expected_profit = total_expected_revenue - total_expected_variable_cost - st.session_state[STATE_TOTAL_FIXED_COST]

        st.subheader("📊 ملخص التوقعات الإجمالية")
        col_rev, col_cost, col_profit = st.columns(3)
        col_rev.metric("إجمالي الإيرادات المتوقعة", f"{total_expected_revenue:,.2f} ج")
        col_cost.metric("إجمالي التكاليف المتوقعة", f"{(total_expected_variable_cost + st.session_state[STATE_TOTAL_FIXED_COST]):,.2f} ج")
        col_profit.metric("إجمالي الربح المتوقع", f"{total_expected_profit:,.2f} ج", delta_color="normal") # Neutral color for profit delta


    elif not st.session_state[STATE_CALCULATED]:
        st.info("يرجى إدخال/تعديل بيانات الخدمات والتكاليف الثابتة، ثم الضغط على زر 'حساب التسعير' لعرض النتائج.")


# --- Tab 2: Analysis and Plots ---
with tab2:
    st.header("📈 تحليل الحساسية للخدمات (Sensitivity Analysis)") # Added English title part

    if not st.session_state[STATE_CALCULATED] or st.session_state[STATE_RESULTS_DF] is None:
        st.warning("يرجى الضغط على زر 'حساب التسعير' في التبويب الأول لعرض التحليلات.")
    else:
        results_df = st.session_state[STATE_RESULTS_DF]
        # Ensure results_df is not empty and has the name column before proceeding
        if results_df.empty or COL_NAME not in results_df.columns:
             st.warning("لا توجد نتائج تحليل متاحة أو أن النتائج غير مكتملة.")
        else:
            service_names = results_df[COL_NAME].tolist()

            if not service_names:
                st.warning("لا توجد خدمات متاحة للتحليل في النتائج المحسوبة.")
            else:
                selected_service_name = st.selectbox(
                    "اختر الخدمة لتحليل حساسيتها لتغير عدد الحالات:",
                    options=service_names,
                    index=0,
                    key="service_select"
                )

                # Check if selected_service_name exists in the DataFrame (robustness)
                if selected_service_name and selected_service_name in results_df[COL_NAME].values:
                    service_data = results_df[results_df[COL_NAME] == selected_service_name].iloc[0]

                    st.markdown(f"#### تحليل حساسية الخدمة: **{selected_service_name}**")
                    st.caption(f"""
                    يُظهر هذا التحليل كيف يتغير **السعر المقترح (Price)** و**نقطة التعادل (Break-Even)** لهذه الخدمة
                    إذا تغير عدد الحالات الفعلي عن العدد المتوقع ({int(service_data[COL_EXPECTED_CASES])} حالة).
                    **ملاحظة:** يفترض هذا التحليل أن التوزيع الأولي للتكاليف الثابتة (المبلغ المخصص لهذه الخدمة: {service_data[COL_ALLOC_FIXED_COST]:,.2f} ج) يبقى كما هو، وأن التكلفة المتغيرة وهامش الربح لا يتغيران.
                    """)

                    # Get sensitivity parameters (same logic as before)
                    col_sens1, col_sens2, col_sens3 = st.columns(3)
                    with col_sens1:
                        min_cases = st.number_input("أقل عدد للحالات في التحليل (Min Cases)", min_value=1, value=max(1, int(service_data[COL_EXPECTED_CASES] * 0.2)), step=1, key="min_cases_sens")
                    with col_sens2:
                        max_cases = st.number_input("أعلى عدد للحالات في التحليل (Max Cases)", min_value=int(min_cases)+1, value=int(service_data[COL_EXPECTED_CASES] * 2.0), step=5, key="max_cases_sens")
                    with col_sens3:
                        step_cases = st.number_input("الخطوة (Step)", min_value=1, value=max(1, int((max_cases - min_cases)/10) if (max_cases - min_cases)>0 else 1), step=1, key="step_cases_sens")

                    if max_cases <= min_cases:
                        st.error("يجب أن يكون أعلى عدد للحالات أكبر من أقل عدد.")
                    else:
                        cases_range_list = list(range(int(min_cases), int(max_cases) + 1, int(step_cases)))
                        if not cases_range_list:
                             st.warning("نطاق تحليل الحالات المحدد فارغ. يرجى تعديل القيم.")
                        else:
                            # Perform sensitivity analysis
                            prices, break_evens = calculate_sensitivity(
                                variable_cost=service_data[COL_VAR_COST],
                                allocated_fixed_cost=service_data[COL_ALLOC_FIXED_COST],
                                margin=st.session_state[STATE_MARGIN],
                                cases_range=cases_range_list
                            )

                            # Generate and display plots (now with English labels)
                            sensitivity_fig = plot_sensitivity(cases_range_list, prices, break_evens)
                            st.pyplot(sensitivity_fig) # Display the Matplotlib figure
                else:
                    st.error(f"الخدمة المحددة '{selected_service_name}' غير موجودة في نتائج التحليل الحالية.")
