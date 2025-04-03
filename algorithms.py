import math
from models import CustomerType
from utils import calculate_gift_value, get_max_gift_quantities

def recommend_gift(order_data, customer_type, budget):
    """
    Recommend gifts based on order data, customer type, and budget
    
    Args:
        order_data (dict): Order summary data
        customer_type (CustomerType): Type of customer
        budget (float): Available budget
        
    Returns:
        dict: Recommended gift quantities
    """
    # Initialize gift quantities
    gift_quantities = {"Pack FOC": 0, "Hookah": 0}
    
    # Get maximum gift quantities based on budget
    max_quantities = get_max_gift_quantities(budget, customer_type, order_data['total_value'])
    
    # Calculate total order weight
    total_order_weight_g = sum([
        order_data["quantities"].get("50g", 0) * 50,
        order_data["quantities"].get("250g", 0) * 250,
        order_data["quantities"].get("1kg", 0) * 1000
    ])
    
    # Convert to kg for easier comparison
    total_order_weight_kg = total_order_weight_g / 1000
    
    # For Tobacco Shops, allocate hookahs first if applicable
    remaining_budget = budget
    
    if customer_type == CustomerType.TOBACCO_SHOP:
        # Allocate hookahs based on order weight and budget
        if total_order_weight_kg > 100 and remaining_budget >= 800:
            # Up to 2 hookahs for orders over 100kg
            gift_quantities["Hookah"] = min(2, max_quantities["Hookah"])
            remaining_budget -= gift_quantities["Hookah"] * 400
        elif total_order_weight_kg > 50 and remaining_budget >= 400:
            # 1 hookah for orders over 50kg
            gift_quantities["Hookah"] = 1
            remaining_budget -= 400
    
    # Allocate remaining budget to Pack FOC
    if remaining_budget > 0:
        pack_foc_quantity = min(math.floor(remaining_budget / 38), max_quantities["Pack FOC"])
        gift_quantities["Pack FOC"] = pack_foc_quantity
    
    return gift_quantities

def calculate_budget_from_roi(order_data, target_roi_percentage):
    """
    Calculate the budget needed to achieve a target ROI
    
    Args:
        order_data (dict): Order summary data
        target_roi_percentage (float): Target ROI percentage
        
    Returns:
        float: Budget needed to achieve the target ROI
    """
    # Calculate budget as a percentage of total order value
    budget = order_data["total_value"] * (target_roi_percentage / 100)
    
    # Round to 2 decimal places
    budget = round(budget, 2)
    
    return budget

def optimize_budget(order_data, customer_type, target_roi_percentage):
    """
    Optimize gift allocation to achieve a target ROI
    
    Args:
        order_data (dict): Order summary data
        customer_type (CustomerType): Type of customer
        target_roi_percentage (float): Target ROI percentage
        
    Returns:
        dict: Optimized gift quantities
    """
    # Calculate budget based on target ROI
    budget = calculate_budget_from_roi(order_data, target_roi_percentage)
    
    # Recommend gifts based on the calculated budget
    gifts = recommend_gift(order_data, customer_type, budget)
    
    # Calculate actual ROI with recommended gifts
    actual_roi = calculate_roi(order_data, gifts, budget)
    
    # Fine-tune the allocation by adjusting pack gifts
    # Add or remove individual Pack FOC as needed
    while abs(actual_roi - target_roi_percentage) > 0.1:
        if actual_roi > target_roi_percentage:
            # ROI is too high, reduce Pack FOC if possible
            if gifts["Pack FOC"] > 0:
                gifts["Pack FOC"] -= 1
            else:
                # Can't reduce Pack FOC further, try to reduce Hookah
                if gifts["Hookah"] > 0:
                    gifts["Hookah"] -= 1
                else:
                    # Can't reduce further
                    break
        else:
            # ROI is too low, increase Pack FOC if budget allows
            max_quantities = get_max_gift_quantities(budget, customer_type, order_data['total_value'])
            if gifts["Pack FOC"] < max_quantities["Pack FOC"]:
                gifts["Pack FOC"] += 1
            else:
                # Can't increase further
                break
        
        # Recalculate actual ROI
        actual_roi = calculate_roi(order_data, gifts, budget)
    
    return gifts

def calculate_roi(order_data, gifts, budget):
    """
    Calculate ROI (Return on Investment) for the gifts
    
    Args:
        order_data (dict): Order summary data
        gifts (dict): Gift allocation
        budget (float): Budget allocated
        
    Returns:
        float: ROI percentage
    """
    # Calculate total gift value
    gift_value = (
        calculate_gift_value("Pack FOC", gifts.get("Pack FOC", 0)) +
        calculate_gift_value("Hookah", gifts.get("Hookah", 0))
    )
    
    # Calculate ROI as a percentage
    if order_data["total_value"] > 0:
        roi_percentage = (gift_value / order_data["total_value"]) * 100
    else:
        roi_percentage = 0
    
    return round(roi_percentage, 2)
