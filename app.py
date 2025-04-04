import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
import xlsxwriter
import base64
from datetime import datetime
from utils import load_csv, validate_csv, generate_order_summary, is_eligible_for_gift, calculate_gift_value, get_max_gift_quantities
from algorithms import recommend_gift, optimize_budget, calculate_roi, calculate_budget_from_roi
from models import CustomerType

# Default price data if not provided
DEFAULT_PRICES = pd.DataFrame({
    "Size": ["50g", "250g", "1kg"],
    "Price/Pack": [32.80, 176.81, 638.83]
})

def create_excel_download_link(df, filename, link_text="Download as Excel"):
    """
    Create a download link for a pandas DataFrame as an Excel file

    Args:
        df (pandas.DataFrame): DataFrame to export
        filename (str): Name of the file
        link_text (str): Text to display for the link

    Returns:
        str: HTML string containing the download link
    """
    # Create a BytesIO buffer
    buffer = io.BytesIO()

    # Create ExcelWriter object with XlsxWriter engine
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        # Write DataFrame to Excel
        df.to_excel(writer, index=False, sheet_name='Sheet1')

        # Close the Pandas Excel writer
        writer.close()

    # Get the value of the BytesIO buffer
    excel_data = buffer.getvalue()

    # Generate a base64 encoded string
    b64 = base64.b64encode(excel_data).decode()

    # Generate download link
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">{link_text}</a>'

    return href

def display_gift_summary(gifts, budget, customer_type, order_data, gift_values=None):
    """
    Display a summary of the gift allocation

    Args:
        gifts (dict): Dictionary of gift quantities
        budget (float): Available budget
        customer_type (CustomerType): Type of customer
        order_data (dict): Order summary data
        gift_values (dict, optional): Dictionary of gift values. Defaults to None.
    """
    if gift_values is None:
        gift_values = {
            "Pack FOC": gifts.get("Pack FOC", 0) * 38,
            "Hookah": gifts.get("Hookah", 0) * 400
        }

    # Create DataFrame for gift summary
    gift_df = pd.DataFrame({
        "Gift Type": list(gift_values.keys()),
        "Quantity": [gifts.get(gift, 0) for gift in gift_values.keys()],
        "Value": [gift_values[gift] for gift in gift_values.keys()]
    })

    # Display gift summary in a table
    st.write("### Gift Summary")
    st.dataframe(gift_df, use_container_width=True)

    # Calculate total gift value and remaining budget
    total_gift_value = sum(gift_values.values())
    remaining_budget = budget - total_gift_value

    # Display budget metrics
    budget_cols = st.columns(4)
    with budget_cols[0]:
        st.metric("Available Budget", f"${budget:.2f}")
    with budget_cols[1]:
        st.metric("Total Gift Value", f"${total_gift_value:.2f}")
    with budget_cols[2]:
        st.metric("Remaining Budget", f"${remaining_budget:.2f}")
    with budget_cols[3]:
        # Calculate actual ROI
        actual_roi = calculate_roi(order_data, gifts, budget)
        st.metric("Actual ROI", f"{actual_roi:.2f}%")

    # Create a pie chart showing gift value distribution
    gift_values_filtered = {k: v for k, v in gift_values.items() if v > 0}
    if gift_values_filtered:
        fig = px.pie(
            values=list(gift_values_filtered.values()),
            names=list(gift_values_filtered.keys()),
            title="Gift Value Distribution"
        )
        # Add a unique key to prevent duplicate chart ID errors
        chart_key = f"chart_{hash(str(gifts))}_{hash(str(budget))}"
        st.plotly_chart(fig, use_container_width=True, key=chart_key)

    # Create export data
    export_data = pd.DataFrame([
        {"Category": "Customer Information", "Item": "Customer Name", "Value": st.session_state.customer_name if st.session_state.customer_name else "N/A"},
        {"Category": "Customer Information", "Item": "Customer Address", "Value": st.session_state.customer_address if st.session_state.customer_address else "N/A"},
        {"Category": "Customer Information", "Item": "Customer Type", "Value": "Tobacco Shop" if customer_type == CustomerType.TOBACCO_SHOP else "Retailer"},
        {"Category": "Order Information", "Item": "Total Order Value", "Value": f"${order_data['total_value']:.2f}"},
        {"Category": "Order Information", "Item": "Number of 50g Packs", "Value": str(order_data['quantities'].get('50g', 0))},
        {"Category": "Order Information", "Item": "Number of 250g Packs", "Value": str(order_data['quantities'].get('250g', 0))},
        {"Category": "Order Information", "Item": "Number of 1kg Packs", "Value": str(order_data['quantities'].get('1kg', 0))},
        {"Category": "Gift Details", "Item": "Pack FOC Quantity", "Value": str(gifts.get("Pack FOC", 0))},
        {"Category": "Gift Details", "Item": "Hookah Quantity", "Value": str(gifts.get("Hookah", 0))},
        {"Category": "Budget Information", "Item": "Available Budget", "Value": f"${budget:.2f}"},
        {"Category": "Budget Information", "Item": "Total Gift Value", "Value": f"${total_gift_value:.2f}"},
        {"Category": "Budget Information", "Item": "Remaining Budget", "Value": f"${remaining_budget:.2f}"},
        {"Category": "Budget Information", "Item": "Actual ROI", "Value": f"{actual_roi:.2f}%"}
    ])

    # Create timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create download link
    download_link = create_excel_download_link(export_data, f"al_fakher_offer_{timestamp}.xlsx")

    # Display download link
    st.markdown(download_link, unsafe_allow_html=True)

