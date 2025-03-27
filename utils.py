import pandas as pd
import numpy as np
import streamlit as st
from io import BytesIO
from models import CustomerType

def load_csv(uploaded_file):
    """
    Load and parse a CSV file into a pandas DataFrame
    
    Args:
        uploaded_file: The uploaded file object
        
    Returns:
        pandas.DataFrame: The loaded data
    """
    try:
        # Try to load directly
        return pd.read_csv(uploaded_file)
    except Exception as e:
        # Alternative approach for Replit environment
        # Read the file content to bytes and then parse
        content = uploaded_file.read()
        try:
            return pd.read_csv(BytesIO(content))
        except:
            # Convert to string if binary approach fails
            content_str = content.decode('utf-8')
            return pd.read_csv(BytesIO(content_str.encode('utf-8')))

def validate_csv(df):
    """
    Validate that the CSV has the required columns
    
    Args:
        df (pandas.DataFrame): The dataframe to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_columns = ['Size', 'Price/Pack']
    return all(column in df.columns for column in required_columns)

def generate_order_summary(price_data, quantities):
    """
    Generate an order summary based on price data and quantities
    
    Args:
        price_data (pandas.DataFrame): The price data with Size and Price/Pack columns
        quantities (dict): Dictionary mapping sizes to quantities
        
    Returns:
        dict: Order summary including quantities, prices, total value, etc.
    """
    # Create a dictionary to store prices by size
    prices = {}
    for _, row in price_data.iterrows():
        size = row['Size']
        price = row['Price/Pack']
        prices[size] = price
    
    # Calculate total value
    total_value = sum(quantities.get(size, 0) * prices.get(size, 0) for size in quantities.keys())
    
    # Return order summary
    return {
        "quantities": quantities,
        "prices": prices,
        "total_value": total_value
    }

def is_eligible_for_gift(order_data):
    """
    Check if the order is eligible for gifts based on the quantity rules
    
    Args:
        order_data (dict): Order summary data
        
    Returns:
        bool: True if eligible, False otherwise
    """
    # Get quantities
    quantities = order_data["quantities"]
    
    # Check eligibility: 10+ packs of 50g, 3+ packs of 250g, or 2+ packs of 1kg
    return (
        quantities.get("50g", 0) >= 10 or
        quantities.get("250g", 0) >= 3 or
        quantities.get("1kg", 0) >= 2
    )

def calculate_gift_value(gift_type, quantity, order_value=0):
    """
    Calculate the monetary value of a gift
    
    Args:
        gift_type (str): Type of gift (Pack FOC, Hookah, AF Points)
        quantity (float): Quantity of the gift
        order_value (float): Total order value (not used anymore)
        
    Returns:
        float: Monetary value of the gift
    """
    if gift_type == "Pack FOC":
        return quantity * 38
    elif gift_type == "Hookah":
        return quantity * 400
    elif gift_type == "AF Points":
        # Assume 1 AF Point is worth $1
        return quantity * 1
    return 0

def get_max_gift_quantities(budget, customer_type, order_value):
    """
    Get maximum gift quantities based on budget
    
    Args:
        budget (float): Available budget
        customer_type (CustomerType): Type of customer
        order_value (float): Total order value (not used anymore)
        
    Returns:
        dict: Maximum quantities for each gift type
    """
    max_quantities = {
        "Pack FOC": int(budget / 38),
        "AF Points": int(budget / 1)  # Assuming 1 point = $1
    }
    
    # Only Tobacco Shops can get hookahs
    if customer_type == CustomerType.TOBACCO_SHOP:
        max_quantities["Hookah"] = int(budget / 400)
    else:
        max_quantities["Hookah"] = 0
        
    return max_quantities
