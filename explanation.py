import streamlit as st
import pandas as pd

def main():
    st.title("Al Fakher Mexico - Calculation Methodology")
    
    # Tier System Explanation
    st.header("Tier System")
    st.write("""
    The tier system is based on order volume (total grams) and specific product requirements:
    """)
    
    tier_data = {
        'Tier': ['Silver', 'Gold', 'Diamond', 'Platinum'],
        'Minimum Order (g)': ['6,000g', '66,050g', '126,050g', '246,050g'],
        'Master Cases (6000g each)': ['1', '11', '21', '41'],
        'ROI %': ['5%', '7%', '9%', '13%'],
        'Special Requirements': [
            'None',
            'Must include at least one 1kg pack',
            'Must include at least one 1kg pack',
            'Must include at least one 1kg pack'
        ]
    }
    st.table(pd.DataFrame(tier_data))
    
    # Budget Calculation
    st.header("Budget Calculation")
    st.write("""
    The gift budget is calculated based on the ROI percentage for each tier:
    
    ```
    Budget = Total Order Value × ROI Percentage
    ```
    
    For example, if a Gold tier order (7% ROI) has a total value of $10,000:
    - Budget = $10,000 × 0.07
    - Budget = $700
    """)
    
    # Gift Allocation
    st.header("Gift Allocation Algorithm")
    st.write("""
    The gift budget is allocated across different types of gifts using this priority:
    
    1. **Hookah Allocation** (Tobacco Shops Only)
    - If budget ≥ $400 and order weight > 100kg: Up to 2 hookahs
    - If budget ≥ $400 and order weight > 50kg: 1 hookah
    
    2. **Remaining Budget Distribution**
    - 60% for Pack FOC (Free of Charge Packs)
    - 40% for AF Points
    
    Each Pack FOC costs $38 in the calculation.
    """)
    
    # Eligibility Rules
    st.header("Order Eligibility Rules")
    st.write("""
    An order must meet at least one of these conditions to be eligible for gifts:
    - 10 or more packs of 50g
    - 3 or more packs of 250g
    - 2 or more packs of 1kg
    """)
    
    # ROI Calculation
    st.header("ROI Calculation")
    st.write("""
    The actual ROI is calculated as:
    ```
    ROI = (Total Gift Value / Total Order Value) × 100
    
    Where Total Gift Value includes:
    - Number of FOC Packs × $38
    - Number of Hookahs × $400
    - AF Points (1 point = $1)
    ```
    """)

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
    # Add developer footer
    add_developer_footer()
