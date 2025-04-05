import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

st.title("تحليل تسعير مفصل لعيادة الأسنان")

# إنشاء تاب لتفاصيل البيانات وتفاصيل الخدمات
tab1, tab2 = st.tabs(["إدخال البيانات التفصيلية", "التحليلات والرسوم البيانية"])

# -----------------------------
# تبويب إدخال البيانات التفصيلية
# -----------------------------
with tab1:
    st.header("1. إدخال التكاليف الثابتة")
    st.write("أدخل تفاصيل المصاريف الثابتة للعيادة:")
    
    rent = st.number_input("إيجار العيادة (جنيه)", min_value=0.0, value=15000.0, step=500.0)
    salaries = st.number_input("رواتب العاملين (جنيه)", min_value=0.0, value=20000.0, step=500.0)
    utilities = st.number_input("فواتير الخدمات (كهرباء، ماء، إنترنت) (جنيه)", min_value=0.0, value=5000.0, step=200.0)
    insurance = st.number_input("تأمين وصيانة (جنيه)", min_value=0.0, value=2000.0, step=100.0)
    marketing = st.number_input("تكاليف تسويق وإعلان (جنيه)", min_value=0.0, value=1000.0, step=100.0)
    
    total_fixed_cost = rent + salaries + utilities + insurance + marketing
    st.write(f"**إجمالي التكاليف الثابتة للعيادة:** {total_fixed_cost:.2f} جنيه")
    
    st.header("2. إدخال بيانات الخدمات")
    st.write("أدخل تفاصيل كل خدمة تقدمها العيادة:")
    
    num_services = st.number_input("عدد أنواع الخدمات", min_value=1, value=3, step=1)
    
    # إنشاء قائمة لتخزين بيانات الخدمات
    services = []
    for i in range(int(num_services)):
        st.subheader(f"الخدمة {i+1}")
        service_name = st.text_input(f"اسم الخدمة {i+1}", value=f"الخدمة {i+1}", key=f"name_{i}")
        expected_cases = st.number_input(f"عدد الحالات المتوقع تنفيذها شهرياً ({service_name})", min_value=1, value=50, step=1, key=f"cases_{i}")
        variable_cost = st.number_input(f"التكلفة المتغيرة لكل حالة ({service_name}) (جنيه)", min_value=0.0, value=300.0, step=10.0, key=f"var_{i}")
        services.append({
            "name": service_name,
            "expected_cases": expected_cases,
            "variable_cost": variable_cost
        })
        
    margin = st.slider("هامش الربح المطلوب (%)", min_value=0, max_value=100, value=30) / 100.0

    if st.button("احسب التسعير التفصيلي"):
        # حساب إجمالي عدد الحالات لجميع الخدمات
        total_expected_cases = sum([s["expected_cases"] for s in services])
        
        results = []
        for s in services:
            # توزيع التكاليف الثابتة بناءً على نسبة عدد الحالات
            allocated_fixed_cost = total_fixed_cost * (s["expected_cases"] / total_expected_cases)
            fixed_cost_per_case = allocated_fixed_cost / s["expected_cases"]
            total_cost_per_case = s["variable_cost"] + fixed_cost_per_case
            price_per_case = total_cost_per_case * (1 + margin)
            contribution_margin = price_per_case - s["variable_cost"]
            break_even = allocated_fixed_cost / contribution_margin if contribution_margin > 0 else 0
            
            s.update({
                "allocated_fixed_cost": allocated_fixed_cost,
                "fixed_cost_per_case": fixed_cost_per_case,
                "total_cost_per_case": total_cost_per_case,
                "price_per_case": price_per_case,
                "break_even": break_even
            })
            results.append(s)
        
        # عرض النتائج في جدول
        df = pd.DataFrame(results)
        df = df.rename(columns={
            "name": "اسم الخدمة",
            "expected_cases": "عدد الحالات المتوقعة",
            "variable_cost": "التكلفة المتغيرة لكل حالة",
            "allocated_fixed_cost": "التكاليف الثابتة المخصصة",
            "fixed_cost_per_case": "التكلفة الثابتة لكل حالة",
            "total_cost_per_case": "التكلفة الإجمالية لكل حالة",
            "price_per_case": "السعر النهائي لكل حالة",
            "break_even": "نقطة التعادل (عدد الحالات)"
        })
        st.subheader("نتائج التحليل التفصيلي لكل خدمة")
        st.dataframe(df.style.format({
            "التكلفة المتغيرة لكل حالة": "{:.2f}",
            "التكلفة الثابتة لكل حالة": "{:.2f}",
            "التكلفة الإجمالية لكل حالة": "{:.2f}",
            "السعر النهائي لكل حالة": "{:.2f}",
            "نقطة التعادل (عدد الحالات)": "{:.2f}",
            "التكاليف الثابتة المخصصة": "{:.2f}"
        }))

# -----------------------------
# تبويب التحليلات والرسوم البيانية
# -----------------------------
with tab2:
    st.header("التحليلات والرسوم البيانية")
    st.write("يمكنك استكشاف حساسية النتائج لتغير عدد الحالات لكل خدمة.")
    
    selected_service = st.selectbox("اختر الخدمة للتحليل", [s["name"] for s in services] if services else [])
    
    if selected_service:
        # إيجاد بيانات الخدمة المحددة
        service_data = next(s for s in services if s["name"] == selected_service)
        # نعمل تحليل لحساسية السعر ونقطة التعادل بتغير عدد الحالات
        min_cases = st.number_input("أقل عدد للحالات", min_value=1, value=10, step=1, key="min_cases")
        max_cases = st.number_input("أعلى عدد للحالات", min_value=1, value=200, step=1, key="max_cases")
        step_cases = st.number_input("الخطوة", min_value=1, value=10, step=1, key="step_cases")
        
        def sensitivity_analysis(variable_cost, allocated_fixed_cost, margin, cases_range):
            prices = []
            break_evens = []
            for cases in cases_range:
                # إعادة توزيع الثابت على أساس عدد الحالات الجديدة
                fixed_cost_per_case = allocated_fixed_cost / cases
                total_cost = variable_cost + fixed_cost_per_case
                price = total_cost * (1 + margin)
                contribution_margin = price - variable_cost
                be = allocated_fixed_cost / contribution_margin if contribution_margin > 0 else 0
                prices.append(price)
                break_evens.append(be)
            return prices, break_evens
        
        cases_range = range(int(min_cases), int(max_cases)+1, int(step_cases))
        prices, break_evens = sensitivity_analysis(service_data["variable_cost"],
                                                     service_data["allocated_fixed_cost"],
                                                     margin,
                                                     cases_range)
        # رسم البيانات باستخدام matplotlib
        fig, axs = plt.subplots(1, 2, figsize=(12, 5))
        axs[0].plot(list(cases_range), prices, marker='o', color='b')
        axs[0].set_title("السعر النهائي مقابل عدد الحالات")
        axs[0].set_xlabel("عدد الحالات")
        axs[0].set_ylabel("السعر النهائي لكل حالة")
        axs[0].grid(True)
        
        axs[1].plot(list(cases_range), break_evens, marker='o', color='r')
        axs[1].set_title("نقطة التعادل مقابل عدد الحالات")
        axs[1].set_xlabel("عدد الحالات")
        axs[1].set_ylabel("نقطة التعادل (عدد الحالات)")
        axs[1].grid(True)
        
        st.pyplot(fig)
