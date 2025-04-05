import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional

# --- Constants ---
# Define column names as constants for consistency and easier refactoring
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
COL_SERVICE_HOURS = "service_hours" # Intermediate calculation column

# Define keys for session state
STATE_RESULTS_DF = "results_df"
STATE_TOTAL_FIXED_COST = "total_fixed_cost"
STATE_MARGIN = "margin"
STATE_CALCULATED = "calculated" # Flag to check if calculation was done

# --- Helper Functions ---

def initialize_session_state():
    """Initializes required keys in Streamlit's session state."""
    if STATE_RESULTS_DF not in st.session_state:
        st.session_state[STATE_RESULTS_DF] = None
    if STATE_TOTAL_FIXED_COST not in st.session_state:
        st.session_state[STATE_TOTAL_FIXED_COST] = 0.0
    if STATE_MARGIN not in st.session_state:
        st.session_state[STATE_MARGIN] = 0.30 # Default 30%
    if STATE_CALCULATED not in st.session_state:
        st.session_state[STATE_CALCULATED] = False

def calculate_detailed_pricing(
    services_df: pd.DataFrame,
    total_fixed_cost: float,
    margin: float
) -> Optional[pd.DataFrame]:
    """
    Calculates detailed pricing, cost allocation, and break-even points for services.

    Args:
        services_df: DataFrame containing service details (name, expected_cases, variable_cost, duration_hours).
        total_fixed_cost: Total fixed costs for the period.
        margin: Desired profit margin (e.g., 0.30 for 30%).

    Returns:
        A DataFrame with calculated pricing details, or None if input is invalid.
    """
    if services_df.empty:
        st.error("لا توجد بيانات خدمات لإجراء الحسابات. يرجى إضافة خدمة واحدة على الأقل.")
        return None

    # Ensure correct data types (st.data_editor might change them)
    try:
        services_df[COL_EXPECTED_CASES] = services_df[COL_EXPECTED_CASES].astype(int)
        services_df[COL_VAR_COST] = services_df[COL_VAR_COST].astype(float)
        services_df[COL_DURATION] = services_df[COL_DURATION].astype(float)
        # Ensure non-negative values where appropriate
        if (services_df[COL_EXPECTED_CASES] < 0).any() or \
           (services_df[COL_VAR_COST] < 0).any() or \
           (services_df[COL_DURATION] <= 0).any(): # Duration must be positive
             st.error("يرجى التأكد من أن عدد الحالات والتكلفة المتغيرة ليست سالبة، وأن مدة الخدمة أكبر من صفر.")
             return None
    except Exception as e:
        st.error(f"خطأ في تحويل أنواع البيانات: {e}. يرجى التحقق من إدخالات الجدول.")
        return None

    # Calculate total "service hours" (weight) for allocation
    services_df[COL_SERVICE_HOURS] = services_df[COL_EXPECTED_CASES] * services_df[COL_DURATION]
    total_service_hours = services_df[COL_SERVICE_HOURS].sum()

    if total_service_hours <= 0:
        st.warning("إجمالي ساعات الخدمة (الوزن) هو صفر أو أقل. لا يمكن توزيع التكاليف الثابتة.")
        # Assign zero fixed costs in this edge case, or handle as appropriate
        services_df[COL_ALLOC_FIXED_COST] = 0.0
        services_df[COL_FIXED_COST_PER_CASE] = 0.0
    else:
        # Allocate fixed costs based on time weight
        services_df[COL_ALLOC_FIXED_COST] = total_fixed_cost * (services_df[COL_SERVICE_HOURS] / total_service_hours)

        # Calculate fixed cost per case (handle division by zero if expected_cases is 0)
        services_df[COL_FIXED_COST_PER_CASE] = services_df.apply(
            lambda row: row[COL_ALLOC_FIXED_COST] / row[COL_EXPECTED_CASES] if row[COL_EXPECTED_CASES] > 0 else 0,
            axis=1
        )

    # Calculate total cost and price
    services_df[COL_TOTAL_COST_PER_CASE] = services_df[COL_VAR_COST] + services_df[COL_FIXED_COST_PER_CASE]
    services_df[COL_PRICE_PER_CASE] = services_df[COL_TOTAL_COST_PER_CASE] * (1 + margin)

    # Calculate contribution margin and break-even
    services_df[COL_CONTRIB_MARGIN] = services_df[COL_PRICE_PER_CASE] - services_df[COL_VAR_COST]
    services_df[COL_BREAK_EVEN] = services_df.apply(
        lambda row: row[COL_ALLOC_FIXED_COST] / row[COL_CONTRIB_MARGIN] if row[COL_CONTRIB_MARGIN] > 0 else float('inf'), # Indicate infinite BE if margin is non-positive
        axis=1
    )

    return services_df

