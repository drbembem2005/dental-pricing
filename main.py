# --- START OF FILE main_redesigned.py ---

import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import json
import os
import io # For download buffer

# --- Constants ---
# File for saving data
DATA_FILE = "clinic_data_v2.json"

# Column names (consistent reference)
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
STATE_LANG = "language"
STATE_SETTINGS = "clinic_settings"
STATE_SERVICES_DF_INPUT = "services_df_input" # DataFrame being edited
STATE_RESULTS_DF = "results_df"
STATE_CALCULATED = "calculated"
STATE_SIMULATION_RESULTS_DF = "simulation_results_df"

# --- Language Strings ---
LANG_STRINGS = {
    'en': {
        # General
        'app_title': "Dental Clinic Pricing Dashboard V3 (EGP)",
        'lang_select': "Select Language",
        'sidebar_title': "Clinic Settings",
        'fixed_costs_header': "1. Monthly Fixed Costs (EGP)",
        'rent': "Rent", 'salaries': "Staff Salaries", 'utilities': "Utilities",
        'insurance': "Insurance & Maintenance", 'marketing': "Marketing",
        'other_fixed': "Other Fixed Costs", 'total_fixed_cost': "Total Monthly Fixed Costs",
        'margin_header': "2. Base Target Profit Margin",
        'margin_label': "Base Profit Margin (%)",
        'margin_help': "Desired profit markup on Total Cost/Case (Variable + Allocated Fixed). E.g., 30% means Price = Total Cost * 1.30.",
        'margin_display': "Base Target Margin",
        'reset_button': "Reset All to Defaults",
        'reset_confirm': "Are you sure? This will reset settings and services to the initial defaults and cannot be undone.",
        'data_saved': "Data saved successfully.",
        'data_loaded': "Data loaded successfully.",
        'error_saving': "Error saving data.",
        'error_loading': "Error loading data or file not found. Using defaults.",
        'tab_setup': "⚙️ Setup & Calculate",
        'tab_analysis': "📊 Analysis & Simulation",
        'step1_header': "Step 1: Setup Services & Costs",
        'setup_intro': "Define services and review fixed costs from the sidebar.",
        'fixed_cost_summary': "Monthly Fixed Costs Summary",
        'fixed_cost_caption': "Total Fixed Costs are allocated based on service duration.",
        'manage_services_header': "Manage Services List",
        'manage_services_intro': """
            Use the table below to add, edit, or remove services. EGP currency assumed.
            - **Double-click a cell to edit.**
            - **Click '+' at the bottom to add a row.** Fill required fields (*).
            - **Select rows and press `Delete` key to remove.**
            - 'Service Name (Display)' must be unique.
            - `Duration (hr)` (>0) is critical for fixed cost allocation.
        """,
        'service_editor_key': "service_editor",
        'col_name_orig': "Service Name (Original)", 'col_name_orig_help': "Optional: Name in original language or internal code.",
        'col_name_disp': "Service Name (Display)*", 'col_name_disp_help': "Unique name for display/analysis (e.g., English). **Required**.",
        'col_exp_cases': "Exp. Cases/Month*", 'col_exp_cases_help': "Estimated procedures per month. **Required**.",
        'col_var_cost': "Var. Cost/Case (EGP)*", 'col_var_cost_help': "Direct cost per procedure (materials, lab fees). **Required**.",
        'col_duration': "Duration (hr)*", 'col_duration_help': "Average chair time in hours (e.g., 1.5). **Required & > 0**.",
        'validation_ok': "Service data looks valid.",
        'validation_warn': "Input Validation Error:",
        'step2_header': "Step 2: Calculate Pricing",
        'step2_intro': "Click below to calculate prices, costs, and KPIs based on the current setup.",
        'calculate_button': "💰 Calculate Detailed Pricing & KPIs (EGP)",
        'calculate_error': "Cannot calculate. Please fix validation errors.",
        'calculate_success': "Pricing calculated successfully! View results below and in the Analysis tab.",
        'calculate_fail': "Calculation failed. Check data.",
        'step3_header': "Step 3: Review Base Results",
        'results_kpi_header': "📊 Key Performance Indicators (Base Calculation)",
        'kpi_total_revenue': "Total Projected Revenue", 'kpi_total_revenue_help': "Sum of (Price/Case * Exp. Cases).",
        'kpi_total_profit': "Total Projected Profit", 'kpi_total_profit_help': "Total Revenue - Total Var Costs - Total Fixed Costs.",
        'kpi_overall_margin': "Overall Profit Margin", 'kpi_overall_margin_help': "(Total Profit / Total Revenue) * 100.",
        'kpi_be_revenue': "Overall Break-Even Revenue", 'kpi_be_revenue_help': "Total revenue needed to cover all costs (Total Fixed / Weighted Avg CM Ratio). 'N/A' if loss.",
        'kpi_avg_rev_hr': "Avg. Revenue per Hour", 'kpi_avg_rev_hr_help': "Total Revenue / Total Service Hours.",
        'kpi_avg_cm_hr': "Avg. Contrib. Margin / Hour", 'kpi_avg_cm_hr_help': "Total Contrib. Margin / Total Service Hours. Profit generation relative to time before fixed costs.",
        'kpi_total_hours': "Total Hours Projected", 'kpi_total_hours_help': "Sum of (Exp. Cases * Duration).",
        'kpi_num_services': "Number of Services Priced",
        'results_table_header': "📋 Detailed Pricing per Service (Base Calculation - EGP)",
        'results_tooltip_name': "Display name of the service.",
        'results_tooltip_cases': "Expected cases/month.",
        'results_tooltip_vc': "Direct variable cost/case.",
        'results_tooltip_dur': "Avg duration/case (hrs).",
        'results_tooltip_afc': "Portion of total fixed costs allocated based on service hours.",
        'results_tooltip_fcpc': "Allocated Fixed Cost / Expected Cases.",
        'results_tooltip_tcpc': "Variable Cost/Case + Fixed Cost/Case.",
        'results_tooltip_price': "Calc Price = Total Cost/Case * (1 + Base Margin %).",
        'results_tooltip_cm': "Contrib Margin/Case = Price - Variable Cost.",
        'results_tooltip_cmr': "Contrib Margin Ratio = (CM / Price) * 100.",
        'results_tooltip_be': "Break-Even (Cases) = Alloc Fixed Cost / CM per Case.",
        'download_button': "Download Results as CSV",
        'download_error': "No results to download.",
        'results_info': "Click 'Calculate' on Setup tab to view results.",
        'analysis_header': "Analysis & Simulation",
        'analysis_warning': "Please calculate pricing on the 'Setup & Calculate' tab first.",
        'analysis_tab_visual': "📈 Visual Analysis",
        'analysis_tab_sim': "💡 Scenario Simulation",
        'analysis_tab_sens': "📉 Sensitivity Analysis",
        'viz_profit_title': "Profitability Visuals",
        'viz_profit_chart_title': "Total Expected Profit by Service (EGP)", 'viz_profit_chart_ylabel': "Expected Profit (EGP)",
        'viz_profit_chart_tooltip': "Compares estimated total monthly profit per service (Revenue - Var Costs - Alloc Fixed Costs).",
        'viz_cm_chart_title': "Contribution Margin per Case by Service (EGP)", 'viz_cm_chart_ylabel': "Contrib. Margin (EGP)",
        'viz_cm_chart_tooltip': "Compares CM per Case (Price - Var Cost). Higher values cover fixed costs & profit better.",
        'viz_time_title': "Time & Efficiency Visuals",
        'viz_time_chart_title': "Total Expected Chair Time by Service", 'viz_time_chart_ylabel': "Total Hours",
        'viz_time_chart_tooltip': "Shows total estimated chair time (hours) per month per service.",
        'viz_cm_hr_chart_title': "Contribution Margin per Hour by Service (EGP)", 'viz_cm_hr_chart_ylabel': "CM per Hour (EGP)",
        'viz_cm_hr_chart_tooltip': "Compares CM generated per hour (CM per Case / Duration). Higher values = more efficient profit generators.",
        'plot_service': "Service", 'plot_nodata': "No data to plot.",
        'sim_header': "Scenario Simulation ('What-If')",
        'sim_intro': "Adjust parameters below to simulate changes based on the **last calculated results**. Does **not** change saved setup.",
        'sim_form_key': "simulation_form",
        'sim_global_adjust': "**Global Adjustments:**",
        'sim_fixed_cost_label': "Simulated Total Fixed Costs (EGP)", 'sim_fixed_cost_help': "Adjust total fixed costs. Base was {}.",
        'sim_margin_label': "Simulated Profit Margin (%)", 'sim_margin_help': "Adjust overall profit margin. Base was {}%.",
        'sim_specific_adjust': "**Specific Service Adjustment (Optional):**",
        'sim_select_service': "Select Service to Modify:", 'sim_option_none': "(None)",
        'sim_var_cost_label': "Sim Var Cost", 'sim_cases_label': "Sim Exp Cases", 'sim_duration_label': "Sim Duration",
        'sim_service_not_found': "Selected service not found in original input data.",
        'sim_run_button': "🚀 Run Simulation",
        'sim_input_invalid': "Simulation Input Data Invalid:",
        'sim_success': "Simulation complete!",
        'sim_fail': "Simulation calculation failed.",
        'sim_results_header': "Simulation Results vs. Base Calculation",
        'sim_kpi_compare': "**Overall KPI Comparison:**",
        'sim_kpi_revenue': "Total Revenue", 'sim_kpi_profit': "Total Profit", 'sim_kpi_margin': "Overall Margin", 'sim_kpi_rev_hr': "Avg Rev/Hour",
        'sim_detail_compare': "**Detailed Comparison for:** {}",
        'sim_detail_price': "Price/Case", 'sim_detail_cm': "CM/Case", 'sim_detail_bep': "BEP (Cases)", 'sim_detail_profit': "Exp. Profit (Service)",
        'sim_table_header': "**Full Simulated Pricing Details (EGP):**",
        'sim_col_service': "Service", 'sim_col_cases': "Cases", 'sim_col_vc': "Var Cost", 'sim_col_hrs': "Hrs",
        'sim_col_afc': "Alloc FixCost", 'sim_col_fcpc': "FixCost/Case", 'sim_col_tcpc': "TotalCost/Case",
        'sim_col_price': "Price/Case", 'sim_col_cm': "CM/Case", 'sim_col_cmr': "CM Ratio %", 'sim_col_bep': "BEP (Cases)",
        'sens_header': "Sensitivity Analysis (Case Volume Impact)",
        'sens_intro': "Analyze how **Price** and **Break-Even Point** change for one service if its case volume varies, using the **base calculated** allocation and margin.",
        'sens_select_service': "Select Service for Sensitivity Analysis:",
        'sens_no_service': "No services available in base results to analyze.",
        'sens_analyzing': "Analyzing:",
        'sens_min_cases': "Min Cases", 'sens_min_cases_help': "Lowest number of cases to test.",
        'sens_max_cases': "Max Cases", 'sens_max_cases_help': "Highest number of cases to test.",
        'sens_step': "Step", 'sens_step_help': "Increment between min and max cases.",
        'sens_error_range': "Max Cases must be > Min Cases.",
        'sens_error_step': "Invalid range/step.",
        'sens_plot_price_title': "Price Sensitivity vs. Cases", 'sens_plot_price_ylabel': "Calculated Price/Case (EGP)",
        'sens_plot_be_title': "Break-Even Point vs. Cases", 'sens_plot_be_ylabel': "Calculated BEP (Cases)",
        'sens_plot_xlabel': "Number of Cases", 'sens_plot_fig_title': "Sensitivity Analysis: Impact of Case Volume",
        'valid_err_empty': "Service data is empty. Please add services.",
        'valid_err_missing_cols': "Missing required columns: {}",
        'valid_err_empty_name': "Service Name (Display) cannot be empty.",
        'valid_err_duplicate_name': "Duplicate Service Names (Display) found: {}. Names must be unique.",
        'valid_err_non_numeric': "'{}' contains non-numeric or invalid values.",
        'valid_err_negative': "'{}' cannot be negative.",
        'valid_err_zero_dur': "'Duration (hr)' must be greater than zero.",
    },
    'ar': {
        # General
        'app_title': "لوحة تحكم تسعير عيادة الأسنان V3 (بالجنيه المصري)",
        'lang_select': "اختر اللغة",
        'sidebar_title': "إعدادات العيادة",
        'fixed_costs_header': "1. التكاليف الثابتة الشهرية (بالجنيه المصري)",
        'rent': "الإيجار", 'salaries': "رواتب الموظفين", 'utilities': "المرافق",
        'insurance': "التأمين والصيانة", 'marketing': "التسويق",
        'other_fixed': "تكاليف ثابتة أخرى", 'total_fixed_cost': "إجمالي التكاليف الثابتة الشهرية",
        'margin_header': "2. هامش الربح المستهدف الأساسي",
        'margin_label': "هامش الربح الأساسي (%)",
        'margin_help': "الربح المطلوب كنسبة مئوية *إضافية* على التكلفة الإجمالية للحالة (المتغيرة + الثابتة المخصصة). مثال: 30% تعني السعر = التكلفة الإجمالية * 1.30.",
        'margin_display': "هامش الربح المستهدف الأساسي",
        'reset_button': "إعادة الضبط إلى الإعدادات الافتراضية",
        'reset_confirm': "هل أنت متأكد؟ سيؤدي هذا إلى إعادة ضبط الإعدادات والخدمات إلى الوضع الافتراضي الأولي ولا يمكن التراجع عنه.",
        'data_saved': "تم حفظ البيانات بنجاح.",
        'data_loaded': "تم تحميل البيانات بنجاح.",
        'error_saving': "خطأ في حفظ البيانات.",
        'error_loading': "خطأ في تحميل البيانات أو الملف غير موجود. يتم استخدام الإعدادات الافتراضية.",
        'tab_setup': "⚙️ الإعداد والحساب",
        'tab_analysis': "📊 التحليل والمحاكاة",
        'step1_header': "الخطوة 1: إعداد الخدمات والتكاليف",
        'setup_intro': "حدد الخدمات التي تقدمها العيادة وراجع التكاليف الثابتة من الشريط الجانبي.",
        'fixed_cost_summary': "ملخص التكاليف الثابتة الشهرية",
        'fixed_cost_caption': "يتم توزيع إجمالي التكاليف الثابتة بناءً على مدة الخدمة.",
        'manage_services_header': "إدارة قائمة الخدمات",
        'manage_services_intro': """
            استخدم الجدول أدناه لإضافة أو تعديل أو إزالة الخدمات. العملة المفترضة هي الجنيه المصري.
            - **انقر نقرًا مزدوجًا على الخلية للتعديل.**
            - **انقر فوق '+' في الأسفل لإضافة صف جديد.** املأ الحقول المطلوبة (*).
            - **حدد الصفوف واضغط على مفتاح `Delete` للإزالة.**
            - يجب أن يكون 'اسم الخدمة (للعرض)' فريدًا لكل خدمة.
            - `المدة (ساعة)` (> 0) ضرورية لتوزيع التكاليف الثابتة.
        """,
        'service_editor_key': "service_editor_ar", # Use different key for AR if needed
        'col_name_orig': "اسم الخدمة (الأصلي)", 'col_name_orig_help': "اختياري: الاسم باللغة الأصلية أو الكود الداخلي.",
        'col_name_disp': "اسم الخدمة (للعرض)*", 'col_name_disp_help': "اسم فريد يستخدم للعرض والتحليل (مثلاً، بالإنجليزية أو العربية الواضحة). **مطلوب**.",
        'col_exp_cases': "الحالات المتوقعة/الشهر*", 'col_exp_cases_help': "العدد المقدر لإجراء هذه الخدمة شهريًا. **مطلوب**.",
        'col_var_cost': "التكلفة المتغيرة/الحالة (جنيه)*", 'col_var_cost_help': "التكلفة المباشرة لكل إجراء (مواد، رسوم معمل). **مطلوب**.",
        'col_duration': "المدة (ساعة)*", 'col_duration_help': "متوسط وقت الكرسي بالساعات اللازم للإجراء (مثال: 1.5). **مطلوب و > 0**.",
        'validation_ok': "بيانات الخدمة تبدو صالحة.",
        'validation_warn': "خطأ في التحقق من صحة الإدخال:",
        'step2_header': "الخطوة 2: حساب التسعير",
        'step2_intro': "انقر أدناه لحساب الأسعار والتكاليف ومؤشرات الأداء الرئيسية بناءً على الإعداد الحالي.",
        'calculate_button': "💰 حساب التسعير المفصل ومؤشرات الأداء (بالجنيه المصري)",
        'calculate_error': "لا يمكن الحساب. يرجى إصلاح أخطاء التحقق المذكورة أعلاه.",
        'calculate_success': "تم حساب التسعير بنجاح! اعرض النتائج أدناه وفي علامة التبويب 'التحليل'.",
        'calculate_fail': "فشل الحساب. تحقق من البيانات.",
        'step3_header': "الخطوة 3: مراجعة النتائج الأساسية",
        'results_kpi_header': "📊 مؤشرات الأداء الرئيسية (الحساب الأساسي)",
        'kpi_total_revenue': "إجمالي الإيرادات المتوقعة", 'kpi_total_revenue_help': "مجموع (السعر/الحالة * الحالات المتوقعة).",
        'kpi_total_profit': "إجمالي الربح المتوقع", 'kpi_total_profit_help': "إجمالي الإيرادات - إجمالي التكاليف المتغيرة - إجمالي التكاليف الثابتة.",
        'kpi_overall_margin': "هامش الربح الإجمالي", 'kpi_overall_margin_help': "(إجمالي الربح / إجمالي الإيرادات) * 100.",
        'kpi_be_revenue': "إجمالي إيرادات نقطة التعادل", 'kpi_be_revenue_help': "الإيرادات الإجمالية اللازمة لتغطية جميع التكاليف (التكاليف الثابتة / متوسط نسبة هامش المساهمة المرجح). 'N/A' إذا كانت خسارة.",
        'kpi_avg_rev_hr': "متوسط الإيرادات لكل ساعة", 'kpi_avg_rev_hr_help': "إجمالي الإيرادات / إجمالي ساعات الخدمة.",
        'kpi_avg_cm_hr': "متوسط هامش المساهمة / ساعة", 'kpi_avg_cm_hr_help': "إجمالي هامش المساهمة / إجمالي ساعات الخدمة. توليد الربح بالنسبة للوقت قبل التكاليف الثابتة.",
        'kpi_total_hours': "إجمالي الساعات المتوقعة", 'kpi_total_hours_help': "مجموع (الحالات المتوقعة * المدة).",
        'kpi_num_services': "عدد الخدمات المسعرة",
        'results_table_header': "📋 التسعير المفصل لكل خدمة (الحساب الأساسي - بالجنيه المصري)",
        'results_tooltip_name': "اسم الخدمة المعروض.",
        'results_tooltip_cases': "الحالات المتوقعة شهريًا.",
        'results_tooltip_vc': "التكلفة المتغيرة المباشرة لكل حالة.",
        'results_tooltip_dur': "متوسط المدة لكل حالة (بالساعات).",
        'results_tooltip_afc': "الجزء المخصص من إجمالي التكاليف الثابتة بناءً على ساعات الخدمة.",
        'results_tooltip_fcpc': "التكلفة الثابتة المخصصة / الحالات المتوقعة.",
        'results_tooltip_tcpc': "التكلفة المتغيرة/الحالة + التكلفة الثابتة/الحالة.",
        'results_tooltip_price': "السعر المحسوب = التكلفة الإجمالية/الحالة * (1 + هامش الربح الأساسي %).",
        'results_tooltip_cm': "هامش المساهمة لكل حالة = السعر/الحالة - التكلفة المتغيرة/الحالة.",
        'results_tooltip_cmr': "نسبة هامش المساهمة = (هامش المساهمة / السعر لكل حالة) * 100.",
        'results_tooltip_be': "نقطة التعادل (الحالات) = التكلفة الثابتة المخصصة / هامش المساهمة لكل حالة.",
        'download_button': "تنزيل النتائج كملف CSV",
        'download_error': "لا توجد نتائج لتنزيلها.",
        'results_info': "انقر فوق 'حساب' في علامة تبويب الإعداد لعرض النتائج هنا.",
        'analysis_header': "التحليل والمحاكاة",
        'analysis_warning': "يرجى حساب التسعير في علامة التبويب 'الإعداد والحساب' أولاً لتمكين التحليل والمحاكاة.",
        'analysis_tab_visual': "📈 التحليل المرئي",
        'analysis_tab_sim': "💡 محاكاة السيناريو",
        'analysis_tab_sens': "📉 تحليل الحساسية",
        'viz_profit_title': "المرئيات المتعلقة بالربحية",
        'viz_profit_chart_title': "إجمالي الربح المتوقع حسب الخدمة (بالجنيه المصري)", 'viz_profit_chart_ylabel': "الربح المتوقع (جنيه)",
        'viz_profit_chart_tooltip': "يقارن إجمالي الربح الشهري المقدر لكل خدمة (الإيرادات - التكاليف المتغيرة - التكاليف الثابتة المخصصة).",
        'viz_cm_chart_title': "هامش المساهمة لكل حالة حسب الخدمة (بالجنيه المصري)", 'viz_cm_chart_ylabel': "هامش المساهمة (جنيه)",
        'viz_cm_chart_tooltip': "يقارن هامش المساهمة لكل حالة (السعر - التكلفة المتغيرة). القيم الأعلى تساهم بشكل أكبر في تغطية التكاليف الثابتة وتحقيق الربح.",
        'viz_time_title': "المرئيات المتعلقة بالوقت والكفاءة",
        'viz_time_chart_title': "إجمالي وقت الكرسي المتوقع حسب الخدمة", 'viz_time_chart_ylabel': "إجمالي الساعات",
        'viz_time_chart_tooltip': "يعرض إجمالي وقت الكرسي المقدر (بالساعات) شهريًا لكل خدمة.",
        'viz_cm_hr_chart_title': "هامش المساهمة لكل ساعة حسب الخدمة (بالجنيه المصري)", 'viz_cm_hr_chart_ylabel': "هامش المساهمة/ساعة (جنيه)",
        'viz_cm_hr_chart_tooltip': "يقارن هامش المساهمة المتولد لكل ساعة من وقت الكرسي (هامش المساهمة للحالة / المدة للحالة). الخدمات ذات هامش مساهمة/ساعة مرتفع تعتبر مولدات ربح فعالة جدًا.",
        'plot_service': "الخدمة", 'plot_nodata': "لا توجد بيانات للرسم.",
        'sim_header': "محاكاة السيناريو ('ماذا لو')",
        'sim_intro': "اضبط المعلمات أدناه لمحاكاة التغييرات بناءً على **آخر النتائج المحسوبة**. هذا **لا** يغير الإعداد المحفوظ.",
        'sim_form_key': "simulation_form_ar",
        'sim_global_adjust': "**التعديلات العامة:**",
        'sim_fixed_cost_label': "إجمالي التكاليف الثابتة المحاكاة (جنيه)", 'sim_fixed_cost_help': "اضبط إجمالي التكاليف الثابتة. الأساس كان {}.",
        'sim_margin_label': "هامش الربح المحاكاة (%)", 'sim_margin_help': "اضبط هامش الربح الإجمالي. الأساس كان {}%.",
        'sim_specific_adjust': "**تعديل خدمة محددة (اختياري):**",
        'sim_select_service': "اختر الخدمة للتعديل:", 'sim_option_none': "(لا شيء)",
        'sim_var_cost_label': "تكلفة متغيرة محاكاة", 'sim_cases_label': "حالات متوقعة محاكاة", 'sim_duration_label': "مدة محاكاة",
        'sim_service_not_found': "الخدمة المحددة غير موجودة في بيانات الإدخال الأصلية.",
        'sim_run_button': "🚀 تشغيل المحاكاة",
        'sim_input_invalid': "بيانات إدخال المحاكاة غير صالحة:",
        'sim_success': "اكتملت المحاكاة!",
        'sim_fail': "فشل حساب المحاكاة.",
        'sim_results_header': "نتائج المحاكاة مقابل الحساب الأساسي",
        'sim_kpi_compare': "**مقارنة مؤشرات الأداء الرئيسية الإجمالية:**",
        'sim_kpi_revenue': "إجمالي الإيرادات", 'sim_kpi_profit': "إجمالي الربح", 'sim_kpi_margin': "الهامش الإجمالي", 'sim_kpi_rev_hr': "متوسط الإيراد/ساعة",
        'sim_detail_compare': "**مقارنة تفصيلية لـ:** {}",
        'sim_detail_price': "السعر/الحالة", 'sim_detail_cm': "هامش مساهمة/الحالة", 'sim_detail_bep': "نقطة التعادل (حالات)", 'sim_detail_profit': "الربح المتوقع (للخدمة)",
        'sim_table_header': "**تفاصيل التسعير المحاكاة الكاملة (بالجنيه المصري):**",
        'sim_col_service': "الخدمة", 'sim_col_cases': "الحالات", 'sim_col_vc': "تكلفة متغيرة", 'sim_col_hrs': "ساعات",
        'sim_col_afc': "تكلفة ثابتة مخصصة", 'sim_col_fcpc': "تكلفة ثابتة/حالة", 'sim_col_tcpc': "تكلفة إجمالية/حالة",
        'sim_col_price': "السعر/حالة", 'sim_col_cm': "هامش مساهمة/حالة", 'sim_col_cmr': "نسبة هامش مساهمة %", 'sim_col_bep': "نقطة التعادل (حالات)",
        'sens_header': "تحليل الحساسية (تأثير حجم الحالات)",
        'sens_intro': "حلل كيف يتغير **السعر** و **نقطة التعادل** لخدمة واحدة إذا تغير حجم حالاتها، باستخدام التخصيص والهامش **المحسوبين أساسًا**.",
        'sens_select_service': "اختر الخدمة لتحليل الحساسية:",
        'sens_no_service': "لا توجد خدمات متاحة في النتائج الأساسية للتحليل.",
        'sens_analyzing': "تحليل:",
        'sens_min_cases': "أدنى عدد حالات", 'sens_min_cases_help': "أقل عدد من الحالات للاختبار.",
        'sens_max_cases': "أقصى عدد حالات", 'sens_max_cases_help': "أعلى عدد من الحالات للاختبار.",
        'sens_step': "الخطوة", 'sens_step_help': "الزيادة بين أدنى وأقصى عدد حالات.",
        'sens_error_range': "يجب أن يكون أقصى عدد حالات > أدنى عدد حالات.",
        'sens_error_step': "نطاق/خطوة غير صالحة.",
        'sens_plot_price_title': "حساسية السعر مقابل الحالات", 'sens_plot_price_ylabel': "السعر المحسوب/الحالة (جنيه)",
        'sens_plot_be_title': "نقطة التعادل مقابل الحالات", 'sens_plot_be_ylabel': "نقطة التعادل المحسوبة (حالات)",
        'sens_plot_xlabel': "عدد الحالات", 'sens_plot_fig_title': "تحليل الحساسية: تأثير حجم الحالات",
        'valid_err_empty': "بيانات الخدمة فارغة. الرجاء إضافة خدمات.",
        'valid_err_missing_cols': "الأعمدة المطلوبة مفقودة: {}",
        'valid_err_empty_name': "لا يمكن ترك اسم الخدمة (للعرض) فارغًا.",
        'valid_err_duplicate_name': "تم العثور على أسماء خدمة (للعرض) مكررة: {}. يجب أن تكون الأسماء فريدة.",
        'valid_err_non_numeric': "'{}' يحتوي على قيم غير رقمية أو غير صالحة.",
        'valid_err_negative': "'{}' لا يمكن أن يكون سالبًا.",
        'valid_err_zero_dur': "يجب أن تكون 'المدة (ساعة)' أكبر من الصفر.",
    }
}

