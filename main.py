import streamlit as st
import os
import sys
import importlib
import base64
import json
from PIL import Image
import pandas as pd

# Function to get the Al Fakher logo with red outline
def get_svg_icon():
    # Check if we have the generated PNG file
    if os.path.exists('generated-icon.png'):
        # Use the PNG file
        with open('generated-icon.png', "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode('utf-8')
            return f'data:image/png;base64,{b64}'
    elif os.path.exists('al_fakher_icon.svg'):
        # Use the SVG file if PNG is not available
        with open('al_fakher_icon.svg', "r") as f:
            svg_code = f.read()
            b64 = base64.b64encode(svg_code.encode('utf-8')).decode('utf-8')
            return f'data:image/svg+xml;base64,{b64}'
    else:
        # Fallback to built-in SVG
        svg_code = """
        <svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
            <rect width="100" height="100" rx="20" fill="#000000"/>
            <rect x="10" y="10" width="80" height="80" rx="15" fill="none" stroke="#FF0000" stroke-width="5"/>
            <text x="50" y="55" font-family="Arial" font-size="30" font-weight="bold" text-anchor="middle" fill="white">AF</text>
        </svg>
        """
        b64 = base64.b64encode(svg_code.encode('utf-8')).decode('utf-8')
        return f'data:image/svg+xml;base64,{b64}'



# Set page configuration with custom icon - must be first Streamlit command
st.set_page_config(
    page_title="Al Fakher Mexico Tools",
    page_icon=get_svg_icon(),
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define the apps
APPS = {
    "Trade Offer Calculator": "app",
    "Investment Calculator": "investment_calculator",
    "Explanation": "explanation"
}

# Create a logo for the sidebar
def add_logo():
    st.sidebar.markdown(
        f'<div style="text-align: center; margin-bottom: 20px;"><img src="{get_svg_icon()}" width="80"></div>',
        unsafe_allow_html=True
    )
    st.sidebar.markdown(f'<h1 style="text-align: center; font-size: 1.5em; margin-bottom: 30px;">Al Fakher Mexico</h1>', 
                       unsafe_allow_html=True)

def load_csv(uploaded_file):
    #Add error handling for incorrect file types
    try:
        import pandas as pd
        return pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Error reading CSV file: {str(e)}")
        return None

def validate_csv(data):
    #Add error handling for missing columns
    try:
        return 'Size' in data.columns and 'Price/Pack' in data.columns
    except:
        return False

# Main function
def main():
    # Add logo to sidebar
    add_logo()

    # Title
    st.title("Al Fakher Mexico Tools")

    # Sidebar for app selection
    with st.sidebar:
        st.header("Application Selection")
        selected_app = st.radio(
            "Choose an application:",
            list(APPS.keys()),
            index=0
        )

        st.markdown("---")

        # App descriptions
        if selected_app == "Trade Offer Calculator":
            st.subheader("Trade Offer Calculator")
            st.write("""
            Calculate optimized gift allocations for customer orders:
            - Upload pricing data
            - Enter order quantities
            - Get gift recommendations based on order size
            - Adjust gift allocations with linked sliders
            - Export offer details
            """)
        elif selected_app == "Investment Calculator":
            st.subheader("Investment Calculator")
            st.write("""
            Analyze investment requirements for the gift program:
            - Calculate ROI across customer tiers
            - Visualize budget allocation
            - Forecast gift expenditure
            - Understand net revenue impact
            - Optimize gift strategy
            """)
        else: #explanation tab
            st.subheader("Explanation")
            st.write("""This section details the calculation methods and tier system.""")
        
        


    # Main area - Import and run the selected app
    if selected_app == "Trade Offer Calculator":
        st.write("## Trade Offer Calculator")
        # Import app module
        app_module = importlib.import_module(APPS[selected_app])
        if hasattr(app_module, 'main'):
            #Added session state for price data
            if 'price_data' not in st.session_state:
                # Initialize with default prices from app module
                st.session_state.price_data = app_module.DEFAULT_PRICES
            if 'uploaded_data' not in st.session_state:
                st.session_state.uploaded_data = None
            st.subheader("Price Data")

            # Price data source selection
            price_source = st.radio(
                "Select Price Data Source",
                ["Use Default Prices", "Upload CSV", "Manual Entry"],
                index=0 if st.session_state.price_data is not None and st.session_state.uploaded_data is None else 1
            )

            if price_source == "Use Default Prices":
                if st.session_state.price_data is not None:
                    st.success("Using default price data")
                else:
                    st.error("Default price data not available. Please use another option.")

            elif price_source == "Upload CSV":
                uploaded_file = st.file_uploader("Upload Price Data (CSV)", type=["csv"], key="main_uploader")
                if uploaded_file is not None:
                    try:
                        data = load_csv(uploaded_file)
                        if validate_csv(data):
                            st.session_state.price_data = data
                            st.session_state.uploaded_data = uploaded_file.name
                            st.success(f"Successfully loaded {uploaded_file.name}")
                            
                            # Display the uploaded pricing data
                            st.subheader("Uploaded Pricing Data")
                            st.dataframe(data, use_container_width=True)
                        else:
                            st.error("Invalid CSV format. File must contain 'Size' and 'Price/Pack' columns.")
                    except Exception as e:
                        st.error(f"Error loading file: {str(e)}")

            else:  # Manual Entry
                st.write("Enter prices for each pack size:")
                col1, col2, col3 = st.columns(3)

                with col1:
                    price_50g = st.number_input("50g Pack Price ($)", 
                                              min_value=0.0,
                                              value=float(st.session_state.price_data['Price/Pack'][st.session_state.price_data['Size'] == '50g'].iloc[0]) if st.session_state.price_data is not None and '50g' in st.session_state.price_data['Size'].values else 0.0,
                                              step=0.01)
                with col2:
                    price_250g = st.number_input("250g Pack Price ($)", 
                                               min_value=0.0,
                                               value=float(st.session_state.price_data['Price/Pack'][st.session_state.price_data['Size'] == '250g'].iloc[0]) if st.session_state.price_data is not None and '250g' in st.session_state.price_data['Size'].values else 0.0,
                                               step=0.01)
                with col3:
                    price_1kg = st.number_input("1kg Pack Price ($)", 
                                              min_value=0.0,
                                              value=float(st.session_state.price_data['Price/Pack'][st.session_state.price_data['Size'] == '1kg'].iloc[0]) if st.session_state.price_data is not None and '1kg' in st.session_state.price_data['Size'].values else 0.0,
                                              step=0.01)

                if st.button("Apply Manual Prices"):
                    # Create DataFrame from manual entries
                    manual_data = pd.DataFrame({
                        'Size': ['50g', '250g', '1kg'],
                        'Price/Pack': [price_50g, price_250g, price_1kg]
                    })
                    st.session_state.price_data = manual_data
                    st.session_state.uploaded_data = None
                    st.success("Manual prices applied successfully!")

            app_module.main()
    elif selected_app == "Investment Calculator":
        st.write("## Investment Calculator")
        # Import investment calculator module
        app_module = importlib.import_module(APPS[selected_app])
        if hasattr(app_module, 'main'):
            app_module.main()
    else:
        st.write("## Explanation")
        app_module = importlib.import_module(APPS[selected_app])
        if hasattr(app_module, 'main'):
            app_module.main()

# Function to create a developer footer for the app
def add_developer_footer():
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray; padding: 10px;'>"
        "Developed by Walid El Tayeh"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
    # Add developer footer to every page
    add_developer_footer()
