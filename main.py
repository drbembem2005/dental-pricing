import streamlit as st
import matplotlib.pyplot as plt

# -------------------------------
# Core Functions
# -------------------------------

def pricing_analysis(fixed_cost, variable_cost_per_case, expected_cases, margin=0.3):
    """
    Calculate pricing parameters for a dental clinic service.
    
    Parameters:
      fixed_cost (float): Total fixed monthly costs.
      variable_cost_per_case (float): Variable cost per case.
      expected_cases (int): Expected number of cases per month.
      margin (float): Desired profit margin (e.g., 0.3 for 30%).
    
    Returns:
      tuple: (fixed_cost_per_case, total_cost_per_case, price_per_case, break_even_point)
    """
    # Calculate fixed cost allocated per case
    fixed_cost_per_case = fixed_cost / expected_cases
    
    # Total cost per case = variable cost + allocated fixed cost
    total_cost_per_case = variable_cost_per_case + fixed_cost_per_case
    
    # Final price after adding profit margin
    price_per_case = total_cost_per_case * (1 + margin)
    
    # Contribution margin per case = price - variable cost
    contribution_margin = calculate_contribution_margin(price_per_case, variable_cost_per_case)
    
    # Break-even point = fixed_cost / contribution margin per case
    break_even_point = fixed_cost / contribution_margin
    
    return fixed_cost_per_case, total_cost_per_case, price_per_case, break_even_point

def calculate_contribution_margin(price, variable_cost):
    """
    Calculate the contribution margin per case.
    
    Parameters:
      price (float): Final price per case.
      variable_cost (float): Variable cost per case.
    
    Returns:
      float: Contribution margin.
    """
    return price - variable_cost

def simulate_scenarios(fixed_cost, variable_cost_per_case, margin, cases_range):
    """
    Simulate pricing analysis for a range of expected cases.
    
    Parameters:
      fixed_cost (float): Total fixed costs.
      variable_cost_per_case (float): Variable cost per case.
      margin (float): Desired profit margin.
      cases_range (iterable): A range or list of expected cases values.
    
    Returns:
      dict: Dictionary containing lists of expected_cases, prices, and break-even points.
    """
    results = {
        "expected_cases": [],
        "price_per_case": [],
        "break_even_point": []
    }
    
    for cases in cases_range:
        fixed_per_case, total_cost, price, break_even = pricing_analysis(
            fixed_cost, variable_cost_per_case, cases, margin
        )
        results["expected_cases"].append(cases)
        results["price_per_case"].append(price)
        results["break_even_point"].append(break_even)
    
    return results

def plot_sensitivity(results):
    """
    Plot the sensitivity of final price and break-even point against the number of expected cases.
    
    Parameters:
      results (dict): Dictionary returned by simulate_scenarios containing expected_cases, price_per_case, and break_even_point.
      
    Returns:
      Matplotlib figure object.
    """
    fig, axs = plt.subplots(1, 2, figsize=(12, 6))
    
    # Plot final price per case vs expected cases
    axs[0].plot(results["expected_cases"], results["price_per_case"], marker='o', color='b')
    axs[0].set_xlabel("Expected Cases per Month")
    axs[0].set_ylabel("Final Price per Case (Ghem)")
    axs[0].set_title("Final Price vs Expected Cases")
    axs[0].grid(True)
    
    # Plot break-even point vs expected cases
    axs[1].plot(results["expected_cases"], results["break_even_point"], marker='o', color='r')
    axs[1].set_xlabel("Expected Cases per Month")
    axs[1].set_ylabel("Break-even Point (Cases)")
    axs[1].set_title("Break-even Point vs Expected Cases")
    axs[1].grid(True)
    
    plt.tight_layout()
    return fig

# -------------------------------
# Streamlit App Layout
# -------------------------------

st.title("Dental Clinic Pricing Analysis")

# Create two tabs: one for basic pricing and one for analytics
tab1, tab2 = st.tabs(["Pricing Analysis", "Analytics"])

# -------------------------------
# Tab 1: Pricing Analysis
# -------------------------------
with tab1:
    st.header("Enter Your Clinic Data")
    
    fixed_cost = st.number_input("Total Fixed Costs (Ghem)", min_value=0.0, value=42000.0, step=1000.0)
    variable_cost = st.number_input("Variable Cost per Case (Ghem)", min_value=0.0, value=300.0, step=10.0)
    expected_cases = st.number_input("Expected Cases per Month", min_value=1, value=200, step=1)
    margin = st.slider("Desired Profit Margin (%)", min_value=0, max_value=100, value=30) / 100.0
    
    if st.button("Calculate Pricing"):
        fixed_per_case, total_cost, price, break_even = pricing_analysis(fixed_cost, variable_cost, expected_cases, margin)
        st.subheader("Results")
        st.write(f"**Fixed Cost per Case:** {fixed_per_case:.2f} Ghem")
        st.write(f"**Total Cost per Case:** {total_cost:.2f} Ghem")
        st.write(f"**Final Price per Case (with {margin*100:.0f}% margin):** {price:.2f} Ghem")
        st.write(f"**Break-even Point (Number of Cases):** {break_even:.2f}")

# -------------------------------
# Tab 2: Analytics
# -------------------------------
with tab2:
    st.header("Sensitivity Analysis")
    st.write("Explore how changes in the expected number of cases affect the pricing and break-even point.")
    
    min_cases = st.number_input("Minimum Expected Cases", min_value=1, value=100, step=1, key="min")
    max_cases = st.number_input("Maximum Expected Cases", min_value=1, value=300, step=1, key="max")
    step_cases = st.number_input("Step", min_value=1, value=20, step=1, key="step")
    
    if st.button("Run Sensitivity Analysis"):
        cases_range = range(int(min_cases), int(max_cases)+1, int(step_cases))
        results = simulate_scenarios(fixed_cost, variable_cost, margin, cases_range)
        fig = plot_sensitivity(results)
        st.pyplot(fig)