def calculate_sensitivity(
    variable_cost: float,
    allocated_fixed_cost: float, # Fixed cost allocated based on *initial* calculation
    margin: float,
    cases_range: range
) -> Tuple[List[float], List[float]]:
    """
    Calculates price and break-even sensitivity based on varying case numbers,
    assuming the initial fixed cost allocation per service remains constant.

    Args:
        variable_cost: Variable cost per case for the specific service.
        allocated_fixed_cost: Total fixed cost allocated to this service (from initial calc).
        margin: Desired profit margin.
        cases_range: A range object representing the number of cases to analyze.

    Returns:
        A tuple containing two lists: (prices, break_even_points).
    """
    prices = []
    break_evens = []
    for cases in cases_range:
        if cases <= 0: # Avoid division by zero for fixed_cost_per_case
            price = float('inf') # Or handle as appropriate (e.g., skip, set to None)
            be = float('inf')
        else:
            fixed_cost_per_case = allocated_fixed_cost / cases
            total_cost = variable_cost + fixed_cost_per_case
            price = total_cost * (1 + margin)
            contribution_margin = price - variable_cost
            if contribution_margin <= 0:
                be = float('inf') # Infinite break-even if no positive contribution
            else:
                be = allocated_fixed_cost / contribution_margin
        prices.append(price)
        break_evens.append(be)
    return prices, break_evens

def plot_sensitivity(cases_range: List[int], prices: List[float], break_evens: List[float]) -> plt.Figure:
    """Generates Matplotlib plots for sensitivity analysis."""
    fig, axs = plt.subplots(1, 2, figsize=(12, 5)) # Keep using Matplotlib as requested

    # Plot Price Sensitivity
    axs[0].plot(cases_range, prices, marker='o', linestyle='-', color='royalblue')
    axs[0].set_title("حساسية السعر النهائي مقابل عدد الحالات")
    axs[0].set_xlabel("عدد الحالات المتغير")
    axs[0].set_ylabel("السعر النهائي المحسوب لكل حالة (جنيه)")
    axs[0].grid(True, linestyle='--', alpha=0.6)
    axs[0].ticklabel_format(style='plain', axis='y') # Avoid scientific notation

    # Plot Break-even Sensitivity
    axs[1].plot(cases_range, break_evens, marker='x', linestyle='--', color='crimson')
    axs[1].set_title("حساسية نقطة التعادل مقابل عدد الحالات")
    axs[1].set_xlabel("عدد الحالات المتغير")
    axs[1].set_ylabel("نقطة التعادل المحسوبة (عدد الحالات)")
    axs[1].grid(True, linestyle='--', alpha=0.6)
    axs[1].ticklabel_format(style='plain', axis='y')

    # Improve layout
    fig.tight_layout(pad=3.0)
    return fig


# --- Streamlit App Layout ---

st.set_page_config(layout="wide") # Use wider layout for tables/plots
st.title("تحليل تسعير مفصل لعيادة الأسنان مع وزن الوقت 📊🦷")
st.markdown("""
هذه الأداة تساعد في تحديد أسعار خدمات عيادة الأسنان بناءً على التكاليف الثابتة والمتغيرة،
مع الأخذ في الاعتبار **الوقت المستغرق لكل خدمة** كأساس لتوزيع التكاليف الثابتة.
""")

# Initialize session state
initialize_session_state()

# Default data (can be loaded from file/DB in a real app)
default_services_data = [
    {"name": "تنظيف الأسنان", "expected_cases": 80, "variable_cost": 150.0, "duration_hours": 1.0},
    {"name": "حشو الأسنان", "expected_cases": 60, "variable_cost": 250.0, "duration_hours": 1.0},
    {"name": "علاج جذور الأسنان", "expected_cases": 40, "variable_cost": 500.0, "duration_hours": 2.0},
    {"name": "تقويم الأسنان", "expected_cases": 20, "variable_cost": 1000.0, "duration_hours": 2.0},
    {"name": "تبييض الأسنان", "expected_cases": 50, "variable_cost": 350.0, "duration_hours": 1.0},
    {"name": "زراعة الأسنان", "expected_cases": 10, "variable_cost": 3000.0, "duration_hours": 3.0}
]
# Use session state to store the editable services dataframe to preserve edits across runs
if 'editable_services_df' not in st.session_state:
    st.session_state['editable_services_df'] = pd.DataFrame(default_services_data)


# --- Tabs ---
tab1, tab2 = st.tabs(["🎛️ إدخال البيانات وحساب التسعير", "📈 التحليلات والرسوم البيانية"])

