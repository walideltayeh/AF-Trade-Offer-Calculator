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
        """
        Initialize a gift with a name and value
        
        Args:
            name (str): Name of the gift
            value (float): Value of the gift
        """
        self.name = name
        self.value = value

class Offer:
    """
    Class representing an offer tier (Silver, Gold, Diamond, Platinum)
    """
    def __init__(self, name, roi_percentage):
        """
        Initialize an offer tier with a name and ROI percentage
        
        Args:
            name (str): Name of the tier
            roi_percentage (float): ROI percentage for the tier
        """
        self.name = name
        self.roi_percentage = roi_percentage
