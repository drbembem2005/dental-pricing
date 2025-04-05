import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

st.title("تحليل تسعير مفصل لعيادة الأسنان مع وزن الوقت")

# -----------------------------
# إعداد بيانات مُسبقة لبعض الخدمات الشائعة
# -----------------------------
default_services = [
    {"name": "تنظيف الأسنان", "expected_cases": 80, "variable_cost": 150.0, "duration_hours": 1},   # خدمة لمدة ساعة
    {"name": "حشو الأسنان", "expected_cases": 60, "variable_cost": 250.0, "duration_hours": 1},      # خدمة لمدة ساعة
    {"name": "علاج جذور الأسنان", "expected_cases": 40, "variable_cost": 500.0, "duration_hours": 2}, # خدمة لمدة ساعتين
    {"name": "تقويم الأسنان", "expected_cases": 20, "variable_cost": 1000.0, "duration_hours": 2},     # خدمة لمدة ساعتين
    {"name": "تبييض الأسنان", "expected_cases": 50, "variable_cost": 350.0, "duration_hours": 1},      # خدمة لمدة ساعة
    {"name": "زراعة الأسنان", "expected_cases": 10, "variable_cost": 3000.0, "duration_hours": 3}      # خدمة لمدة 3 ساعات
]

# -----------------------------
# تبويبات التطبيق
# -----------------------------
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
    
    st.header("2. بيانات الخدمات")
    st.write("يتم تحميل بعض الخدمات الشائعة مُسبقاً. يمكنك تعديل القيم أو إضافة خدمات جديدة.")
    
    # عرض جدول مُسبق للخدمات بحيث يمكن للمستخدم تعديله
    services_df = pd.DataFrame(default_services)
    services_df["name"] = services_df["name"].astype(str)
    services_df["expected_cases"] = services_df["expected_cases"].astype(int)
    services_df["variable_cost"] = services_df["variable_cost"].astype(float)
    services_df["duration_hours"] = services_df["duration_hours"].astype(float)
    
    st.dataframe(services_df)
    
    st.write("يمكنك تعديل أو إضافة خدمة عبر الجدول أدناه:")
    edited_services = st.experimental_data_editor(services_df, num_rows="dynamic")
    
    st.header("3. إعداد هامش الربح")
    margin = st.slider("هامش الربح المطلوب (%)", min_value=0, max_value=100, value=30) / 100.0

    if st.button("احسب التسعير التفصيلي لكل خدمة"):
        # تحويل الجدول المعدل إلى قائمة من القواميس
        services = edited_services.to_dict(orient="records")
        
        # حساب إجمالي "ساعات الخدمة" لجميع الخدمات
        total_service_hours = sum([s["expected_cases"] * s["duration_hours"] for s in services])
        
        results = []
        for s in services:
            # حساب الوزن الخاص بالخدمة = عدد الحالات * مدة الخدمة (بالساعات)
            service_hours = s["expected_cases"] * s["duration_hours"]
            # توزيع التكاليف الثابتة بناءً على الوزن الزمني للخدمة
            allocated_fixed_cost = total_fixed_cost * (service_hours / total_service_hours)
            fixed_cost_per_case = allocated_fixed_cost / s["expected_cases"]
            
            # التكلفة الإجمالية لكل حالة = التكلفة المتغيرة + التكلفة الثابتة لكل حالة
            total_cost_per_case = s["variable_cost"] + fixed_cost_per_case
            
            # السعر النهائي بعد إضافة هامش الربح
            price_per_case = total_cost_per_case * (1 + margin)
            
            # هامش المساهمة = السعر النهائي - التكلفة المتغيرة
            contribution_margin = price_per_case - s["variable_cost"]
            
            # نقطة التعادل لكل خدمة
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
        results_df = pd.DataFrame(results)
        results_df = results_df.rename(columns={
            "name": "اسم الخدمة",
            "expected_cases": "عدد الحالات المتوقعة",
            "variable_cost": "التكلفة المتغيرة لكل حالة",
            "duration_hours": "مدة الخدمة (بالساعات)",
            "allocated_fixed_cost": "التكاليف الثابتة المخصصة",
            "fixed_cost_per_case": "التكلفة الثابتة لكل حالة",
            "total_cost_per_case": "التكلفة الإجمالية لكل حالة",
            "price_per_case": "السعر النهائي لكل حالة",
            "break_even": "نقطة التعادل (عدد الحالات)"
        })
        
        st.subheader("نتائج التحليل التفصيلي لكل خدمة")
        st.dataframe(results_df.style.format({
            "التكلفة المتغيرة لكل حالة": "{:.2f}",
            "مدة الخدمة (بالساعات)": "{:.1f}",
            "التكاليف الثابتة المخصصة": "{:.2f}",
            "التكلفة الثابتة لكل حالة": "{:.2f}",
            "التكلفة الإجمالية لكل حالة": "{:.2f}",
            "السعر النهائي لكل حالة": "{:.2f}",
            "نقطة التعادل (عدد الحالات)": "{:.2f}"
        }))

# -----------------------------
# تبويب التحليلات والرسوم البيانية
# -----------------------------
with tab2:
    st.header("التحليلات والرسوم البيانية")
    st.write("اختر خدمة للتحليل وحساسية السعر ونقطة التعادل بتغير عدد الحالات.")
    
    if edited_services is not None and not edited_services.empty:
        service_names = edited_services["name"].tolist()
    else:
        service_names = [s["name"] for s in default_services]
    
    selected_service = st.selectbox("اختر الخدمة للتحليل", service_names)
    
    if selected_service:
        # إيجاد بيانات الخدمة المحددة
        service_data = edited_services[edited_services["name"] == selected_service].iloc[0].to_dict()
        
        st.write(f"تحليل حساسية الخدمة: **{selected_service}**")
        min_cases = st.number_input("أقل عدد للحالات", min_value=1, value=10, step=1, key="min_cases")
        max_cases = st.number_input("أعلى عدد للحالات", min_value=1, value=200, step=1, key="max_cases")
        step_cases = st.number_input("الخطوة", min_value=1, value=10, step=1, key="step_cases")
        
        def sensitivity_analysis(variable_cost, allocated_fixed_cost, margin, cases_range):
            prices = []
            break_evens = []
            for cases in cases_range:
                fixed_cost_per_case = allocated_fixed_cost / cases
                total_cost = variable_cost + fixed_cost_per_case
                price = total_cost * (1 + margin)
                contribution_margin = price - variable_cost
                be = allocated_fixed_cost / contribution_margin if contribution_margin > 0 else 0
                prices.append(price)
                break_evens.append(be)
            return prices, break_evens
        
        cases_range = range(int(min_cases), int(max_cases) + 1, int(step_cases))
        prices, break_evens = sensitivity_analysis(service_data["variable_cost"],
                                                     service_data["allocated_fixed_cost"],
                                                     margin,
                                                     cases_range)
        
        # رسم الرسوم البيانية باستخدام matplotlib
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