# --- Tab 1: Data Input and Calculation ---
with tab1:
    st.header("1. إدخال التكاليف الثابتة الشهرية")
    st.caption("أدخل التكاليف التي لا تتغير مباشرة بتغير عدد الحالات (مثل الإيجار، الرواتب الأساسية).")
    col1, col2 = st.columns(2)
    with col1:
        rent = st.number_input("إيجار العيادة (جنيه)", min_value=0.0, value=15000.0, step=500.0, key="rent")
        salaries = st.number_input("رواتب العاملين (جنيه)", min_value=0.0, value=20000.0, step=500.0, key="salaries")
        utilities = st.number_input("فواتير الخدمات (كهرباء، ماء، إنترنت) (جنيه)", min_value=0.0, value=5000.0, step=200.0, key="utilities")
    with col2:
        insurance = st.number_input("تأمين وصيانة ومصاريف إدارية (جنيه)", min_value=0.0, value=2000.0, step=100.0, key="insurance")
        marketing = st.number_input("تكاليف تسويق وإعلان (جنيه)", min_value=0.0, value=1000.0, step=100.0, key="marketing")
        other_fixed = st.number_input("تكاليف ثابتة أخرى (جنيه)", min_value=0.0, value=0.0, step=100.0, key="other_fixed")

    # Calculate and display total fixed costs
    current_total_fixed_cost = rent + salaries + utilities + insurance + marketing + other_fixed
    st.metric(label="**إجمالي التكاليف الثابتة الشهرية**", value=f"{current_total_fixed_cost:,.2f} جنيه")

    st.divider()

    st.header("2. بيانات الخدمات وتكاليفها المتغيرة ومدتها")
    st.caption("""
    أدخل أو عدّل الخدمات المقدمة.
    - **التكلفة المتغيرة:** تكلفة المواد المستهلكة مباشرة لكل حالة (مواد حشو، زرعة، مواد تبييض، إلخ).
    - **مدة الخدمة (بالساعات):** متوسط الوقت الفعلي الذي تستغرقه الخدمة (وقت الطبيب/المساعد على الكرسي). هذا الوزن يستخدم لتوزيع التكاليف الثابتة.
    - **عدد الحالات المتوقعة:** تقدير لعدد المرات التي ستقدم فيها الخدمة خلال الشهر (يؤثر على توزيع التكلفة الثابتة لكل حالة).
    """)

    # Use st.data_editor for interactive editing, linked to session state
    edited_services_df = st.data_editor(
        st.session_state['editable_services_df'],
        num_rows="dynamic",
        key="data_editor",
        use_container_width=True,
         column_config={ # Optional: Add more specific configurations
            COL_NAME: st.column_config.TextColumn("اسم الخدمة", required=True),
            COL_EXPECTED_CASES: st.column_config.NumberColumn("عدد الحالات المتوقعة/شهر", min_value=0, format="%d"),
            COL_VAR_COST: st.column_config.NumberColumn("التكلفة المتغيرة للحالة (جنيه)", min_value=0.0, format="%.2f"),
            COL_DURATION: st.column_config.NumberColumn("مدة الخدمة (ساعات)", min_value=0.1, step=0.25, format="%.2f", help="أدخل متوسط وقت الكرسي الفعلي بالساعات (مثال: 1.5 يعني ساعة ونصف)")
        }
    )
    # Update session state with the potentially edited data
    st.session_state['editable_services_df'] = edited_services_df

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
        if edited_services_df is not None and not edited_services_df.empty:
            results = calculate_detailed_pricing(
                edited_services_df.copy(), # Pass a copy to avoid modifying the editor's source directly
                current_total_fixed_cost,
                current_margin
            )
            if results is not None:
                # Store results in session state for Tab 2
                st.session_state[STATE_RESULTS_DF] = results
                st.session_state[STATE_TOTAL_FIXED_COST] = current_total_fixed_cost
                st.session_state[STATE_MARGIN] = current_margin
                st.session_state[STATE_CALCULATED] = True
                st.success("تم حساب التسعير بنجاح! يمكنك الآن عرض النتائج أدناه وفي تبويب التحليلات.")
            else:
                # Calculation failed, handled by error messages in the function
                 st.session_state[STATE_CALCULATED] = False
        else:
            st.warning("لا يمكن إجراء الحسابات. يرجى إضافة بيانات خدمة واحدة على الأقل.")
            st.session_state[STATE_CALCULATED] = False


    # --- Display Results Table (if calculated) ---
    if st.session_state[STATE_CALCULATED] and st.session_state[STATE_RESULTS_DF] is not None:
        st.subheader("📋 نتائج التحليل التفصيلي لكل خدمة")
        display_df = st.session_state[STATE_RESULTS_DF]

        # Select and rename columns for display
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
            "نقطة التعادل (عدد حالات)": "{:.1f}"
        }), use_container_width=True)

        # Optional: Display total potential revenue/profit based on expected cases
        total_expected_revenue = (display_df[COL_PRICE_PER_CASE] * display_df[COL_EXPECTED_CASES]).sum()
        total_expected_variable_cost = (display_df[COL_VAR_COST] * display_df[COL_EXPECTED_CASES]).sum()
        total_expected_profit = total_expected_revenue - total_expected_variable_cost - st.session_state[STATE_TOTAL_FIXED_COST]

        st.subheader("📊 ملخص التوقعات الإجمالية")
        col_rev, col_cost, col_profit = st.columns(3)
        col_rev.metric("إجمالي الإيرادات المتوقعة", f"{total_expected_revenue:,.2f} ج")
        col_cost.metric("إجمالي التكاليف المتوقعة", f"{(total_expected_variable_cost + st.session_state[STATE_TOTAL_FIXED_COST]):,.2f} ج")
        col_profit.metric("إجمالي الربح المتوقع", f"{total_expected_profit:,.2f} ج")

    elif not st.session_state[STATE_CALCULATED]:
        st.info("يرجى إدخال/تعديل البيانات والضغط على زر 'حساب التسعير' لعرض النتائج.")


