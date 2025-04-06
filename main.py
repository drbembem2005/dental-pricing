import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os # Needed for checking file existence

# --- Configuration & Constants ---
DATA_FILE = "dental_services_data.csv"
COLUMNS = ['Service', 'Duration (hours)', 'Variable Cost', 'Allocated Fixed Cost', 'Total Cost']

# --- Helper Functions ---

def load_data(file_path):
    """Loads data from a CSV file. Returns an empty DataFrame if file not found."""
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            # Ensure correct data types after loading
            df['Duration (hours)'] = pd.to_numeric(df['Duration (hours)'], errors='coerce').fillna(0)
            df['Variable Cost'] = pd.to_numeric(df['Variable Cost'], errors='coerce').fillna(0)
            df['Allocated Fixed Cost'] = pd.to_numeric(df['Allocated Fixed Cost'], errors='coerce').fillna(0)
            df['Total Cost'] = pd.to_numeric(df['Total Cost'], errors='coerce').fillna(0)
            # Ensure all required columns exist, add if missing
            for col in COLUMNS:
                if col not in df.columns:
                    df[col] = 0 if 'Cost' in col or 'Duration' in col else '' # Default value
            return df[COLUMNS] # Return with correct column order
        except pd.errors.EmptyDataError:
            st.warning(f"Data file '{file_path}' is empty. Starting fresh.")
            return pd.DataFrame(columns=COLUMNS)
        except Exception as e:
            st.error(f"Error loading data file '{file_path}': {e}")
            return pd.DataFrame(columns=COLUMNS)
    else:
        st.info(f"Data file '{file_path}' not found. Starting with an empty dataset.")
        return pd.DataFrame(columns=COLUMNS)

def save_data(df, file_path):
    """Saves the DataFrame to a CSV file."""
    try:
        df.to_csv(file_path, index=False)
    except Exception as e:
        st.error(f"Error saving data to '{file_path}': {e}")

def calculate_total_cost(df):
    """Recalculates the 'Total Cost' column based on other cost columns."""
    # Ensure columns exist and handle potential non-numeric data if necessary
    df['Variable Cost'] = pd.to_numeric(df['Variable Cost'], errors='coerce').fillna(0)
    df['Allocated Fixed Cost'] = pd.to_numeric(df['Allocated Fixed Cost'], errors='coerce').fillna(0)
    df['Total Cost'] = df['Variable Cost'] + df['Allocated Fixed Cost']
    return df

# --- Initialize Session State ---
# Load data only once per session or if it's not already loaded
if 'df' not in st.session_state:
    st.session_state.df = load_data(DATA_FILE)
    st.session_state.df = calculate_total_cost(st.session_state.df.copy()) # Ensure total cost is correct on load

# --- Sidebar: Add New Service ---
st.sidebar.header("Add New Service")
with st.sidebar.form(key='service_form', clear_on_submit=True):
    service = st.text_input('Service Name')
    duration = st.number_input('Duration (hours)', min_value=0.0, step=0.5, format="%.1f")
    variable_cost = st.number_input('Variable Cost', min_value=0.0, step=0.1, format="%.2f")
    allocated_fixed_cost = st.number_input('Allocated Fixed Cost', min_value=0.0, step=0.1, format="%.2f")
    submit_button = st.form_submit_button(label='Add Service')

    if submit_button:
        if not service:
            st.sidebar.error("Service Name cannot be empty.")
        # Optional: Check for duplicates before adding
        elif service in st.session_state.df['Service'].tolist():
             st.sidebar.warning(f"Service '{service}' already exists. Consider editing the existing entry.")
        else:
            total_cost = variable_cost + allocated_fixed_cost
            new_data = pd.DataFrame({
                'Service': [service],
                'Duration (hours)': [duration],
                'Variable Cost': [variable_cost],
                'Allocated Fixed Cost': [allocated_fixed_cost],
                'Total Cost': [total_cost]
            })
            # Use pd.concat instead of append (append is deprecated)
            st.session_state.df = pd.concat([st.session_state.df, new_data], ignore_index=True)
            save_data(st.session_state.df, DATA_FILE)
            st.sidebar.success(f'Service "{service}" added successfully!')
            # No need for st.experimental_rerun because clear_on_submit=True handles form reset