def adjust_gifts_for_tier_roi(order_data, eligible_tier, custom_gifts, budget):
    """
    Adjust gift quantities to maintain the ROI percentage of the eligible tier

    Args:
        order_data (dict): Order summary data
        eligible_tier (str): Name of the eligible tier (e.g., 'Silver', 'Gold')
        custom_gifts (dict): Current custom gift quantities
        budget (float): Available budget

    Returns:
        dict: Adjusted gift quantities
    """
    if not eligible_tier:
        return custom_gifts

    # Define tier ROI percentages
    tier_roi = {
        'Silver': 13.0,
        'Gold': 14.5,
        'Diamond': 16.0,
        'Platinum': 18.0
    }

    # Calculate current ROI with custom gifts
    current_roi = calculate_roi(order_data, custom_gifts, budget)

    # Get target ROI for the tier
    target_roi = tier_roi.get(eligible_tier, 13.0)

    # If current ROI is already lower than or equal to target, no adjustment needed
    if current_roi <= target_roi:
        return custom_gifts

    # Clone the gifts to avoid modifying the original
    adjusted_gifts = custom_gifts.copy()

    # Gradually reduce Pack FOC until ROI is below or equal to target
    while calculate_roi(order_data, adjusted_gifts, budget) > target_roi:
        if adjusted_gifts.get("Pack FOC", 0) > 0:
            adjusted_gifts["Pack FOC"] = max(0, adjusted_gifts["Pack FOC"] - 1)
        else:
            # If Pack FOC is also 0, reduce Hookah if present
            if adjusted_gifts.get("Hookah", 0) > 0:
                adjusted_gifts["Hookah"] = max(0, adjusted_gifts["Hookah"] - 1)
            else:
                # Cannot reduce further
                break

    return adjusted_gifts

def reset_all_calculations():
    """
    Reset all calculation-related session state variables but keep customer info and price data
    """
    # Get current price data and customer info
    price_data = st.session_state.get('price_data', DEFAULT_PRICES)
    customer_name = st.session_state.get('customer_name', "")
    customer_address = st.session_state.get('customer_address', "")
    customer_type = st.session_state.get('customer_type', CustomerType.RETAILER)

    # Get list of keys to preserve
    preserve_keys = ['price_data', 'customer_name', 'customer_address', 'customer_type']

    # Clear all custom gift related session state
    custom_gift_keys = [
        'custom_pack_foc', 'custom_hookah',
        'original_gifts', 'custom_gifts', 'applied_custom_gifts'
    ]
    for key in custom_gift_keys:
        if key in st.session_state:
            del st.session_state[key]

    # Clear other calculation variables
    for key in list(st.session_state.keys()):
        if key not in preserve_keys and not key.startswith('_'):
            try:
                del st.session_state[key]
            except:
                pass  # Ignore any keys that can't be deleted

    # Restore price data and customer info
    st.session_state.price_data = price_data
    st.session_state.customer_name = customer_name
    st.session_state.customer_address = customer_address
    st.session_state.customer_type = customer_type

