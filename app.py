import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import base64
from io import BytesIO
import os
from PIL import Image

# Import local modules
from utils import load_csv, validate_csv, generate_order_summary, is_eligible_for_gift, calculate_gift_value, get_max_gift_quantities
from models import CustomerType, Offer, Gift
from algorithms import recommend_gift, calculate_budget_from_roi, calculate_roi, optimize_budget

def to_excel(df):
    """
    Convert a DataFrame to Excel bytes
    
    Args:
        df (pandas.DataFrame): DataFrame to convert
        
    Returns:
        bytes: Excel file as bytes
    """
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Sheet1', index=False)
    processed_data = output.getvalue()
    return processed_data

def get_table_download_link(df, filename, text):
    """
    Generate a download link for a DataFrame
    
    Args:
        df (pandas.DataFrame): DataFrame to download
        filename (str): Filename for download
        text (str): Link text
        
    Returns:
        str: HTML link for download
    """
    val = to_excel(df)
    b64 = base64.b64encode(val).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">{text}</a>'

def get_tier_requirements(tier):
    """
    Get the requirements for a specific tier
    
    Args:
        tier (str): Tier name
        
    Returns:
        tuple: (min_grams, max_grams, requires_1kg)
    """
    if tier == "Silver":
        return (6000, 60000, False)
    elif tier == "Gold":
        return (66050, 120000, True)
    elif tier == "Diamond":
        return (126050, 240000, True)
    elif tier == "Platinum":
        return (246050, float("inf"), True)
    return (0, 0, False)

def get_eligible_tier(total_grams, has_1kg_order):
    """
    Determine eligible tier based on total grams ordered
    
    Args:
        total_grams (float): Total grams ordered
        has_1kg_order (bool): Whether 1kg size was ordered
        
    Returns:
        str: Eligible tier name or None
    """
    if total_grams < 6000:
        return None  # No tier eligible
    elif 6000 <= total_grams <= 60000:
        return "Silver"
    elif 66050 <= total_grams <= 120000:
        return "Gold" if has_1kg_order else "Silver"
    elif 126050 <= total_grams <= 240000:
        return "Diamond" if has_1kg_order else "Silver"
    elif total_grams >= 246050:
        return "Platinum" if has_1kg_order else "Silver"
    return None

def create_offer_table(offers):
    """
    Create a DataFrame for display of offers
    
    Args:
        offers (list): List of Offer objects
        
    Returns:
        pandas.DataFrame: Formatted offer data
    """
    if not offers:
        return None
    
    data = []
    for offer in offers:
        data.append({
            "Tier": offer.name,
            "Target ROI": f"{offer.roi_percentage:.1f}%",
            "Budget": f"${offer.budget:.2f}",
            "Actual ROI": f"{offer.actual_roi:.1f}%",
            "Pack FOC": offer.gifts.get("Pack FOC", 0),
            "Hookah": offer.gifts.get("Hookah", 0),
            "AF Points": offer.gifts.get("AF Points", 0),
            "Cash Back": f"{offer.gifts.get('Cash Back %', 0):.1f}%"
        })
    
    return pd.DataFrame(data)

# Define a reset function to clear session state
def reset_calculator():
    """Reset all calculator-related session state variables"""
    # Use a reset flag to trigger actions on next rerun
    st.session_state.reset_triggered = True
    
    # Clear data-related state vars
    for key in ['uploaded_data', 'order_data', 'eligible_tier', 'offers', 
                'last_offer_tier', 'adjusted_gifts', 'original_gifts']:
        if key in st.session_state:
            del st.session_state[key]
    
    # We'll handle the slider resets by checking for reset_triggered flag
    # before the sliders are instantiated in the UI

