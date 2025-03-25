from enum import Enum

class CustomerType(Enum):
    """
    Enumeration for different customer types
    """
    RETAILER = 1
    TOBACCO_SHOP = 2

class Gift:
    """
    Class representing a gift
    """
    def __init__(self, name, value):
        self.name = name
        self.value = value  # Value in dollars

class Offer:
    """
    Class representing an offer tier (Silver, Gold, Diamond, Platinum)
    """
    def __init__(self, name, roi_percentage):
        self.name = name
        self.roi_percentage = roi_percentage  # Target ROI percentage
        self.gifts = {}  # Dictionary mapping gift types to quantities
        self.budget = 0.0  # Will be calculated based on order value and ROI
        self.actual_roi = 0.0  # Actual ROI percentage achieved