def main():
    # Use the session state for price data
    if 'price_data' not in st.session_state or st.session_state.price_data is None:
        st.session_state.price_data = DEFAULT_PRICES

    # Initialize customer information in session state if not present
    if 'customer_name' not in st.session_state:
        st.session_state.customer_name = ""
    if 'customer_address' not in st.session_state:
        st.session_state.customer_address = ""

    # Customer information section
    st.header("Customer Information")
    col1, col2 = st.columns(2)

    with col1:
        customer_name = st.text_input("Customer Name", value=st.session_state.customer_name)
        st.session_state.customer_name = customer_name

    with col2:
        customer_address = st.text_area("Customer Address", value=st.session_state.customer_address, height=100)
        st.session_state.customer_address = customer_address

    # Order input section
    st.header("Order Information")

    # Customer type selection
    customer_type_str = st.radio(
        "Customer Type",
        ["Retailer", "Tobacco Shop"],
        index=0,
        horizontal=True
    )
    customer_type = CustomerType.RETAILER if customer_type_str == "Retailer" else CustomerType.TOBACCO_SHOP

    # Package quantities
    st.subheader("Enter Package Quantities")

    # Create 3 columns for the 3 package sizes
    col1, col2, col3 = st.columns(3)

    with col1:
        qty_50g = st.number_input("50g Packs", min_value=0, value=0, step=1)

    with col2:
        qty_250g = st.number_input("250g Packs", min_value=0, value=0, step=1)

    with col3:
        qty_1kg = st.number_input("1kg Packs", min_value=0, value=0, step=1)

    # Create order quantities dictionary
    quantities = {
        "50g": qty_50g,
        "250g": qty_250g,
        "1kg": qty_1kg
    }

    # Generate order summary
    order_data = generate_order_summary(st.session_state.price_data, quantities)

    # Calculate total grams ordered
    total_grams = 0
    for size, quantity in order_data["quantities"].items():
        if size == "50g":
            total_grams += quantity * 50
        elif size == "250g":
            total_grams += quantity * 250
        elif size == "1kg":
            total_grams += quantity * 1000

    # Check if 1kg size was ordered for tier eligibility
    has_1kg_order = order_data["quantities"].get("1kg", 0) > 0

    # Get eligible tier
    if total_grams < 6000:
        # Not eligible for any gifts
        is_eligible = False
        eligible_tier = "Silver"  # Default to Silver, but won't be shown if not eligible
    else:
        is_eligible = True
        eligible_tier = "Silver"
        if total_grams >= 246050 and has_1kg_order:
            eligible_tier = "Platinum"
        elif total_grams >= 126050 and has_1kg_order:
            eligible_tier = "Diamond"
        elif total_grams >= 66050 and has_1kg_order:
            eligible_tier = "Gold"

    # Display order summary
    st.subheader("Order Summary")

    # Show total order value and tier status
    if is_eligible:
        st.success(f"Order Total: ${order_data['total_value']:.2f} - Total Weight: {total_grams/1000:.1f}kg")
        st.success(f"Eligible for **{eligible_tier}** tier")
    else:
        st.warning(f"Order Total: ${order_data['total_value']:.2f} - Total Weight: {total_grams/1000:.1f}kg")
        st.warning("This order is not eligible for gifts yet. Minimum order requirement: 6kg or more.")

    # Check gift eligibility based on specific product quantities
    product_eligible = is_eligible_for_gift(order_data)
    
    # Show the gift eligibility status
    if is_eligible and product_eligible:
        st.success("This order qualifies for promotional gifts!")
    elif is_eligible and not product_eligible:
        st.warning("Order meets tier weight requirements but not product mix requirements. Need 10+ packs of 50g, 3+ packs of 250g, or 2+ packs of 1kg.")
        return  # Skip gift calculations if not eligible
    elif not is_eligible:
        st.warning("This order does not meet the minimum requirements for gifts.")
        return  # Skip gift calculations if not eligible

    # Target ROI selection based on tier
    tier_roi = {
        'Silver': 5.0,
        'Gold': 7.0,
        'Diamond': 9.0,
        'Platinum': 13.0
    }
    target_roi = tier_roi.get(eligible_tier, 5.0)

    # Gift calculation section
    st.header("Gift Calculator")

    # Add option to use custom ROI
    use_custom_roi = st.checkbox("Use Custom ROI")
    
    if use_custom_roi:
        target_roi = st.slider("Target ROI (%)", min_value=1.0, max_value=20.0, value=target_roi, step=0.5)

    # Calculate budget based on the selected ROI
    budget = calculate_budget_from_roi(order_data, target_roi)
    st.info(f"Available Budget: ${budget:.2f} (based on {target_roi:.1f}% ROI)")

    # Get gift recommendation
    recommended_gifts = recommend_gift(order_data, customer_type, budget)
    
    # Calculate the actual cost of recommended gifts
    recommended_gift_value = {
        "Pack FOC": recommended_gifts["Pack FOC"] * 38,
        "Hookah": recommended_gifts["Hookah"] * 400
    }
    
    # Store original gifts to compare with custom
    if 'original_gifts' not in st.session_state:
        st.session_state.original_gifts = recommended_gifts.copy()

    # Check if custom gift adjustment is requested
    custom_mode = st.checkbox("Customize Gifts")

    if custom_mode:
        st.subheader("Custom Gift Allocation")
        
        # Get maximum gift quantities based on budget
        max_quantities = get_max_gift_quantities(budget, customer_type, order_data['total_value'])
        
        # Store custom gifts in session state to persist during re-renders
        if 'custom_pack_foc' not in st.session_state:
            st.session_state.custom_pack_foc = recommended_gifts["Pack FOC"]
        if 'custom_hookah' not in st.session_state:
            st.session_state.custom_hookah = recommended_gifts["Hookah"]
        
        # Custom input fields with recommended values as defaults
        custom_cols = st.columns(2)
        
        with custom_cols[0]:
            st.session_state.custom_pack_foc = st.number_input(
                "Pack FOC Quantity", 
                min_value=0, 
                max_value=max_quantities["Pack FOC"],
                value=st.session_state.custom_pack_foc
            )
            
        with custom_cols[1]:
            if customer_type == CustomerType.TOBACCO_SHOP:
                st.session_state.custom_hookah = st.number_input(
                    "Hookah Quantity", 
                    min_value=0, 
                    max_value=max_quantities["Hookah"],
                    value=st.session_state.custom_hookah
                )
            else:
                st.info("Hookahs are only available for Tobacco Shops")
                st.session_state.custom_hookah = 0
        
        # Create custom gifts dictionary
        custom_gifts = {
            "Pack FOC": st.session_state.custom_pack_foc,
            "Hookah": st.session_state.custom_hookah
        }
        
        # Store custom gifts in session state
        st.session_state.custom_gifts = custom_gifts
        
        # Button to apply custom allocation
        if st.button("Apply Custom Allocation"):
            st.session_state.applied_custom_gifts = custom_gifts.copy()
            st.success("Custom gift allocation applied!")
            
        # Check if we have applied custom gifts
        if 'applied_custom_gifts' in st.session_state:
            # Adjust custom gifts to maintain tier ROI if needed
            adjusted_gifts = st.session_state.applied_custom_gifts
            
            # Calculate custom gift values
            custom_gift_values = {
                "Pack FOC": adjusted_gifts["Pack FOC"] * 38,
                "Hookah": adjusted_gifts["Hookah"] * 400
            }
            
            # Display the custom gift summary
            st.subheader("Custom Gift Summary")
            display_gift_summary(adjusted_gifts, budget, customer_type, order_data, custom_gift_values)
    else:
        # Display the recommended gift summary
        st.subheader("Recommended Gift Allocation")
        display_gift_summary(recommended_gifts, budget, customer_type, order_data, recommended_gift_value)

    # Reset button to clear all calculations
    if st.button("Reset Calculations"):
        reset_all_calculations()
        st.rerun()

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