# --- Main Area ---
st.title('Dental Clinic Services Editor')

st.subheader("Manage Services")
st.info("You can edit data directly in the table below. Click '+' to add a new row (alternative way), or select rows and press 'Delete' on your keyboard to remove them.")

# Display and edit data using st.data_editor
edited_df = st.data_editor(
    st.session_state.df,
    key="data_editor", # Add a key for stability
    num_rows="dynamic", # Allow adding/deleting rows
    column_config={
        "Service": st.column_config.TextColumn("Service Name", required=True, help="Name of the dental service"),
        "Duration (hours)": st.column_config.NumberColumn("Duration (hrs)", min_value=0, format="%.1f h", help="Time required for the service"),
        "Variable Cost": st.column_config.NumberColumn("Variable Cost ($)", min_value=0, format="$%.2f", help="Costs that change per service (e.g., materials)"),
        "Allocated Fixed Cost": st.column_config.NumberColumn("Fixed Cost ($)", min_value=0, format="$%.2f", help="Allocated portion of fixed clinic costs (rent, salaries)"),
        "Total Cost": st.column_config.NumberColumn("Total Cost ($)", min_value=0, format="$%.2f", help="Variable Cost + Fixed Cost (Auto-calculated)", disabled=True), # Make Total Cost read-only initially
    },
    hide_index=True,
    use_container_width=True
)

# Process changes from the data editor
if edited_df is not None:
    # Check if the edited data is substantially different before saving
    # This comparison helps avoid saving minor float precision changes or saving when nothing changed.
    # It's not strictly necessary but can be good practice.
    if not edited_df.equals(st.session_state.df):
        # Recalculate Total Cost based on potentially edited Variable/Fixed Costs
        processed_df = calculate_total_cost(edited_df.copy())

        # Update session state only if there are actual changes
        if not processed_df.equals(st.session_state.df):
             st.session_state.df = processed_df
             save_data(st.session_state.df, DATA_FILE)
             st.success("Changes saved successfully!")
             st.rerun() # Rerun to ensure plot updates and editor reflects saved state cleanly


st.subheader("Cost Analysis Chart")

# Display the plot only if there's data
if not st.session_state.df.empty:
    try:
        # Ensure data types are suitable for plotting just before plotting
        plot_df = st.session_state.df.copy()
        plot_df['Variable Cost'] = pd.to_numeric(plot_df['Variable Cost'], errors='coerce').fillna(0)
        plot_df['Allocated Fixed Cost'] = pd.to_numeric(plot_df['Allocated Fixed Cost'], errors='coerce').fillna(0)
        plot_df['Total Cost'] = pd.to_numeric(plot_df['Total Cost'], errors='coerce').fillna(0)

        # Filter out rows where Service name might be empty or null if they sneak in
        plot_df = plot_df[plot_df['Service'].astype(str).str.strip() != '']

        if not plot_df.empty:
            fig, ax = plt.subplots(figsize=(10, 6)) # Adjust figure size if needed
            plot_df.plot(kind='bar', x='Service', y=['Variable Cost', 'Allocated Fixed Cost', 'Total Cost'], ax=ax)
            ax.set_title('Cost Analysis per Service')
            ax.set_ylabel('Cost ($)')
            ax.set_xlabel('Service')
            ax.tick_params(axis='x', rotation=45) # Rotate x-axis labels if they overlap
            plt.tight_layout() # Adjust layout
            st.pyplot(fig)
        else:
            st.warning("No valid service data to plot.")

    except Exception as e:
        st.error(f"An error occurred while generating the plot: {e}")
else:
    st.info("Add some services to see the cost analysis chart.")

# Optional: Display raw data for debugging or verification
# with st.expander("Show Raw Data"):
#     st.dataframe(st.session_state.df)