# --- Helper Functions ---

def get_text(key: str) -> str:
    """Retrieves text string in the currently selected language."""
    lang = st.session_state.get(STATE_LANG, 'en') # Default to English if not set
    return LANG_STRINGS.get(lang, {}).get(key, f"<{key}_NOT_FOUND>")

def egp_format(value: float) -> str:
    """Formats a float as EGP currency."""
    if pd.isna(value) or not np.isfinite(value):
        return "N/A"
    try:
        # Format with commas and no decimal places for EGP
        return f"{value:,.0f} EGP"
    except (TypeError, ValueError):
        return "N/A"

def get_default_settings() -> Dict[str, Any]:
    """Returns the default clinic settings."""
    return {
        "rent": 15000.0,
        "salaries": 25000.0,
        "utilities": 5000.0,
        "insurance": 2000.0,
        "marketing": 1500.0,
        "other_fixed": 1000.0,
        "base_margin": 0.35 # 35% default margin
    }

def get_default_services() -> pd.DataFrame:
    """Returns the default services DataFrame tailored for Egypt."""
    default_services_data = [
        # Common Egyptian dental procedures with estimated costs/durations
        {COL_NAME: "تنظيف وتلميع", COL_NAME_EN: "Scaling & Polishing", COL_EXPECTED_CASES: 80, COL_VAR_COST: 100.0, COL_DURATION: 0.75},
        {COL_NAME: "حشو كومبوزيت", COL_NAME_EN: "Composite Filling", COL_EXPECTED_CASES: 60, COL_VAR_COST: 200.0, COL_DURATION: 1.0},
        {COL_NAME: "حشو أملغم", COL_NAME_EN: "Amalgam Filling", COL_EXPECTED_CASES: 20, COL_VAR_COST: 150.0, COL_DURATION: 0.75},
        {COL_NAME: "علاج عصب (ضرس)", COL_NAME_EN: "Root Canal Therapy (Molar)", COL_EXPECTED_CASES: 30, COL_VAR_COST: 450.0, COL_DURATION: 2.0},
        {COL_NAME: "خلع (عادي)", COL_NAME_EN: "Simple Extraction", COL_EXPECTED_CASES: 50, COL_VAR_COST: 80.0, COL_DURATION: 0.5},
        {COL_NAME: "خلع (جراحي)", COL_NAME_EN: "Surgical Extraction", COL_EXPECTED_CASES: 15, COL_VAR_COST: 300.0, COL_DURATION: 1.5},
        {COL_NAME: "تركيبة بورسلين", COL_NAME_EN: "Porcelain Crown (PFM)", COL_EXPECTED_CASES: 25, COL_VAR_COST: 600.0, COL_DURATION: 1.5}, # Duration per visit, might need multiple
        {COL_NAME: "تركيبة زيركون", COL_NAME_EN: "Zirconia Crown", COL_EXPECTED_CASES: 15, COL_VAR_COST: 1000.0, COL_DURATION: 1.5}, # Duration per visit
        {COL_NAME: "تبييض الأسنان (عيادة)", COL_NAME_EN: "In-Office Teeth Whitening", COL_EXPECTED_CASES: 20, COL_VAR_COST: 700.0, COL_DURATION: 1.5},
        {COL_NAME: "زراعة أسنان (جراحة فقط)", COL_NAME_EN: "Dental Implant (Surgery)", COL_EXPECTED_CASES: 10, COL_VAR_COST: 2500.0, COL_DURATION: 2.0},
    ]
    df = pd.DataFrame(default_services_data)
    # Ensure correct types
    for col, dtype in {COL_EXPECTED_CASES: int, COL_VAR_COST: float, COL_DURATION: float}.items():
        try: df[col] = df[col].astype(dtype)
        except Exception: pass # Ignore errors if column doesn't exist initially
    return df