# Function to recalculate gifts based on current order data
def update_gifts():
    """Recalculate all gifts based on current order data"""
    if st.session_state.order_data is None:
        return
        
    # Calculate total grams ordered
    total_grams = 0
    for size, quantity in st.session_state.order_data["quantities"].items():
        if size == "50g":
            total_grams += quantity * 50
        elif size == "250g":
            total_grams += quantity * 250
        elif size == "1kg":
            total_grams += quantity * 1000
                
    # Check if 1kg size was ordered for tier eligibility
    has_1kg_order = st.session_state.order_data["quantities"].get("1kg", 0) > 0
    
    # Determine eligible tier based on total grams ordered
    eligible_tier = get_eligible_tier(total_grams, has_1kg_order)
    
    # Store eligible tier in session state
    st.session_state.eligible_tier = eligible_tier
    
    # Store customer info in session state if present
    if 'customer_name' not in st.session_state:
        st.session_state.customer_name = ""
    if 'customer_address' not in st.session_state:
        st.session_state.customer_address = ""
    
    # Generate offer tiers based on eligibility
    st.session_state.offers = []
    
    if eligible_tier == "Silver" or eligible_tier == "Gold" or eligible_tier == "Diamond" or eligible_tier == "Platinum":
        silver_offer = Offer("Silver", 5.0)
        silver_offer.budget = calculate_budget_from_roi(st.session_state.order_data, 5.0)
        silver_offer.gifts = optimize_budget(st.session_state.order_data, st.session_state.customer_type, 5.0)
        silver_offer.actual_roi = calculate_roi(st.session_state.order_data, silver_offer.gifts, silver_offer.budget)
        st.session_state.offers.append(silver_offer)
        
    if eligible_tier == "Gold" or eligible_tier == "Diamond" or eligible_tier == "Platinum":
        gold_offer = Offer("Gold", 7.0)
        gold_offer.budget = calculate_budget_from_roi(st.session_state.order_data, 7.0)
        gold_offer.gifts = optimize_budget(st.session_state.order_data, st.session_state.customer_type, 7.0)
        gold_offer.actual_roi = calculate_roi(st.session_state.order_data, gold_offer.gifts, gold_offer.budget)
        st.session_state.offers.append(gold_offer)
        
    if eligible_tier == "Diamond" or eligible_tier == "Platinum":
        diamond_offer = Offer("Diamond", 9.0)
        diamond_offer.budget = calculate_budget_from_roi(st.session_state.order_data, 9.0)
        diamond_offer.gifts = optimize_budget(st.session_state.order_data, st.session_state.customer_type, 9.0)
        diamond_offer.actual_roi = calculate_roi(st.session_state.order_data, diamond_offer.gifts, diamond_offer.budget)
        st.session_state.offers.append(diamond_offer)
        
    if eligible_tier == "Platinum":
        platinum_offer = Offer("Platinum", 13.0)
        platinum_offer.budget = calculate_budget_from_roi(st.session_state.order_data, 13.0)
        platinum_offer.gifts = optimize_budget(st.session_state.order_data, st.session_state.customer_type, 13.0)
        platinum_offer.actual_roi = calculate_roi(st.session_state.order_data, platinum_offer.gifts, platinum_offer.budget)
        st.session_state.offers.append(platinum_offer)
    
    # Clear adjusted gifts data to reset sliders
    if 'last_offer_tier' in st.session_state:
        del st.session_state.last_offer_tier
    if 'adjusted_gifts' in st.session_state:
        del st.session_state.adjusted_gifts
    if 'original_gifts' in st.session_state:
        del st.session_state.original_gifts
    if 'hookah_slider' in st.session_state:
        del st.session_state.hookah_slider
    if 'pack_foc_slider' in st.session_state:
        del st.session_state.pack_foc_slider
    if 'af_points_slider' in st.session_state:
        del st.session_state.af_points_slider
    if 'cashback_slider' in st.session_state:
        del st.session_state.cashback_slider

