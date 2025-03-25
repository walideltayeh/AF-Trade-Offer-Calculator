import streamlit as st
import os
import sys
import importlib
import base64
from PIL import Image

# Function to get the Al Fakher logo with red outline
def get_svg_icon():
    # Check if we have the generated PNG file
    if os.path.exists('al_fakher_red_outline.png'):
        # Use the PNG file
        with open('al_fakher_red_outline.png', "rb") as f:
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
    "Investment Calculator": "investment_calculator"
}

# Create a logo for the sidebar
def add_logo():
    st.sidebar.markdown(
        f'<div style="text-align: center; margin-bottom: 20px;"><img src="{get_svg_icon()}" width="80"></div>',
        unsafe_allow_html=True
    )
    st.sidebar.markdown(f'<h1 style="text-align: center; font-size: 1.5em; margin-bottom: 30px;">Al Fakher Mexico</h1>', 
                       unsafe_allow_html=True)

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
        else:
            st.subheader("Investment Calculator")
            st.write("""
            Analyze investment requirements for the gift program:
            - Calculate ROI across customer tiers
            - Visualize budget allocation
            - Forecast gift expenditure
            - Understand net revenue impact
            - Optimize gift strategy
            """)
    
    # Main area - Import and run the selected app
    if selected_app == "Trade Offer Calculator":
        st.write("## Trade Offer Calculator")
        # Import app module
        app_module = importlib.import_module(APPS[selected_app])
        if hasattr(app_module, 'main'):
            app_module.main()
    else:
        st.write("## Investment Calculator")
        # Import investment calculator module
        app_module = importlib.import_module(APPS[selected_app])
        if hasattr(app_module, 'main'):
            app_module.main()

if __name__ == "__main__":
    main()