def load_app_data(file_path: str) -> Tuple[Dict[str, Any], pd.DataFrame]:
    """Loads settings and services DataFrame from a JSON file."""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            settings = data.get("settings", get_default_settings())
            services_list = data.get("services", get_default_services().to_dict(orient='records'))
            services_df = pd.DataFrame(services_list)
            # Ensure correct dtypes after loading from JSON (which might lose them)
            for col, dtype in {COL_EXPECTED_CASES: int, COL_VAR_COST: float, COL_DURATION: float}.items():
                 if col in services_df.columns:
                    services_df[col] = pd.to_numeric(services_df[col], errors='coerce') # Coerce first
                    if dtype == int:
                       services_df[col] = services_df[col].fillna(0).astype(int) # Fill NA for int conversion
                    else:
                       services_df[col] = services_df[col].astype(float) # Can handle NaN

            # Ensure all default columns exist
            default_cols = get_default_services().columns
            for col in default_cols:
                if col not in services_df.columns:
                    # Add missing columns with appropriate default type/value
                    if col in [COL_NAME, COL_NAME_EN]: services_df[col] = ""
                    elif col == COL_EXPECTED_CASES: services_df[col] = 0
                    else: services_df[col] = 0.0
            services_df = services_df[default_cols] # Ensure correct column order

            # Don't show success message on every run, only maybe on first load or reset
            # st.success(f"{get_text('data_loaded')} ({os.path.basename(file_path)})")
            return settings, services_df
        else:
            st.info(f"{get_text('error_loading')} ({os.path.basename(file_path)})")
            return get_default_settings(), get_default_services()
    except Exception as e:
        st.error(f"{get_text('error_loading')}: {e}")
        return get_default_settings(), get_default_services()