# New function to recalculate gift sliders when one is changed
def recalculate_gifts(changed_gift_type):
    """
    Recalculate gift allocations based on the slider that was changed
    
    Args:
        changed_gift_type (str): Type of gift that was changed
    """
    if 'last_offer_tier' not in st.session_state or 'adjusted_gifts' not in st.session_state:
        return
        
    # Get the selected offer
    selected_offer = None
    for offer in st.session_state.offers:
        if offer.name == st.session_state.last_offer_tier:
            selected_offer = offer
            break
    
    if selected_offer is None:
        return
        
    # Get original budget and total gift value
    original_budget = selected_offer.budget
    order_value = st.session_state.order_data["total_value"]
    
    # Get current values from sliders
    current_values = {
        "Hookah": st.session_state.get("hookah_slider", 0),
        "Pack FOC": st.session_state.get("pack_foc_slider", 0),
        "AF Points": st.session_state.get("af_points_slider", 0),
        "Cash Back %": st.session_state.get("cashback_slider", 0)
    }
    
    # Calculate current costs for each gift type
    costs = {
        "Hookah": current_values["Hookah"] * 400,
        "Pack FOC": current_values["Pack FOC"] * 38,
        "AF Points": current_values["AF Points"] * 1,
        "Cash Back %": (current_values["Cash Back %"] / 100) * order_value
    }
    
    # Calculate the cost of the changed gift
    changed_cost = costs[changed_gift_type]
    
    # Calculate how much budget remains for other gifts
    remaining_budget = original_budget - changed_cost
    
    # Get the other gift types (excluding the one that was changed)
    other_gifts = [gift for gift in costs.keys() if gift != changed_gift_type]
    
    # Calculate the total cost of the other gifts before adjustment
    other_costs = {gift: costs[gift] for gift in other_gifts}
    total_other_cost = sum(other_costs.values())
    
    # If total other cost is 0, distribute remaining budget with priority
    if total_other_cost <= 0:
        # If we've exceeded the budget, set other gifts to 0
        if remaining_budget <= 0:
            for gift in other_gifts:
                if gift == "Hookah":
                    st.session_state.hookah_slider = 0
                elif gift == "Pack FOC":
                    st.session_state.pack_foc_slider = 0
                elif gift == "AF Points":
                    st.session_state.af_points_slider = 0
                elif gift == "Cash Back %":
                    st.session_state.cashback_slider = 0
            return
            
        # Simple prioritized allocation
        if "Hookah" in other_gifts and st.session_state.customer_type == CustomerType.TOBACCO_SHOP and remaining_budget >= 400:
            st.session_state.hookah_slider = min(int(remaining_budget / 400), 2)
            remaining_budget -= st.session_state.hookah_slider * 400
        
        if "Pack FOC" in other_gifts and remaining_budget >= 38:
            st.session_state.pack_foc_slider = int(remaining_budget / 38)
            remaining_budget -= st.session_state.pack_foc_slider * 38
            
        if "AF Points" in other_gifts and remaining_budget > 0:
            st.session_state.af_points_slider = int(remaining_budget)
            remaining_budget -= st.session_state.af_points_slider
            
        if "Cash Back %" in other_gifts and remaining_budget > 0 and order_value > 0:
            cashback_percent = min(30, (remaining_budget / order_value) * 100)
            st.session_state.cashback_slider = round(cashback_percent, 1)
    else:
        # Calculate proportions of each gift based on original amounts
        proportions = {gift: other_costs[gift] / total_other_cost for gift in other_gifts}
        
        # If we've exceeded the budget, set other gifts to 0
        if remaining_budget <= 0:
            for gift in other_gifts:
                if gift == "Hookah":
                    st.session_state.hookah_slider = 0
                elif gift == "Pack FOC":
                    st.session_state.pack_foc_slider = 0
                elif gift == "AF Points":
                    st.session_state.af_points_slider = 0
                elif gift == "Cash Back %":
                    st.session_state.cashback_slider = 0
            return
        
        # Distribute remaining budget proportionally
        for gift in other_gifts:
            allocated_budget = remaining_budget * proportions[gift]
            
            if gift == "Hookah":
                if allocated_budget >= 400:
                    st.session_state.hookah_slider = min(int(allocated_budget / 400), 2)
                else:
                    st.session_state.hookah_slider = 0
            elif gift == "Pack FOC":
                if allocated_budget >= 38:
                    st.session_state.pack_foc_slider = int(allocated_budget / 38)
                else:
                    st.session_state.pack_foc_slider = 0
            elif gift == "AF Points":
                st.session_state.af_points_slider = int(allocated_budget)
            elif gift == "Cash Back %" and order_value > 0:
                cashback_percent = min(30, (allocated_budget / order_value) * 100)
                st.session_state.cashback_slider = round(cashback_percent, 1)
    
    # Update the adjusted gifts dictionary
    st.session_state.adjusted_gifts = {
        "Hookah": st.session_state.hookah_slider,
        "Pack FOC": st.session_state.pack_foc_slider,
        "AF Points": st.session_state.af_points_slider,
        "Cash Back %": st.session_state.cashback_slider
    }

