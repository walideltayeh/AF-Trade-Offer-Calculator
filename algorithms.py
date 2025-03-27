import numpy as np
import math
from models import CustomerType

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
    # Check eligibility
    quantities = order_data["quantities"]
    is_eligible = (
        quantities.get("50g", 0) >= 10 or
        quantities.get("250g", 0) >= 3 or
        quantities.get("1kg", 0) >= 2
    )
    
    if not is_eligible:
        return {
            "Pack FOC": 0,
            "Hookah": 0,
            "AF Points": 0
        }
    
    # Initialize gifts
    gifts = {
        "Pack FOC": 0,
        "Hookah": 0,
        "AF Points": 0
    }
    
    # Calculate total packs
    total_packs = sum(quantities.values())
    total_value = order_data["total_value"]
    
    # FLOOR_MATH formula for gift allocation
    # The logic here is to allocate budget proportionally based on order size and value
    
    # Step 1: Calculate weighted score based on pack quantities and sizes
    weight_50g = quantities.get("50g", 0) * 1
    weight_250g = quantities.get("250g", 0) * 5
    weight_1kg = quantities.get("1kg", 0) * 20
    weight_total = weight_50g + weight_250g + weight_1kg
    
    # Step 2: Allocate budget based on weights
    if weight_total > 0:
        # For Tobacco Shops, consider Hookah
        if customer_type == CustomerType.TOBACCO_SHOP and budget >= 400:
            # If budget and order size is large enough, allocate hookah
            if weight_total > 100 and budget > 800:
                hookah_count = min(2, math.floor(budget / 400))
                gifts["Hookah"] = hookah_count
                budget -= hookah_count * 400
            elif weight_total > 50:
                gifts["Hookah"] = 1
                budget -= 400
        
        # Allocate remaining budget between Pack FOC and AF Points (70/30 split)
        # Removed Cash Back allocation and redistributed to other gift types
        remaining_allocation = np.array([0.7, 0.3])  # Pack FOC, AF Points
        
        # Calculate Pack FOC based on 70% of remaining budget
        pack_foc_budget = remaining_allocation[0] * budget
        gifts["Pack FOC"] = math.floor(pack_foc_budget / 38)
        
        # Calculate AF Points based on 30% of remaining budget
        af_points_budget = remaining_allocation[1] * budget
        gifts["AF Points"] = math.floor(af_points_budget)
    
    return gifts

def calculate_budget_from_roi(order_data, target_roi_percentage):
    """
    Calculate the budget needed to achieve a target ROI
    
    Args:
        order_data (dict): Order summary data
        target_roi_percentage (float): Target ROI percentage
        
    Returns:
        float: Budget needed to achieve the target ROI
    """
    # The ROI is now a direct percentage of the total invoice value
    total_order_value = order_data["total_value"]
    
    # Budget is simply the target ROI percentage of the total order value
    budget = (target_roi_percentage / 100) * total_order_value
    
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
    # Check eligibility
    quantities = order_data["quantities"]
    is_eligible = (
        quantities.get("50g", 0) >= 10 or
        quantities.get("250g", 0) >= 3 or
        quantities.get("1kg", 0) >= 2
    )
    
    if not is_eligible:
        return {
            "Pack FOC": 0,
            "Hookah": 0,
            "AF Points": 0
        }
    
    # Calculate budget needed for target ROI
    budget = calculate_budget_from_roi(order_data, target_roi_percentage)
    
    # Start with initial recommendation
    gifts = recommend_gift(order_data, customer_type, budget)
    
    # Calculate current budget usage
    total_value = order_data["total_value"]
    current_budget_usage = (
        gifts["Pack FOC"] * 38 +
        gifts["Hookah"] * 400 +
        gifts["AF Points"] * 1
    )
    
    # Try to optimize budget usage
    remaining_budget = budget - current_budget_usage
    
    # If there's budget remaining, try to allocate it
    if remaining_budget > 38:  # If we can afford at least one more Pack FOC
        additional_packs = math.floor(remaining_budget / 38)
        gifts["Pack FOC"] += additional_packs
        remaining_budget -= additional_packs * 38
    
    # If still budget remaining, allocate to AF Points
    if remaining_budget > 1:
        additional_points = math.floor(remaining_budget)
        gifts["AF Points"] += additional_points
    
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
    total_value = order_data["total_value"]
    
    # If no budget or order value, ROI is 0
    if budget == 0 or total_value == 0:
        return 0
    
    # Calculate the actual cost of all the gifts
    # Removed Cash Back from calculation
    actual_cost = (
        gifts.get("Pack FOC", 0) * 38 +
        gifts.get("Hookah", 0) * 400 +
        gifts.get("AF Points", 0) * 1
    )
    
    # ROI is simply the percentage of the total order value that is being given as gifts
    roi = (actual_cost / total_value) * 100
    
    return round(roi, 2)