def save_app_data(file_path: str, settings: Dict[str, Any], services_df: pd.DataFrame):
    """Saves settings and services DataFrame to a JSON file."""
    try:
        data_to_save = {
            "settings": settings,
            # Convert DataFrame to list of dicts for JSON compatibility
            "services": services_df.to_dict(orient='records')
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        st.toast(get_text('data_saved'), icon="💾") # Use toast for less intrusive message
    except Exception as e:
        st.error(f"{get_text('error_saving')}: {e}")

def initialize_session_state():
    """Initializes session state, loading data from file if exists."""
    if STATE_LANG not in st.session_state:
        st.session_state[STATE_LANG] = 'ar' # Default to Arabic

    if STATE_SETTINGS not in st.session_state or STATE_SERVICES_DF_INPUT not in st.session_state:
        settings, services_df = load_app_data(DATA_FILE)
        st.session_state[STATE_SETTINGS] = settings
        st.session_state[STATE_SERVICES_DF_INPUT] = services_df

    # Initialize other state variables if they don't exist
    if STATE_RESULTS_DF not in st.session_state: st.session_state[STATE_RESULTS_DF] = None
    if STATE_CALCULATED not in st.session_state: st.session_state[STATE_CALCULATED] = False
    if STATE_SIMULATION_RESULTS_DF not in st.session_state: st.session_state[STATE_SIMULATION_RESULTS_DF] = None

def validate_service_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validates the service data DataFrame before calculation."""
    errors = []
    if df is None or df.empty:
        errors.append(get_text('valid_err_empty'))
        return False, errors

    required_cols = [COL_NAME_EN, COL_EXPECTED_CASES, COL_VAR_COST, COL_DURATION]
    present_cols = df.columns.tolist()
    missing_cols = [col for col in required_cols if col not in present_cols]
    if missing_cols:
        errors.append(get_text('valid_err_missing_cols').format(', '.join(missing_cols)))
        # Stop further validation if core columns are missing
        return False, errors

    # Check for null/empty display names (convert to string first)
    if df[COL_NAME_EN].astype(str).isnull().any() or (df[COL_NAME_EN].astype(str).str.strip() == '').any():
        errors.append(get_text('valid_err_empty_name'))

    # Check for duplicate display names (case-insensitive check is safer)
    # Ensure the column exists before checking duplicates
    if COL_NAME_EN in df.columns:
        duplicates = df[df.duplicated(subset=[COL_NAME_EN], keep=False)][COL_NAME_EN].unique()
        if len(duplicates) > 0:
            errors.append(get_text('valid_err_duplicate_name').format(', '.join(duplicates)))

    # Convert numeric columns, coercing errors, then check validity
    numeric_cols = [COL_EXPECTED_CASES, COL_VAR_COST, COL_DURATION]
    for col in numeric_cols:
         if col in df.columns: # Check column exists
            # Try conversion, store result temporarily
            numeric_series = pd.to_numeric(df[col], errors='coerce')

            if numeric_series.isnull().any():
                errors.append(get_text('valid_err_non_numeric').format(col))
            else:
                # Check for negative values only if conversion succeeded
                if col in [COL_EXPECTED_CASES, COL_VAR_COST]:
                    if (numeric_series < 0).any():
                        errors.append(get_text('valid_err_negative').format(col))
                elif col == COL_DURATION:
                    if (numeric_series <= 0).any():
                        errors.append(get_text('valid_err_zero_dur')) # Duration must be > 0

    return not errors, errors

def calculate_detailed_pricing(services_df_input: pd.DataFrame, total_fixed_cost: float, margin: float) -> Optional[pd.DataFrame]:
    """Calculates detailed pricing and related metrics AFTER validation."""
    if services_df_input is None or services_df_input.empty:
        return None

    calc_df = services_df_input.copy()

    # --- Ensure Correct Data Types for Calculation ---
    # Re-apply coercion here as data might come directly from editor
    try:
        if COL_EXPECTED_CASES in calc_df.columns:
            calc_df[COL_EXPECTED_CASES] = pd.to_numeric(calc_df[COL_EXPECTED_CASES], errors='coerce').fillna(0).astype(int)
        if COL_VAR_COST in calc_df.columns:
            calc_df[COL_VAR_COST] = pd.to_numeric(calc_df[COL_VAR_COST], errors='coerce').fillna(0.0).astype(float)
        if COL_DURATION in calc_df.columns:
            calc_df[COL_DURATION] = pd.to_numeric(calc_df[COL_DURATION], errors='coerce').fillna(0.1).astype(float) # Fill duration NA with small positive
            # Ensure duration is positive after potential fillna
            calc_df[COL_DURATION] = calc_df[COL_DURATION].apply(lambda x: max(x, 0.01)) # Ensure duration > 0
    except Exception as e:
         st.error(f"Internal Error: Data type conversion failed: {e}")
         return None

    # Check if required columns for calculation are present after conversion attempt
    required_calc_cols = [COL_EXPECTED_CASES, COL_VAR_COST, COL_DURATION]
    if not all(col in calc_df.columns for col in required_calc_cols):
         st.error("Internal Error: Missing required columns for calculation.")
         return None

    # --- Core Calculations ---
    # Calculate total hours per service, handle potential zero cases/duration
    calc_df[COL_SERVICE_HOURS] = calc_df[COL_EXPECTED_CASES] * calc_df[COL_DURATION]
    total_service_hours = calc_df[COL_SERVICE_HOURS].sum()

    # Allocate fixed costs based on service hours share
    if total_service_hours <= 0:
        # Avoid division by zero if no hours projected
        calc_df[COL_ALLOC_FIXED_COST] = 0.0
        calc_df[COL_FIXED_COST_PER_CASE] = 0.0
    else:
        calc_df[COL_ALLOC_FIXED_COST] = total_fixed_cost * (calc_df[COL_SERVICE_HOURS] / total_service_hours)
        # Calculate fixed cost per case, handle zero expected cases
        calc_df[COL_FIXED_COST_PER_CASE] = np.where(
            calc_df[COL_EXPECTED_CASES] > 0,
            calc_df[COL_ALLOC_FIXED_COST] / calc_df[COL_EXPECTED_CASES],
            0.0 # Assign 0 if no cases expected
        )

    # Calculate total cost and price
    calc_df[COL_TOTAL_COST_PER_CASE] = calc_df[COL_VAR_COST] + calc_df[COL_FIXED_COST_PER_CASE]
    calc_df[COL_PRICE_PER_CASE] = calc_df[COL_TOTAL_COST_PER_CASE] * (1.0 + margin)

    # Calculate Contribution Margin
    calc_df[COL_CONTRIB_MARGIN] = calc_df[COL_PRICE_PER_CASE] - calc_df[COL_VAR_COST]

    # --- Additional Metrics ---
    # Contribution Margin Ratio (%)
    calc_df[COL_CONTRIB_MARGIN_RATIO] = np.where(
        calc_df[COL_PRICE_PER_CASE] > 0,
        (calc_df[COL_CONTRIB_MARGIN] / calc_df[COL_PRICE_PER_CASE]) * 100.0,
        0.0 # Avoid division by zero if price is zero
    )
    # Break-Even Point (Cases)
    calc_df[COL_BREAK_EVEN] = np.where(
        calc_df[COL_CONTRIB_MARGIN] > 0,
        calc_df[COL_ALLOC_FIXED_COST] / calc_df[COL_CONTRIB_MARGIN],
        float('inf') # Infinite BEP if CM is zero or negative
    )
    # Expected Revenue and Profit
    calc_df[COL_REVENUE_EXPECTED] = calc_df[COL_PRICE_PER_CASE] * calc_df[COL_EXPECTED_CASES]
    calc_df[COL_PROFIT_EXPECTED] = (calc_df[COL_CONTRIB_MARGIN] * calc_df[COL_EXPECTED_CASES]) - calc_df[COL_ALLOC_FIXED_COST]

    # Revenue and CM per Hour
    calc_df[COL_REVENUE_PER_HOUR] = np.where(
        calc_df[COL_DURATION] > 0,
        calc_df[COL_PRICE_PER_CASE] / calc_df[COL_DURATION],
        0.0
    )
    calc_df[COL_CM_PER_HOUR] = np.where(
        calc_df[COL_DURATION] > 0,
        calc_df[COL_CONTRIB_MARGIN] / calc_df[COL_DURATION],
        0.0
    )

    return calc_df

# ---!!! CORRECTED PLOT FUNCTION (Attempt 2) !!!---
def plot_bar_chart(df: pd.DataFrame, x_col: str, y_col: str, title_key: str, ylabel_key: str, tooltip_key: str, sort_by_y=True, color='skyblue'):
    """Helper to create a formatted bar chart using Pandas plotting and explicit ticks."""
    if df is None or df.empty or x_col not in df.columns or y_col not in df.columns:
        st.caption(get_text('plot_nodata'))
        return None

    # Ensure y_col is numeric for plotting and sorting
    df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
    plot_df = df.dropna(subset=[y_col]).copy()

    if plot_df.empty:
        st.caption(get_text('plot_nodata'))
        return None

    if sort_by_y:
        plot_df = plot_df.sort_values(by=y_col, ascending=False)

    fig, ax = plt.subplots(figsize=(10, 7)) # Adjust size as needed

    # Use Pandas plotting method directly on the axes
    # IMPORTANT: Reset index here so that bar locations are 0, 1, 2...
    plot_df.reset_index(drop=True).plot(kind='bar', x=x_col, y=y_col, ax=ax, color=color, legend=False)

    # Set title and labels
    ax.set_title(get_text(title_key), fontsize=14, fontweight='bold')
    ax.set_xlabel(get_text('plot_service'), fontsize=12)
    ax.set_ylabel(get_text(ylabel_key), fontsize=12)

    # --- Explicitly set X-axis ticks and labels ---
    # Get locations (0, 1, 2... for the number of bars)
    tick_locations = np.arange(len(plot_df))
    # Get labels from the dataframe column
    tick_labels = plot_df[x_col].tolist()

    # Set the ticks and apply rotation/formatting directly to labels
    ax.set_xticks(tick_locations)
    ax.set_xticklabels(tick_labels, rotation=45, ha='right', fontsize=10)
    # --- End of explicit X-axis tick setting ---

    # Keep Y-axis tick parameters (this seemed fine)
    ax.tick_params(axis='y', labelsize=10)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format(int(x), ',')))
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    # Add bar labels
    if ax.containers:
        try:
            ax.bar_label(ax.containers[0], fmt='{:,.0f}', fontsize=9, padding=3)
        except IndexError:
             st.warning("Could not add bar labels to plot.")

    # Add tooltip
    tooltip_text = get_text(tooltip_key)
    fig.text(0.5, -0.15, tooltip_text, ha='center', va='bottom', fontsize=9, style='italic', wrap=True,
             bbox=dict(boxstyle='round,pad=0.3', fc='lightyellow', alpha=0.6))

    # Adjust layout slightly more if needed
    fig.tight_layout(rect=[0, 0.05, 1, 0.95])

    return fig
# ---!!! END OF CORRECTED PLOT FUNCTION !!!---


# Sensitivity calculation remains the same logic
def calculate_sensitivity(variable_cost: float, allocated_fixed_cost: float, margin: float, cases_range: List[int]) -> Tuple[List[float], List[float]]:
    prices = []
    break_evens = []
    for cases in cases_range:
        # Ensure cases is treated as numeric
        try:
            num_cases = int(cases)
            if num_cases <= 0:
                price, be = float('inf'), float('inf')
            else:
                fixed_cost_per_case = allocated_fixed_cost / num_cases
                total_cost = variable_cost + fixed_cost_per_case
                price = total_cost * (1 + margin)
                contribution_margin = price - variable_cost
                be = allocated_fixed_cost / contribution_margin if contribution_margin > 0 else float('inf')
        except (ValueError, TypeError):
             price, be = float('nan'), float('nan') # Handle non-numeric case input gracefully

        prices.append(price)
        break_evens.append(be)
    return prices, break_evens

# Sensitivity plot function updated for language
def plot_sensitivity(cases_range: List[int], prices: List[float], break_evens: List[float]) -> Optional[plt.Figure]:
    # Filter out non-finite values for plotting range determination
    finite_prices = [p for p in prices if np.isfinite(p)]
    finite_bes = [be for be in break_evens if np.isfinite(be)]

    if not finite_prices and not finite_bes:
        st.warning("No valid sensitivity data points to plot.")
        return None

    fig, axs = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True) # Use constrained layout

    # Plot Price Sensitivity
    axs[0].plot(cases_range, prices, marker='o', linestyle='-', color='royalblue')
    axs[0].set_title(get_text('sens_plot_price_title'))
    axs[0].set_xlabel(get_text('sens_plot_xlabel'))
    axs[0].set_ylabel(get_text('sens_plot_price_ylabel'))
    axs[0].grid(True, linestyle='--', alpha=0.6)
    axs[0].ticklabel_format(style='plain', axis='y')
    if finite_prices: # Set Y limit based on actual data
        min_p, max_p = min(finite_prices), max(finite_prices)
        axs[0].set_ylim(bottom=min_p * 0.9, top=max_p * 1.1)
    else:
         axs[0].set_ylim(bottom=0)

    # Plot Break-Even Sensitivity
    axs[1].plot(cases_range, break_evens, marker='x', linestyle='--', color='crimson')
    axs[1].set_title(get_text('sens_plot_be_title'))
    axs[1].set_xlabel(get_text('sens_plot_xlabel'))
    axs[1].set_ylabel(get_text('sens_plot_be_ylabel'))
    axs[1].grid(True, linestyle='--', alpha=0.6)
    axs[1].ticklabel_format(style='plain', axis='y')
    # Set sensible Y limits for Break-Even
    if finite_bes:
        axs[1].set_ylim(bottom=0, top=max(finite_bes) * 1.15 if finite_bes else 10)
    else:
        axs[1].set_ylim(bottom=0, top=10) # Default small range if no finite BEPs

    fig.suptitle(get_text('sens_plot_fig_title'), fontsize=14)
    # constrained_layout usually handles overlap, but adjust if needed
    # fig.tight_layout(rect=[0, 0, 1, 0.95])
    return fig

def convert_df_to_csv(df: pd.DataFrame) -> bytes:
    """Converts DataFrame to CSV bytes for downloading."""
    output = io.BytesIO()
    # Use utf-8-sig for better Excel compatibility with Arabic
    df.to_csv(output, index=False, encoding='utf-8-sig')
    return output.getvalue()

# --- Streamlit App UI ---
st.set_page_config(layout="wide", page_title="Dental Pricing Dashboard V3 (EGP)")

# Initialize state (MUST be first Streamlit call after config/imports)
initialize_session_state()

# --- Language Selection ---
# Place language selector at the top of the sidebar
lang_options = {'English': 'en', 'العربية': 'ar'}
selected_lang_label = st.sidebar.radio(
    get_text('lang_select'),
    options=list(lang_options.keys()),
    index=list(lang_options.values()).index(st.session_state[STATE_LANG]), # Set default based on state
    key='lang_radio',
    horizontal=True,
)
# Update state immediately if language changes
if lang_options[selected_lang_label] != st.session_state[STATE_LANG]:
    st.session_state[STATE_LANG] = lang_options[selected_lang_label]
    st.rerun() # Rerun to apply new language immediately

# Set app title using selected language
st.title(get_text('app_title'))


# --- Sidebar ---
with st.sidebar:
    st.image("https://img.icons8.com/?size=100&id=p8J6hLVdN_V9&format=png&color=000000", width=64) # Tooth icon
    st.header(get_text('sidebar_title'))

    # Use a dictionary to manage settings in session state for easier saving/loading
    # Make a deep copy to avoid modifying state directly before check
    current_settings = st.session_state[STATE_SETTINGS].copy()
    settings_changed = False # Flag to track if we need to save

    with st.expander(get_text('fixed_costs_header'), expanded=True):
        # Use values from the copied dictionary
        rent = st.number_input(get_text('rent'), min_value=0.0, value=float(current_settings['rent']), step=500.0, key="rent_sb", format="%f")
        salaries = st.number_input(get_text('salaries'), min_value=0.0, value=float(current_settings['salaries']), step=500.0, key="salaries_sb", format="%f")
        utilities = st.number_input(get_text('utilities'), min_value=0.0, value=float(current_settings['utilities']), step=200.0, key="utilities_sb", format="%f")
        insurance = st.number_input(get_text('insurance'), min_value=0.0, value=float(current_settings['insurance']), step=100.0, key="insurance_sb", format="%f")
        marketing = st.number_input(get_text('marketing'), min_value=0.0, value=float(current_settings['marketing']), step=100.0, key="marketing_sb", format="%f")
        other_fixed = st.number_input(get_text('other_fixed'), min_value=0.0, value=float(current_settings['other_fixed']), step=100.0, key="other_fixed_sb", format="%f")

        current_total_fixed_cost = rent + salaries + utilities + insurance + marketing + other_fixed
        st.metric(label=f"**{get_text('total_fixed_cost')}**", value=egp_format(current_total_fixed_cost))

        # Check against original state values before updating copied dict
        if (rent != st.session_state[STATE_SETTINGS]['rent'] or
            salaries != st.session_state[STATE_SETTINGS]['salaries'] or
            utilities != st.session_state[STATE_SETTINGS]['utilities'] or
            insurance != st.session_state[STATE_SETTINGS]['insurance'] or
            marketing != st.session_state[STATE_SETTINGS]['marketing'] or
            other_fixed != st.session_state[STATE_SETTINGS]['other_fixed']):

            # Update the temporary dictionary
            current_settings['rent'] = rent
            current_settings['salaries'] = salaries
            current_settings['utilities'] = utilities
            current_settings['insurance'] = insurance
            current_settings['marketing'] = marketing
            current_settings['other_fixed'] = other_fixed
            settings_changed = True

    with st.expander(get_text('margin_header'), expanded=True):
        # Use value from copied dictionary for slider default
        current_margin_percentage = st.slider(
            get_text('margin_label'), 0, 200,
            int(current_settings.get('base_margin', 0.35) * 100), # Use .get for safety
            5,
            key="margin_slider_sb",
            help=get_text('margin_help'))
        current_margin = current_margin_percentage / 100.0
        st.info(f"{get_text('margin_display')}: {current_margin_percentage}%", icon="🎯")

        # Check against original state before updating copied dict
        if current_margin != st.session_state[STATE_SETTINGS].get('base_margin', 0.35):
             current_settings['base_margin'] = current_margin # Update temp dict
             settings_changed = True

    # Save settings only if they changed
    if settings_changed:
        st.session_state[STATE_SETTINGS] = current_settings # Update state with modified dict
        save_app_data(DATA_FILE, st.session_state[STATE_SETTINGS], st.session_state[STATE_SERVICES_DF_INPUT]) # Save all

    st.divider()
    # Reset button
    if st.button(get_text('reset_button'), key="reset_btn"):
        # Add confirmation checkbox for safety
        confirm = st.checkbox(get_text('reset_confirm'), key="reset_confirm_cb")
        if confirm:
            # Clear relevant session state keys
            keys_to_reset = [STATE_SETTINGS, STATE_SERVICES_DF_INPUT, STATE_RESULTS_DF, STATE_CALCULATED, STATE_SIMULATION_RESULTS_DF]
            for key in keys_to_reset:
                if key in st.session_state:
                    del st.session_state[key]
            # Delete the data file to ensure reload uses defaults
            if os.path.exists(DATA_FILE):
                try:
                    os.remove(DATA_FILE)
                    st.success(f"Removed data file '{DATA_FILE}'.")
                except Exception as e:
                    st.warning(f"Could not delete data file '{DATA_FILE}': {e}")
            st.success("Reset complete. Rerunning...")
            st.rerun() # Rerun the app to re-initialize with defaults

# --- Main Content Tabs ---
tab1, tab2 = st.tabs([
    get_text('tab_setup'),
    get_text('tab_analysis')
])

# === TAB 1: Setup & Calculate ===
with tab1:
    st.header(get_text('step1_header'))
    st.markdown(get_text('setup_intro'))

    # Display Fixed Costs Summary (read-only confirmation)
    with st.expander(get_text('fixed_cost_summary'), expanded=False):
        # Read directly from session state for display here
        display_settings = st.session_state.get(STATE_SETTINGS, get_default_settings())
        display_total_fixed = sum(float(v) for k, v in display_settings.items() if k != 'base_margin')
        st.json({
            get_text('rent'): egp_format(display_settings.get('rent', 0)),
            get_text('salaries'): egp_format(display_settings.get('salaries', 0)),
            get_text('utilities'): egp_format(display_settings.get('utilities', 0)),
            get_text('insurance'): egp_format(display_settings.get('insurance', 0)),
            get_text('marketing'): egp_format(display_settings.get('marketing', 0)),
            get_text('other_fixed'): egp_format(display_settings.get('other_fixed', 0)),
            f"**{get_text('total_fixed_cost')}**": f"**{egp_format(display_total_fixed)}**"
        })
        st.caption(get_text('fixed_cost_caption'))
    st.divider()

    # --- Service Management ---
    st.subheader(get_text('manage_services_header'))
    st.markdown(get_text('manage_services_intro'))

    # Configure columns for the editor dynamically based on language
    column_config_editor = {
        COL_NAME: st.column_config.TextColumn(get_text('col_name_orig'), help=get_text('col_name_orig_help')),
        COL_NAME_EN: st.column_config.TextColumn(get_text('col_name_disp'), required=True, help=get_text('col_name_disp_help')),
        COL_EXPECTED_CASES: st.column_config.NumberColumn(get_text('col_exp_cases'), required=True, min_value=0, format="%d", help=get_text('col_exp_cases_help')),
        COL_VAR_COST: st.column_config.NumberColumn(get_text('col_var_cost'), required=True, min_value=0.0, format="%.2f", help=get_text('col_var_cost_help')),
        COL_DURATION: st.column_config.NumberColumn(get_text('col_duration'), required=True, min_value=0.01, format="%.2f", help=get_text('col_duration_help'))
    }

    # The data_editor modifies a copy, we need to update state and save
    # Ensure the dataframe in state is valid before passing to editor
    if STATE_SERVICES_DF_INPUT not in st.session_state or not isinstance(st.session_state[STATE_SERVICES_DF_INPUT], pd.DataFrame):
         st.session_state[STATE_SERVICES_DF_INPUT] = get_default_services() # Reset if invalid

    edited_df = st.data_editor(
        st.session_state[STATE_SERVICES_DF_INPUT],
        num_rows="dynamic",
        column_config=column_config_editor,
        use_container_width=True,
        key=get_text('service_editor_key'), # Key based on lang may help reset state on switch
        hide_index=True
    )

    # Check if the dataframe has changed compared to the one in session state
    if not edited_df.equals(st.session_state[STATE_SERVICES_DF_INPUT]):
        st.session_state[STATE_SERVICES_DF_INPUT] = edited_df # Update state
        # Save immediately after edit
        save_app_data(DATA_FILE, st.session_state[STATE_SETTINGS], edited_df)
        # Clear old results as input data has changed
        st.session_state[STATE_CALCULATED] = False
        st.session_state[STATE_RESULTS_DF] = None
        st.session_state[STATE_SIMULATION_RESULTS_DF] = None
        st.toast("Service list updated and saved.", icon="📝")
        # Rerun might be needed if clearing results should immediately hide sections
        # st.rerun()


    # --- Validation Feedback ---
    is_valid, errors = validate_service_data(edited_df) # Validate the current state of the editor df
    if not is_valid:
        st.warning(get_text('validation_warn'), icon="⚠️")
        for error in errors:
            st.markdown(f"- {error}")
    # Only show success if no errors AND the dataframe is not empty
    elif not edited_df.empty:
        st.success(get_text('validation_ok'), icon="✅")

    st.divider()

    # --- Calculation Trigger ---
    st.header(get_text('step2_header'))
    st.markdown(get_text('step2_intro'))

    # Disable button if data is invalid OR if the editor df is empty
    calculate_button_disabled = not is_valid or edited_df.empty
    calculate_button = st.button(
        get_text('calculate_button'),
        type="primary",
        use_container_width=True,
        disabled=calculate_button_disabled
    )


    if calculate_button:
        # Re-check validity just before calculation as a safeguard
        is_valid_on_calc, errors_on_calc = validate_service_data(st.session_state[STATE_SERVICES_DF_INPUT])
        if not is_valid_on_calc:
            st.error(get_text('calculate_error'))
            # Optionally display errors again
            # for error in errors_on_calc: st.markdown(f"- {error}")
        else:
            # Use the validated data from the editor's current state
            calc_settings = st.session_state.get(STATE_SETTINGS, get_default_settings())
            calc_total_fixed = sum(float(v) for k, v in calc_settings.items() if k != 'base_margin')
            calc_margin = float(calc_settings.get('base_margin', 0.35))

            results = calculate_detailed_pricing(
                st.session_state[STATE_SERVICES_DF_INPUT], # Use current state df
                calc_total_fixed,
                calc_margin
            )
            if results is not None:
                st.session_state[STATE_RESULTS_DF] = results
                st.session_state[STATE_CALCULATED] = True
                st.session_state[STATE_SIMULATION_RESULTS_DF] = None # Reset simulation on new base calc
                st.success(get_text('calculate_success'))
                # st.balloons()
            else:
                 st.session_state[STATE_CALCULATED] = False
                 st.error(get_text('calculate_fail'))


    # --- Display Results & KPIs (if calculated) ---
    st.divider()
    st.header(get_text('step3_header'))
    # Check calculation flag and ensure results DF is not None and not empty
    if st.session_state.get(STATE_CALCULATED, False) and isinstance(st.session_state.get(STATE_RESULTS_DF), pd.DataFrame) and not st.session_state[STATE_RESULTS_DF].empty:
        results_df = st.session_state[STATE_RESULTS_DF]

        # --- KPIs ---
        with st.container(border=True): # Use border for visual grouping
            st.subheader(get_text('results_kpi_header'))
            # Calculate overall KPIs from the results_df
            total_revenue = results_df[COL_REVENUE_EXPECTED].sum()
            total_profit = results_df[COL_PROFIT_EXPECTED].sum()
            total_var_cost = (results_df[COL_VAR_COST] * results_df[COL_EXPECTED_CASES]).sum()
            # Use the fixed cost that was *used* in the calculation
            calc_settings_kpi = st.session_state.get(STATE_SETTINGS, get_default_settings())
            total_fixed_cost_used = sum(float(v) for k, v in calc_settings_kpi.items() if k != 'base_margin')

            overall_margin_pct = (total_profit / total_revenue * 100) if total_revenue != 0 else 0
            total_cm = (results_df[COL_CONTRIB_MARGIN] * results_df[COL_EXPECTED_CASES]).sum()
            weighted_avg_cm_ratio = (total_cm / total_revenue) if total_revenue != 0 else 0
            total_break_even_revenue = (total_fixed_cost_used / weighted_avg_cm_ratio) if weighted_avg_cm_ratio > 0 else float('inf')
            total_hours = results_df[COL_SERVICE_HOURS].sum()
            avg_revenue_per_hour = total_revenue / total_hours if total_hours != 0 else 0
            avg_cm_per_hour = total_cm / total_hours if total_hours != 0 else 0

            kp_cols = st.columns(4)
            kp_cols[0].metric(get_text('kpi_total_revenue'), egp_format(total_revenue), help=get_text('kpi_total_revenue_help'))
            kp_cols[1].metric(get_text('kpi_total_profit'), egp_format(total_profit), help=get_text('kpi_total_profit_help'))
            kp_cols[2].metric(get_text('kpi_overall_margin'), f"{overall_margin_pct:.1f}%", help=get_text('kpi_overall_margin_help'))
            be_revenue_text = egp_format(total_break_even_revenue) if np.isfinite(total_break_even_revenue) else get_text('kpi_be_revenue_help').split('.')[-1].strip() # Get N/A text part
            kp_cols[3].metric(get_text('kpi_be_revenue'), be_revenue_text, help=get_text('kpi_be_revenue_help'))

            kp_cols2 = st.columns(4)
            kp_cols2[0].metric(get_text('kpi_avg_rev_hr'), egp_format(avg_revenue_per_hour), help=get_text('kpi_avg_rev_hr_help'))
            kp_cols2[1].metric(get_text('kpi_avg_cm_hr'), egp_format(avg_cm_per_hour), help=get_text('kpi_avg_cm_hr_help'))
            kp_cols2[2].metric(get_text('kpi_total_hours'), f"{total_hours:,.1f} hrs", help=get_text('kpi_total_hours_help'))
            kp_cols2[3].metric(get_text('kpi_num_services'), f"{len(results_df)}")

        # --- Detailed Results Table ---
        st.subheader(get_text('results_table_header'))
        display_df_final = results_df.copy()

        # Columns to display in the final table
        display_cols = [
            COL_NAME_EN, COL_EXPECTED_CASES, COL_VAR_COST, COL_DURATION,
            COL_ALLOC_FIXED_COST, COL_FIXED_COST_PER_CASE, COL_TOTAL_COST_PER_CASE,
            COL_PRICE_PER_CASE, COL_CONTRIB_MARGIN, COL_CONTRIB_MARGIN_RATIO, COL_BREAK_EVEN
        ]
        # Tooltips mapped to the display columns
        results_tooltips = {
            COL_NAME_EN: get_text('results_tooltip_name'),
            COL_EXPECTED_CASES: get_text('results_tooltip_cases'),
            COL_VAR_COST: get_text('results_tooltip_vc'),
            COL_DURATION: get_text('results_tooltip_dur'),
            COL_ALLOC_FIXED_COST: get_text('results_tooltip_afc'),
            COL_FIXED_COST_PER_CASE: get_text('results_tooltip_fcpc'),
            COL_TOTAL_COST_PER_CASE: get_text('results_tooltip_tcpc'),
            COL_PRICE_PER_CASE: get_text('results_tooltip_price'),
            COL_CONTRIB_MARGIN: get_text('results_tooltip_cm'),
            COL_CONTRIB_MARGIN_RATIO: get_text('results_tooltip_cmr'),
            COL_BREAK_EVEN: get_text('results_tooltip_be')
        }
        # Apply formatting and tooltips
        st.dataframe(
            display_df_final[display_cols].style.format({
                COL_EXPECTED_CASES: "{:,.0f}",
                COL_VAR_COST: "{:,.0f}", # EGP often uses whole numbers
                COL_DURATION: "{:.1f}",
                COL_ALLOC_FIXED_COST: "{:,.0f}",
                COL_FIXED_COST_PER_CASE: "{:,.0f}",
                COL_TOTAL_COST_PER_CASE: "{:,.0f}",
                COL_PRICE_PER_CASE: "{:,.0f}",
                COL_CONTRIB_MARGIN: "{:,.0f}",
                COL_CONTRIB_MARGIN_RATIO: "{:.1f}%",
                COL_BREAK_EVEN: lambda x: "{:.1f}".format(x) if np.isfinite(x) else "∞" # Show infinity for BEP
            }).set_tooltips(
                pd.DataFrame({col:[results_tooltips.get(col,"")] for col in display_cols}), # Ensure tooltips match selected cols
                props='visibility: hidden; position: absolute; background-color: #eee; border: 1px solid #ccc; padding: 5px; z-index: 10; text-align: left; max-width: 150px;' # Added max-width
            ).background_gradient(cmap='Greens', subset=[COL_CONTRIB_MARGIN_RATIO]), # Apply gradient only to CM Ratio
         hide_index=True, use_container_width=True)

        # --- Download Button ---
        try: # Add error handling for CSV conversion
            csv_data = convert_df_to_csv(display_df_final[display_cols])
            st.download_button(
                label=get_text('download_button'),
                data=csv_data,
                file_name="dental_clinic_pricing_results.csv",
                mime="text/csv",
                key="download_results_btn"
            )
        except Exception as e:
             st.error(f"Error preparing download: {e}")


    # Show info message if calculation hasn't happened or resulted in empty df
    elif not st.session_state.get(STATE_CALCULATED, False):
        st.info(get_text('results_info'), icon="👆")
    # Handle case where calculation ran but result was None or empty
    elif st.session_state.get(STATE_CALCULATED, False) and (st.session_state.get(STATE_RESULTS_DF) is None or st.session_state[STATE_RESULTS_DF].empty):
         st.warning("Calculation resulted in no data to display. Please check inputs.", icon="🤔")


# === TAB 2: Analysis & Simulation ===
with tab2:
    st.header(get_text('analysis_header'))

    # Check calculation flag and ensure results DF is not None and not empty
    if not st.session_state.get(STATE_CALCULATED, False) or not isinstance(st.session_state.get(STATE_RESULTS_DF), pd.DataFrame) or st.session_state[STATE_RESULTS_DF].empty:
        st.warning(get_text('analysis_warning'), icon="⚠️")
    else:
        # Retrieve base results and parameters from state safely
        base_results_df = st.session_state[STATE_RESULTS_DF] # Known to be a non-empty DF here
        base_settings = st.session_state.get(STATE_SETTINGS, get_default_settings())
        base_fixed_cost = sum(float(v) for k, v in base_settings.items() if k != 'base_margin')
        base_margin = float(base_settings.get('base_margin', 0.35))
        # The input DF used for the calculation is the one currently in state
        base_services_df_input = st.session_state.get(STATE_SERVICES_DF_INPUT) # Could be None if state messed up, check later

        analysis_tab1, analysis_tab2, analysis_tab3 = st.tabs([
            get_text('analysis_tab_visual'),
            get_text('analysis_tab_sim'),
            get_text('analysis_tab_sens')
        ])

        # --- Visual Analysis ---
        with analysis_tab1:
            st.subheader(get_text('viz_profit_title'))
            profit_fig = plot_bar_chart(base_results_df, COL_NAME_EN, COL_PROFIT_EXPECTED,
                                        'viz_profit_chart_title', 'viz_profit_chart_ylabel', 'viz_profit_chart_tooltip', color='mediumseagreen')
            if profit_fig: st.pyplot(profit_fig)

            cm_fig = plot_bar_chart(base_results_df, COL_NAME_EN, COL_CONTRIB_MARGIN,
                                    'viz_cm_chart_title', 'viz_cm_chart_ylabel', 'viz_cm_chart_tooltip', color='lightcoral')
            if cm_fig: st.pyplot(cm_fig)

            st.subheader(get_text('viz_time_title'))
            time_fig = plot_bar_chart(base_results_df, COL_NAME_EN, COL_SERVICE_HOURS,
                                      'viz_time_chart_title', 'viz_time_chart_ylabel', 'viz_time_chart_tooltip', color='lightblue')
            if time_fig: st.pyplot(time_fig)

            cm_hr_fig = plot_bar_chart(base_results_df, COL_NAME_EN, COL_CM_PER_HOUR,
                                       'viz_cm_hr_chart_title', 'viz_cm_hr_chart_ylabel', 'viz_cm_hr_chart_tooltip', color='lightgreen')
            if cm_hr_fig: st.pyplot(cm_hr_fig)


        # --- Scenario Simulation ---
        with analysis_tab2:
            st.subheader(get_text('sim_header'))
            st.markdown(get_text('sim_intro'))

            with st.form(get_text('sim_form_key')):
                st.markdown(get_text('sim_global_adjust'))
                sim_cols = st.columns(2)
                sim_fixed_cost = sim_cols[0].number_input(
                    get_text('sim_fixed_cost_label'), value=float(base_fixed_cost), step=1000.0, format="%f",
                    help=get_text('sim_fixed_cost_help').format(egp_format(base_fixed_cost)))
                sim_margin_pct = sim_cols[1].slider(
                    get_text('sim_margin_label'), 0, 200, int(base_margin * 100), 5,
                    help=get_text('sim_margin_help').format(f"{base_margin*100:.0f}"))
                sim_margin = sim_margin_pct / 100.0

                st.markdown(get_text('sim_specific_adjust'))
                # Options depend on base_results_df which is guaranteed non-empty here
                service_options = [get_text('sim_option_none')] + base_results_df[COL_NAME_EN].tolist()

                selected_service_sim = st.selectbox(get_text('sim_select_service'), options=service_options, key="sim_service_select_in_form", index=0)

                sim_var_cost_override = None
                sim_cases_override = None
                sim_duration_override = None
                modified_service_idx = None

                if selected_service_sim != get_text('sim_option_none'):
                     # Ensure base_services_df_input exists and is a DataFrame before indexing
                    if isinstance(base_services_df_input, pd.DataFrame) and not base_services_df_input.empty:
                         service_input_row = base_services_df_input[base_services_df_input[COL_NAME_EN] == selected_service_sim]
                         if not service_input_row.empty:
                            modified_service_idx = service_input_row.index[0]
                            sim_spec_cols = st.columns(3)
                            sim_var_cost_override = sim_spec_cols[0].number_input(get_text('sim_var_cost_label'), value=float(service_input_row[COL_VAR_COST].iloc[0]), format="%.2f", key="sim_vc", min_value=0.0)
                            sim_cases_override = sim_spec_cols[1].number_input(get_text('sim_cases_label'), value=int(service_input_row[COL_EXPECTED_CASES].iloc[0]), key="sim_ec", min_value=0, step=1)
                            sim_duration_override = sim_spec_cols[2].number_input(get_text('sim_duration_label'), value=float(service_input_row[COL_DURATION].iloc[0]), format="%.2f", key="sim_dur", min_value=0.01, step=0.1)
                         else:
                            st.warning(get_text('sim_service_not_found'))
                    else:
                         st.warning("Base service input data not available for simulation overrides.")


                submitted_sim = st.form_submit_button(get_text('sim_run_button'), type="primary")

            # --- Simulation Results Display ---
            if submitted_sim:
                # Ensure base_services_df_input exists before trying to copy/modify
                if isinstance(base_services_df_input, pd.DataFrame):
                    sim_services_df = base_services_df_input.copy()
                    if modified_service_idx is not None and selected_service_sim != get_text('sim_option_none'):
                        # Apply overrides safely using .loc
                        if sim_var_cost_override is not None: sim_services_df.loc[modified_service_idx, COL_VAR_COST] = sim_var_cost_override
                        if sim_cases_override is not None: sim_services_df.loc[modified_service_idx, COL_EXPECTED_CASES] = sim_cases_override
                        if sim_duration_override is not None: sim_services_df.loc[modified_service_idx, COL_DURATION] = sim_duration_override

                    # Validate the simulated input data
                    sim_is_valid, sim_errors = validate_service_data(sim_services_df)
                    if not sim_is_valid:
                        st.error(get_text('sim_input_invalid'))
                        for err in sim_errors: st.markdown(f"- {err}")
                        st.session_state[STATE_SIMULATION_RESULTS_DF] = None # Clear previous results
                    else:
                        # Run calculation with simulated inputs
                        simulated_results = calculate_detailed_pricing(sim_services_df, sim_fixed_cost, sim_margin)
                        if simulated_results is not None:
                            st.session_state[STATE_SIMULATION_RESULTS_DF] = simulated_results
                            st.success(get_text('sim_success'))
                        else:
                            st.error(get_text('sim_fail'))
                            st.session_state[STATE_SIMULATION_RESULTS_DF] = None
                else:
                     st.error("Cannot run simulation - base input data is missing.")


            # Display simulation results if they exist in state
            # Check it's a non-empty DataFrame
            if isinstance(st.session_state.get(STATE_SIMULATION_RESULTS_DF), pd.DataFrame) and not st.session_state[STATE_SIMULATION_RESULTS_DF].empty:
                 sim_results_df = st.session_state[STATE_SIMULATION_RESULTS_DF]
                 st.divider()
                 st.subheader(get_text('sim_results_header'))

                 # Base KPIs are already calculated and stored in base_results_df (guaranteed non-empty here)
                 base_total_revenue = base_results_df[COL_REVENUE_EXPECTED].sum()
                 base_total_profit = base_results_df[COL_PROFIT_EXPECTED].sum()
                 base_overall_margin_pct = (base_total_profit / base_total_revenue * 100) if base_total_revenue != 0 else 0
                 base_total_hours = base_results_df[COL_SERVICE_HOURS].sum()
                 base_avg_revenue_per_hour = base_total_revenue / base_total_hours if base_total_hours != 0 else 0

                 # Calculate Simulated KPIs
                 sim_total_revenue = sim_results_df[COL_REVENUE_EXPECTED].sum()
                 sim_total_profit = sim_results_df[COL_PROFIT_EXPECTED].sum()
                 sim_overall_margin_pct = (sim_total_profit / sim_total_revenue * 100) if sim_total_revenue != 0 else 0
                 sim_total_hours = sim_results_df[COL_SERVICE_HOURS].sum()
                 sim_avg_revenue_per_hour = sim_total_revenue / sim_total_hours if sim_total_hours != 0 else 0

                 st.markdown(get_text('sim_kpi_compare'))
                 sim_kp_cols = st.columns(4)
                 sim_kp_cols[0].metric(get_text('sim_kpi_revenue'), egp_format(sim_total_revenue), f"{sim_total_revenue-base_total_revenue:,.0f}")
                 sim_kp_cols[1].metric(get_text('sim_kpi_profit'), egp_format(sim_total_profit), f"{sim_total_profit-base_total_profit:,.0f}")
                 sim_kp_cols[2].metric(get_text('sim_kpi_margin'), f"{sim_overall_margin_pct:.1f}%", f"{sim_overall_margin_pct-base_overall_margin_pct:.1f}% pts")
                 sim_kp_cols[3].metric(get_text('sim_kpi_rev_hr'), egp_format(sim_avg_revenue_per_hour), f"{sim_avg_revenue_per_hour-base_avg_revenue_per_hour:,.0f}")

                 # Detail Comparison for modified service
                 if selected_service_sim != get_text('sim_option_none') and modified_service_idx is not None:
                     # Check if service name exists in both dataframes
                     base_row = base_results_df[base_results_df[COL_NAME_EN] == selected_service_sim]
                     sim_row = sim_results_df[sim_results_df[COL_NAME_EN] == selected_service_sim]

                     if not base_row.empty and not sim_row.empty:
                         st.markdown(f"--- \n {get_text('sim_detail_compare').format(selected_service_sim)}")
                         sim_comp_cols = st.columns(4)
                         base_service_res = base_row.iloc[0]
                         sim_service_res = sim_row.iloc[0]

                         # Compare Price, CM, BEP, Profit
                         sim_comp_cols[0].metric(get_text('sim_detail_price'), egp_format(sim_service_res[COL_PRICE_PER_CASE]), f"{sim_service_res[COL_PRICE_PER_CASE]-base_service_res[COL_PRICE_PER_CASE]:,.0f}")
                         sim_comp_cols[1].metric(get_text('sim_detail_cm'), egp_format(sim_service_res[COL_CONTRIB_MARGIN]), f"{sim_service_res[COL_CONTRIB_MARGIN]-base_service_res[COL_CONTRIB_MARGIN]:,.0f}")
                         # Safely calculate BEP delta
                         bep_base_val = base_service_res[COL_BREAK_EVEN]
                         bep_sim_val = sim_service_res[COL_BREAK_EVEN]
                         bep_delta = bep_sim_val - bep_base_val if np.isfinite(bep_sim_val) and np.isfinite(bep_base_val) else "N/A"
                         bep_delta_str = f"{bep_delta:.1f}" if isinstance(bep_delta, (int, float)) else bep_delta
                         bep_sim_display = "{:.1f}".format(bep_sim_val) if np.isfinite(bep_sim_val) else "∞"
                         sim_comp_cols[2].metric(get_text('sim_detail_bep'), bep_sim_display, bep_delta_str )
                         sim_comp_cols[3].metric(get_text('sim_detail_profit'), egp_format(sim_service_res[COL_PROFIT_EXPECTED]), f"{sim_service_res[COL_PROFIT_EXPECTED]-base_service_res[COL_PROFIT_EXPECTED]:,.0f}")

                 # Full Simulated Results Table
                 st.markdown(f"--- \n {get_text('sim_table_header')}")
                 # Use similar display logic as base results
                 sim_display_df = sim_results_df.copy()
                 sim_display_cols = [ # Same columns as base results display
                     COL_NAME_EN, COL_EXPECTED_CASES, COL_VAR_COST, COL_DURATION,
                     COL_ALLOC_FIXED_COST, COL_FIXED_COST_PER_CASE, COL_TOTAL_COST_PER_CASE,
                     COL_PRICE_PER_CASE, COL_CONTRIB_MARGIN, COL_CONTRIB_MARGIN_RATIO, COL_BREAK_EVEN
                 ]
                 # Map display text to columns for renaming
                 sim_rename_map = {
                     COL_NAME_EN: get_text('sim_col_service'), COL_EXPECTED_CASES: get_text('sim_col_cases'),
                     COL_VAR_COST: get_text('sim_col_vc'), COL_DURATION: get_text('sim_col_hrs'),
                     COL_ALLOC_FIXED_COST: get_text('sim_col_afc'), COL_FIXED_COST_PER_CASE: get_text('sim_col_fcpc'),
                     COL_TOTAL_COST_PER_CASE: get_text('sim_col_tcpc'), COL_PRICE_PER_CASE: get_text('sim_col_price'),
                     COL_CONTRIB_MARGIN: get_text('sim_col_cm'), COL_CONTRIB_MARGIN_RATIO: get_text('sim_col_cmr'),
                     COL_BREAK_EVEN: get_text('sim_col_bep')
                 }
                 st.dataframe(
                     sim_display_df[sim_display_cols].rename(columns=sim_rename_map)
                     .style.format({ # Apply formatting based on renamed columns
                         get_text('sim_col_cases'): "{:,.0f}",
                         get_text('sim_col_vc'): "{:,.0f}",
                         get_text('sim_col_hrs'): "{:.1f}",
                         get_text('sim_col_afc'): "{:,.0f}",
                         get_text('sim_col_fcpc'): "{:,.0f}",
                         get_text('sim_col_tcpc'): "{:,.0f}",
                         get_text('sim_col_price'): "{:,.0f}",
                         get_text('sim_col_cm'): "{:,.0f}",
                         get_text('sim_col_cmr'): "{:.1f}%",
                         get_text('sim_col_bep'): lambda x: "{:.1f}".format(x) if np.isfinite(x) else "∞"
                     }),
                     hide_index=True, use_container_width=True
                 )
                 # Optional: Add download for simulation results too
                 try: # Add error handling for CSV conversion
                    sim_csv_data = convert_df_to_csv(sim_display_df[sim_display_cols].rename(columns=sim_rename_map))
                    st.download_button(
                        label=get_text('download_button') + " (Simulation)",
                        data=sim_csv_data,
                        file_name="dental_clinic_simulation_results.csv",
                        mime="text/csv",
                        key="download_sim_results_btn"
                    )
                 except Exception as e:
                     st.error(f"Error preparing simulation download: {e}")


        # --- Sensitivity Analysis ---
        with analysis_tab3:
            st.subheader(get_text('sens_header'))
            st.markdown(get_text('sens_intro'))
            # Base results df is guaranteed non-empty here
            service_names_options_sens = base_results_df[COL_NAME_EN].tolist()
            if not service_names_options_sens: # Should not happen based on outer check, but safe practice
                 st.info(get_text('sens_no_service'))
            else:
                selected_service_sens = st.selectbox(get_text('sens_select_service'), options=service_names_options_sens, key="sens_select")

                if selected_service_sens:
                     service_data_row = base_results_df[base_results_df[COL_NAME_EN] == selected_service_sens]
                     if not service_data_row.empty:
                         service_data_sens = service_data_row.iloc[0]
                         st.markdown(f"{get_text('sens_analyzing')} **{selected_service_sens}**")
                         # Ensure expected cases is treated as int
                         try:
                            expected_cases_display = int(service_data_sens[COL_EXPECTED_CASES])
                         except (ValueError, TypeError):
                            st.warning(f"Invalid expected cases value for {selected_service_sens}. Using 1.")
                            expected_cases_display = 1


                         sens_cols = st.columns(3)
                         min_cases = sens_cols[0].number_input(get_text('sens_min_cases'), 1, value=max(1, int(expected_cases_display * 0.2)), step=1, key="sens_min", help=get_text('sens_min_cases_help'))
                         max_cases = sens_cols[1].number_input(get_text('sens_max_cases'), int(min_cases)+1, value=int(expected_cases_display * 2.0), step=5, key="sens_max", help=get_text('sens_max_cases_help'))
                         step_cases = sens_cols[2].number_input(get_text('sens_step'), 1, value=max(1, int((max_cases - min_cases)/10) if (max_cases - min_cases)>0 else 1), step=1, key="sens_step", help=get_text('sens_step_help'))

                         if max_cases <= min_cases: st.error(get_text('sens_error_range'))
                         elif step_cases <= 0: st.error("Step must be positive.") # Added check for step
                         else:
                             try:
                                 cases_range_list = list(range(int(min_cases), int(max_cases) + 1, int(step_cases)))
                                 if not cases_range_list: st.warning(get_text('sens_error_step'))
                                 else:
                                     # Ensure calculation inputs are floats
                                     var_cost_sens = float(service_data_sens[COL_VAR_COST])
                                     alloc_fixed_sens = float(service_data_sens[COL_ALLOC_FIXED_COST])

                                     prices, break_evens = calculate_sensitivity(
                                         variable_cost=var_cost_sens,
                                         allocated_fixed_cost=alloc_fixed_sens,
                                         margin=float(base_margin), # Use base margin
                                         cases_range=cases_range_list
                                     )
                                     sensitivity_fig = plot_sensitivity(cases_range_list, prices, break_evens)
                                     if sensitivity_fig:
                                         st.pyplot(sensitivity_fig)
                                     # No need for else here, plot_sensitivity handles no data case

                             except ValueError as ve:
                                  st.error(f"Please ensure Min/Max/Step cases are valid integers. Error: {ve}")
                             except Exception as e_sens:
                                  st.error(f"An error occurred during sensitivity analysis: {e_sens}")
                     else:
                          st.warning("Selected service data not found in results.")


# --- END OF FILE main_redesigned.py ---