def main():
    # Check if we need to do a full reset (triggered by the Start New Calculation button)
    if 'reset_triggered' in st.session_state and st.session_state.reset_triggered:
        # Clean up slider keys completely from session state before widgets are instantiated
        for key in ['hookah_slider', 'pack_foc_slider', 'af_points_slider', 'cashback_slider']:
            if key in st.session_state:
                del st.session_state[key]
        
        # Clear reset flag
        del st.session_state.reset_triggered
    
    # Check if we need to reset allocation values
    if 'reset_allocation' in st.session_state and st.session_state.reset_allocation:
        # Reset values from temp storage
        st.session_state['hookah_slider'] = st.session_state.get('temp_hookah', 0)
        st.session_state['pack_foc_slider'] = st.session_state.get('temp_pack_foc', 0)
        st.session_state['af_points_slider'] = st.session_state.get('temp_af_points', 0)
        st.session_state['cashback_slider'] = st.session_state.get('temp_cashback', 0)
        st.session_state['adjusted_gifts'] = st.session_state.original_gifts.copy()
        
        # Clear reset flag
        del st.session_state['reset_allocation']
        del st.session_state['temp_hookah']
        del st.session_state['temp_pack_foc']
        del st.session_state['temp_af_points']
        del st.session_state['temp_cashback']
    
    # Initialize session state variables if they don't exist
    if 'price_data' not in st.session_state:
        # Try to load the default price data
        try:
            default_price_data = pd.read_csv("Prices.csv")
            if validate_csv(default_price_data):
                st.session_state.price_data = default_price_data
        except:
            st.session_state.price_data = None
    
    if 'uploaded_data' not in st.session_state:
        st.session_state.uploaded_data = None
    
    if 'order_data' not in st.session_state:
        st.session_state.order_data = None
    
    if 'customer_type' not in st.session_state:
        st.session_state.customer_type = CustomerType.RETAILER
    
    if 'offers' not in st.session_state:
        st.session_state.offers = []
        
    # Initialize gift slider variables to prevent AttributeError
    if 'hookah_slider' not in st.session_state:
        st.session_state.hookah_slider = 0
        
    if 'pack_foc_slider' not in st.session_state:
        st.session_state.pack_foc_slider = 0
        
    if 'af_points_slider' not in st.session_state:
        st.session_state.af_points_slider = 0
        
    if 'cashback_slider' not in st.session_state:
        st.session_state.cashback_slider = 0
        
    if 'last_offer_tier' not in st.session_state:
        st.session_state.last_offer_tier = None
        
    if 'adjusted_gifts' not in st.session_state:
        st.session_state.adjusted_gifts = {
            "Hookah": 0,
            "Pack FOC": 0,
            "AF Points": 0,
            "Cash Back %": 0
        }
        
    if 'original_gifts' not in st.session_state:
        st.session_state.original_gifts = {
            "Hookah": 0,
            "Pack FOC": 0,
            "AF Points": 0,
            "Cash Back %": 0
        }
    
    # Create tabs for the main application
    tabs = st.tabs(["Order and Gift Calculation", "Export"])
    
    # Tab 1: Combined Order and Gift Calculation
    with tabs[0]:
        st.subheader("Customer Information")
        
        # Customer info
        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input("Customer Name", 
                                         value=st.session_state.get('customer_name', ''))
            st.session_state.customer_name = customer_name
            
        with col2:
            customer_type = st.selectbox(
                "Customer Type",
                ["Retailer", "Tobacco Shop"],
                index=0 if st.session_state.customer_type == CustomerType.RETAILER else 1
            )
            st.session_state.customer_type = CustomerType.RETAILER if customer_type == "Retailer" else CustomerType.TOBACCO_SHOP
            
        customer_address = st.text_area("Address", 
                                       value=st.session_state.get('customer_address', ''),
                                       height=100)
        st.session_state.customer_address = customer_address
        
        st.divider()
        
        st.subheader("Price Data")
        
        # Price data upload or use default
        col1, col2 = st.columns([1, 2])
        with col1:
            use_default_data = st.checkbox("Use Default Prices", 
                                          value=True if st.session_state.price_data is not None and st.session_state.uploaded_data is None else False)
        
        with col2:
            if not use_default_data:
                uploaded_file = st.file_uploader("Upload Price Data (CSV)", type=["csv"], key="trade_offer_uploader")
                if uploaded_file is not None:
                    try:
                        data = load_csv(uploaded_file)
                        if validate_csv(data):
                            st.session_state.price_data = data
                            st.session_state.uploaded_data = uploaded_file.name
                            st.success(f"Successfully loaded {uploaded_file.name}")
                        else:
                            st.error("Invalid CSV format. File must contain 'Size' and 'Price/Pack' columns.")
                    except Exception as e:
                        st.error(f"Error loading file: {str(e)}")
            else:
                if st.session_state.price_data is not None:
                    st.success("Using default price data")
                else:
                    st.error("Default price data not available. Please upload a CSV file.")
        
        # Show price data if available
        if st.session_state.price_data is not None:
            st.dataframe(st.session_state.price_data, use_container_width=True)
        
        st.divider()
        
        st.subheader("Order Quantities")
        
        # Order quantities input
        col1, col2, col3 = st.columns(3)
        with col1:
            qty_50g = st.number_input("50g Quantity", min_value=0, value=0, step=1)
        with col2:
            qty_250g = st.number_input("250g Quantity", min_value=0, value=0, step=1)
        with col3:
            qty_1kg = st.number_input("1kg Quantity", min_value=0, value=0, step=1)
        
        # Create columns for buttons
        col1, col2 = st.columns(2)
        
        # Button to calculate
        with col1:
            calculate_clicked = st.button("Calculate Order")
        
        # Button to reset
        with col2:
            reset_clicked = st.button("Reset Calculation")
            
        if reset_clicked:
            reset_calculator()
            st.rerun()
            
        if calculate_clicked:
            if st.session_state.price_data is not None:
                # Create quantities dictionary
                quantities = {
                    "50g": qty_50g,
                    "250g": qty_250g,
                    "1kg": qty_1kg
                }
                
                # Generate order summary
                order_data = generate_order_summary(st.session_state.price_data, quantities)
                st.session_state.order_data = order_data
                
                # Update gift calculations
                update_gifts()
                
                # Get eligible tier information
                eligible_tier = st.session_state.eligible_tier
                
                # Display success message with tier information
                if eligible_tier:
                    st.success(f"Order calculated successfully! This order qualifies for the **{eligible_tier} Tier**.")
                else:
                    st.success("Order calculated successfully! This order does not qualify for any tier yet.")
            else:
                st.error("Price data is required. Please upload a CSV file or use default prices.")
    
    # Continue with gift calculation section of the same tab if order data exists
        if st.session_state.order_data is not None:
            st.divider()
            
            # Add the gift calculation section after the order calculation
            st.subheader("Gift Calculation")
            
            # Display order summary
            st.subheader("Order Summary")
            col1, col2 = st.columns(2)
            
            with col1:
                total_value = st.session_state.order_data["total_value"]
                st.metric("Total Order Value", f"${total_value:.2f}")
                
                # Show quantities
                quantities = st.session_state.order_data["quantities"]
                qty_summary = []
                if quantities.get("50g", 0) > 0:
                    qty_summary.append(f"{quantities['50g']} x 50g")
                if quantities.get("250g", 0) > 0:
                    qty_summary.append(f"{quantities['250g']} x 250g")
                if quantities.get("1kg", 0) > 0:
                    qty_summary.append(f"{quantities['1kg']} x 1kg")
                
                st.write("Quantities: " + ", ".join(qty_summary))
            
            with col2:
                # Calculate total grams for tier determination
                total_grams = 0
                for size, quantity in quantities.items():
                    if size == "50g":
                        total_grams += quantity * 50
                    elif size == "250g":
                        total_grams += quantity * 250
                    elif size == "1kg":
                        total_grams += quantity * 1000
                
                st.metric("Total Weight", f"{total_grams:,}g")
                st.write(f"Eligible Tier: {st.session_state.eligible_tier if st.session_state.eligible_tier else 'None'}")
            
            # Check eligibility
            is_eligible = is_eligible_for_gift(st.session_state.order_data)
            
            if not is_eligible:
                st.warning(
                    "This order is not eligible for gifts. "
                    "Minimum requirements: 10+ packs of 50g, 3+ packs of 250g, or 2+ packs of 1kg."
                )
            else:
                if not st.session_state.offers:
                    st.error("No eligible offers available for this order.")
                else:
                    # Create offer table
                    offer_table = create_offer_table(st.session_state.offers)
                    
                    # Display offers
                    st.subheader("Available Offers")
                    st.dataframe(offer_table, use_container_width=True)
                    
                    # Allow user to select an offer for adjustment
                    offer_tiers = [offer.name for offer in st.session_state.offers]
                    selected_tier = st.selectbox(
                        "Select Offer Tier for Adjustment", 
                        offer_tiers,
                        index=0
                    )
                    
                    # Find the selected offer
                    selected_offer = None
                    for offer in st.session_state.offers:
                        if offer.name == selected_tier:
                            selected_offer = offer
                            break
                    
                    if selected_offer:
                        st.write(f"Budget: ${selected_offer.budget:.2f}")
                        
                        # Initialize or update adjusted gifts in session state
                        if 'last_offer_tier' not in st.session_state or st.session_state.last_offer_tier != selected_tier:
                            st.session_state.last_offer_tier = selected_tier
                            st.session_state.original_gifts = selected_offer.gifts.copy()
                            st.session_state.adjusted_gifts = selected_offer.gifts.copy()
                            
                            # Set initial slider values
                            st.session_state.hookah_slider = selected_offer.gifts.get("Hookah", 0)
                            st.session_state.pack_foc_slider = selected_offer.gifts.get("Pack FOC", 0)
                            st.session_state.af_points_slider = selected_offer.gifts.get("AF Points", 0)
                            st.session_state.cashback_slider = selected_offer.gifts.get("Cash Back %", 0)
                        
                        # Display gift adjustment sliders
                        st.subheader("Adjust Gift Allocation")
                        
                        # Get maximum gift values based on budget
                        max_quantities = get_max_gift_quantities(selected_offer.budget, st.session_state.customer_type, st.session_state.order_data["total_value"])
                        
                        # Define callback functions for sliders
                        def on_hookah_change():
                            recalculate_gifts("Hookah")
                            
                        def on_pack_foc_change():
                            recalculate_gifts("Pack FOC")
                            
                        def on_af_points_change():
                            recalculate_gifts("AF Points")
                            
                        def on_cashback_change():
                            recalculate_gifts("Cash Back %")
                        
                        # Create columns for sliders
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Only show hookah slider for tobacco shops
                            if st.session_state.customer_type == CustomerType.TOBACCO_SHOP:
                                st.slider(
                                    "Hookah (400 USD each)",
                                    min_value=0,
                                    max_value=max_quantities["Hookah"],
                                    value=st.session_state.hookah_slider,
                                    step=1,
                                    key="hookah_slider",
                                    on_change=on_hookah_change
                                )
                            
                            st.slider(
                                "Pack FOC (38 USD each)",
                                min_value=0,
                                max_value=max_quantities["Pack FOC"],
                                value=st.session_state.pack_foc_slider,
                                step=1,
                                key="pack_foc_slider",
                                on_change=on_pack_foc_change
                            )
                        
                        with col2:
                            st.slider(
                                "AF Points (1 USD each)",
                                min_value=0,
                                max_value=max_quantities["AF Points"],
                                value=st.session_state.af_points_slider,
                                step=10,
                                key="af_points_slider",
                                on_change=on_af_points_change
                            )
                            
                            st.slider(
                                "Cash Back %",
                                min_value=0.0,
                                max_value=min(30.0, max_quantities["Cash Back %"]),
                                value=float(st.session_state.cashback_slider),
                                step=0.1,
                                key="cashback_slider",
                                on_change=on_cashback_change
                            )
                        
                        # Add Apply New Gift Adjustment button
                        if st.button("Apply New Gift Adjustment"):
                            st.success("Gift allocation has been updated!")
                            # The sliders already update the session state values automatically
                            # This button is just for user feedback
                        
                        # Display current gift values
                        gift_values = {
                            "Hookah": st.session_state.hookah_slider * 400,
                            "Pack FOC": st.session_state.pack_foc_slider * 38,
                            "AF Points": st.session_state.af_points_slider * 1,
                            "Cash Back": (st.session_state.cashback_slider / 100) * st.session_state.order_data["total_value"]
                        }
                        
                        total_gift_value = sum(gift_values.values())
                        budget_difference = total_gift_value - selected_offer.budget
                        budget_usage_percent = (total_gift_value / selected_offer.budget) * 100 if selected_offer.budget > 0 else 0
                        
                        # Display gift values
                        st.subheader("Gift Allocation Summary")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Gift Value", f"${total_gift_value:.2f}")
                        with col2:
                            st.metric("Budget", f"${selected_offer.budget:.2f}")
                        with col3:
                            st.metric("Budget Usage", f"{budget_usage_percent:.1f}%")
                        
                        # Create a DataFrame for the gift values
                        gift_df = pd.DataFrame([
                            {"Gift Type": "Hookah", "Quantity": st.session_state.hookah_slider, "Total Value": gift_values["Hookah"]},
                            {"Gift Type": "Pack FOC", "Quantity": st.session_state.pack_foc_slider, "Total Value": gift_values["Pack FOC"]},
                            {"Gift Type": "AF Points", "Quantity": st.session_state.af_points_slider, "Total Value": gift_values["AF Points"]},
                            {"Gift Type": "Cash Back", "Quantity": f"{st.session_state.cashback_slider}", "Total Value": gift_values["Cash Back"]},
                        ])
                        
                        # Format the Quantity column for display
                        gift_df["Display Quantity"] = gift_df.apply(
                            lambda row: f"{row['Quantity']}%" if row["Gift Type"] == "Cash Back" else row["Quantity"], 
                            axis=1
                        )
                        
                        # Display the gift values - use the Display Quantity column for better formatting
                        st.dataframe(
                            gift_df.drop(columns=["Quantity"]).rename(columns={"Display Quantity": "Quantity"}), 
                            use_container_width=True
                        )
                        
                        # Show reset button
                        if st.button("Reset to Original Allocation"):
                            # Store original values in temporary variables
                            hookah_val = st.session_state.original_gifts.get("Hookah", 0)
                            pack_foc_val = st.session_state.original_gifts.get("Pack FOC", 0)
                            af_points_val = st.session_state.original_gifts.get("AF Points", 0)
                            cashback_val = st.session_state.original_gifts.get("Cash Back %", 0)
                            
                            # Set reset flag to trigger value reset on next rerun
                            st.session_state['reset_allocation'] = True
                            st.session_state['temp_hookah'] = hookah_val
                            st.session_state['temp_pack_foc'] = pack_foc_val
                            st.session_state['temp_af_points'] = af_points_val
                            st.session_state['temp_cashback'] = cashback_val
                            
                            st.rerun()
    
    # Tab 2: Export
    with tabs[1]:
        if st.session_state.order_data is None:
            st.info("Please enter and calculate an order in the Order and Gift Calculation tab first.")
        elif not is_eligible_for_gift(st.session_state.order_data):
            st.warning(
                "This order is not eligible for gifts. "
                "Minimum requirements: 10+ packs of 50g, 3+ packs of 250g, or 2+ packs of 1kg."
            )
        else:
            st.subheader("Export Offer")
            
            # Customer information
            st.write("### Customer Information")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Name:** {st.session_state.customer_name}")
                st.write(f"**Type:** {st.session_state.customer_type.name.replace('_', ' ').title()}")
            with col2:
                st.write("**Address:**")
                st.write(st.session_state.customer_address)
            
            # Order information
            st.write("### Order Details")
            quantities = st.session_state.order_data["quantities"]
            prices = st.session_state.order_data["prices"]
            
            order_items = []
            for size, qty in quantities.items():
                if qty > 0:
                    order_items.append({
                        "Product": f"Al Fakher {size}",
                        "Quantity": qty,
                        "Price": prices[size],
                        "Total": qty * prices[size]
                    })
            
            order_df = pd.DataFrame(order_items)
            st.dataframe(order_df, use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Order Value", f"${st.session_state.order_data['total_value']:.2f}")
            
            # Check if we have offers and adjusted gifts
            if st.session_state.offers and 'last_offer_tier' in st.session_state:
                # Find the selected offer
                selected_offer = None
                for offer in st.session_state.offers:
                    if offer.name == st.session_state.last_offer_tier:
                        selected_offer = offer
                        break
                
                if selected_offer:
                    st.write("### Selected Offer")
                    st.write(f"**Tier:** {selected_offer.name}")
                    st.write(f"**Budget:** ${selected_offer.budget:.2f}")
                    
                    # Get current gift values
                    gift_values = {
                        "Hookah": st.session_state.hookah_slider * 400,
                        "Pack FOC": st.session_state.pack_foc_slider * 38,
                        "AF Points": st.session_state.af_points_slider * 1,
                        "Cash Back": (st.session_state.cashback_slider / 100) * st.session_state.order_data["total_value"]
                    }
                    
                    total_gift_value = sum(gift_values.values())
                    budget_usage_percent = (total_gift_value / selected_offer.budget) * 100 if selected_offer.budget > 0 else 0
                    
                    with col2:
                        st.metric("Total Gift Value", f"${total_gift_value:.2f}")
                    
                    # Create a DataFrame for the gift values
                    gift_df = pd.DataFrame([
                        {"Gift Type": "Hookah", "Quantity": st.session_state.hookah_slider, "Total Value": gift_values["Hookah"]},
                        {"Gift Type": "Pack FOC", "Quantity": st.session_state.pack_foc_slider, "Total Value": gift_values["Pack FOC"]},
                        {"Gift Type": "AF Points", "Quantity": st.session_state.af_points_slider, "Total Value": gift_values["AF Points"]},
                        {"Gift Type": "Cash Back", "Quantity": f"{st.session_state.cashback_slider}", "Total Value": gift_values["Cash Back"]},
                    ])
                    
                    # Format the Quantity column for display
                    gift_df["Display Quantity"] = gift_df.apply(
                        lambda row: f"{row['Quantity']}%" if row["Gift Type"] == "Cash Back" else row["Quantity"], 
                        axis=1
                    )
                    
                    # Display the gift values - use the Display Quantity column for better formatting
                    st.dataframe(
                        gift_df.drop(columns=["Quantity"]).rename(columns={"Display Quantity": "Quantity"}), 
                        use_container_width=True
                    )
                    
                    # Create export data
                    export_data = pd.DataFrame({
                        "Item": ["Customer Name", "Customer Type", "Address", "Order Total", "Selected Tier", 
                               "Hookah", "Pack FOC", "AF Points", "Cash Back", "Gift Total", "Budget Usage"],
                        "Value": [
                            st.session_state.customer_name,
                            st.session_state.customer_type.name.replace('_', ' ').title(),
                            st.session_state.customer_address,
                            f"${st.session_state.order_data['total_value']:.2f}",
                            selected_offer.name,
                            f"{st.session_state.hookah_slider} (${gift_values['Hookah']:.2f})",
                            f"{st.session_state.pack_foc_slider} (${gift_values['Pack FOC']:.2f})",
                            f"{st.session_state.af_points_slider} (${gift_values['AF Points']:.2f})",
                            f"{st.session_state.cashback_slider}% (${gift_values['Cash Back']:.2f})",
                            f"${total_gift_value:.2f}",
                            f"{budget_usage_percent:.1f}%"
                        ]
                    })
                    
                    # Add order details
                    export_data = pd.concat([export_data, pd.DataFrame({
                        "Item": [f"Order {size}" for size in quantities.keys() if quantities[size] > 0],
                        "Value": [f"{quantities[size]} x ${prices[size]} = ${quantities[size] * prices[size]:.2f}" 
                                 for size in quantities.keys() if quantities[size] > 0]
                    })], ignore_index=True)
                    
                    # Add download button
                    st.write("### Export Options")
                    st.write(get_table_download_link(export_data, f"al_fakher_offer_{st.session_state.customer_name.replace(' ', '_')}.xlsx", 
                                                  "Download Offer Details as Excel"), unsafe_allow_html=True)
                    
                    # Add download button for order details
                    st.write(get_table_download_link(order_df, f"al_fakher_order_{st.session_state.customer_name.replace(' ', '_')}.xlsx", 
                                                  "Download Order Details as Excel"), unsafe_allow_html=True)
            else:
                st.info("Please select and adjust an offer in the Gift Calculation section first.")
            
            # Reset button
            if st.button("Start New Calculation"):
                # We use this approach to avoid modifying session state variables directly
                # after widgets have been instantiated
                reset_calculator()
                st.rerun()

if __name__ == "__main__":
    main()