# --- Tab 2: Analysis and Plots ---
with tab2:
    st.header("📈 تحليل الحساسية للخدمات")

    if not st.session_state[STATE_CALCULATED] or st.session_state[STATE_RESULTS_DF] is None:
        st.warning("يرجى الضغط على زر 'حساب التسعير' في التبويب الأول لعرض التحليلات.")
    else:
        results_df = st.session_state[STATE_RESULTS_DF]
        service_names = results_df[COL_NAME].tolist()

        if not service_names:
             st.warning("لا توجد خدمات متاحة للتحليل.")
        else:
            selected_service_name = st.selectbox(
                "اختر الخدمة لتحليل حساسيتها لتغير عدد الحالات:",
                options=service_names,
                index=0, # Default to first service
                key="service_select"
            )

            if selected_service_name:
                # Find the data for the selected service from the *calculated* results
                service_data = results_df[results_df[COL_NAME] == selected_service_name].iloc[0]

                st.markdown(f"#### تحليل حساسية الخدمة: **{selected_service_name}**")
                st.caption(f"""
                يُظهر هذا التحليل كيف يتغير **السعر المقترح** و**نقطة التعادل** لهذه الخدمة
                إذا تغير عدد الحالات الفعلي عن العدد المتوقع ({service_data[COL_EXPECTED_CASES]} حالة).
                 **ملاحظة:** يفترض هذا التحليل أن التوزيع الأولي للتكاليف الثابتة (المبلغ المخصص لهذه الخدمة: {service_data[COL_ALLOC_FIXED_COST]:,.2f} ج) يبقى كما هو.
                """)

                # Get sensitivity parameters
                col_sens1, col_sens2, col_sens3 = st.columns(3)
                with col_sens1:
                    min_cases = st.number_input("أقل عدد للحالات في التحليل", min_value=1, value=max(1, int(service_data[COL_EXPECTED_CASES] * 0.2)), step=1, key="min_cases_sens") # Start near 20% of expected
                with col_sens2:
                     max_cases = st.number_input("أعلى عدد للحالات في التحليل", min_value=int(min_cases)+1, value=int(service_data[COL_EXPECTED_CASES] * 2.0), step=5, key="max_cases_sens") # End near 200% of expected
                with col_sens3:
                    step_cases = st.number_input("الخطوة (الزيادة) في عدد الحالات", min_value=1, value=max(1, int((max_cases - min_cases)/10)), step=1, key="step_cases_sens") # Aim for ~10 steps

                if max_cases <= min_cases:
                    st.error("يجب أن يكون أعلى عدد للحالات أكبر من أقل عدد.")
                else:
                    # Prepare range for analysis
                    cases_range_list = list(range(int(min_cases), int(max_cases) + 1, int(step_cases)))

                    if not cases_range_list:
                        st.warning("نطاق تحليل الحالات المحدد فارغ. يرجى تعديل القيم.")
                    else:
                        # Perform sensitivity analysis using the function
                        prices, break_evens = calculate_sensitivity(
                            variable_cost=service_data[COL_VAR_COST],
                            allocated_fixed_cost=service_data[COL_ALLOC_FIXED_COST], # Use the already allocated cost
                            margin=st.session_state[STATE_MARGIN],
                            cases_range=cases_range_list
                        )

                        # Generate and display plots
                        sensitivity_fig = plot_sensitivity(cases_range_list, prices, break_evens)
                        st.pyplot(sensitivity_fig)

                        # Optional: Display sensitivity data in a table
                        # sens_data = pd.DataFrame({
                        #     "عدد الحالات المفترض": cases_range_list,
                        #     "السعر المحسوب للحالة (ج)": prices,
                        #     "نقطة التعادل المحسوبة (حالة)": break_evens
                        # })
                        # st.dataframe(sens_data.style.format("{:.2f}", subset=["السعر المحسوب للحالة (ج)", "نقطة التعادل المحسوبة (حالة)"]))
