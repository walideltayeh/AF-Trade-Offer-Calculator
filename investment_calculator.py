import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from models import CustomerType

def calculate_investment(
    total_master_cases,
    mc_50g_percent,
    mc_250g_percent,
    mc_1kg_percent,
    silver_percent,
    gold_percent,
    diamond_percent,
    platinum_percent,
    retail_percent,
    tobacco_shop_percent
):
    """
    Calculate investment requirements for gift programs
    
    Args:
        total_master_cases (float): Total number of master cases
        mc_50g_percent (float): Percentage of 50g master cases
        mc_250g_percent (float): Percentage of 250g master cases
        mc_1kg_percent (float): Percentage of 1kg master cases
        silver_percent (float): Percentage of silver tier orders
        gold_percent (float): Percentage of gold tier orders
        diamond_percent (float): Percentage of diamond tier orders
        platinum_percent (float): Percentage of platinum tier orders
        retail_percent (float): Percentage of retail customers
        tobacco_shop_percent (float): Percentage of tobacco shop customers
        
    Returns:
        dict: Dictionary containing investment calculation results
    """
    # Validate percentage inputs sum to 100%
    if abs(mc_50g_percent + mc_250g_percent + mc_1kg_percent - 100) > 0.001:
        return {"error": "Size percentages must sum to 100%"}
    if abs(silver_percent + gold_percent + diamond_percent + platinum_percent - 100) > 0.001:
        return {"error": "Tier percentages must sum to 100%"}
    if abs(retail_percent + tobacco_shop_percent - 100) > 0.001:
        return {"error": "Customer type percentages must sum to 100%"}
    
    # Calculate master cases by size
    mc_50g = (total_master_cases * mc_50g_percent) / 100
    mc_250g = (total_master_cases * mc_250g_percent) / 100
    mc_1kg = (total_master_cases * mc_1kg_percent) / 100
    
    # Calculate packs by size (master case quantities)
    packs_50g = mc_50g * 10 * 12  # Each 50g Master Case has 10 cartons of 12 packs
    packs_250g = mc_250g * 10 * 6  # Each 250g Master Case has 10 cartons of 6 packs
    packs_1kg = mc_1kg * 10 * 2  # Each 1kg Master Case has 10 cartons of 2 packs
    
    # Calculate total order value by size and pack price
    price_50g = 32.80
    price_250g = 176.81
    price_1kg = 638.83
    
    value_50g = packs_50g * price_50g
    value_250g = packs_250g * price_250g
    value_1kg = packs_1kg * price_1kg
    
    total_value = value_50g + value_250g + value_1kg
    
    # Calculate order values by tier
    silver_value = (total_value * silver_percent) / 100
    gold_value = (total_value * gold_percent) / 100
    diamond_value = (total_value * diamond_percent) / 100
    platinum_value = (total_value * platinum_percent) / 100
    
    # Calculate budget by tier using ROI percentages
    silver_roi = 5.0 / 100
    gold_roi = 7.0 / 100
    diamond_roi = 9.0 / 100
    platinum_roi = 13.0 / 100
    
    silver_budget = silver_value * silver_roi
    gold_budget = gold_value * gold_roi
    diamond_budget = diamond_value * diamond_roi
    platinum_budget = platinum_value * platinum_roi
    
    total_budget = silver_budget + gold_budget + diamond_budget + platinum_budget
    
    # Calculate customer split
    retail_value = (total_value * retail_percent) / 100
    tobacco_shop_value = (total_value * tobacco_shop_percent) / 100
    
    # Return calculation results
    return {
        "mc_50g": mc_50g,
        "mc_250g": mc_250g,
        "mc_1kg": mc_1kg,
        "packs_50g": packs_50g,
        "packs_250g": packs_250g,
        "packs_1kg": packs_1kg,
        "value_50g": value_50g,
        "value_250g": value_250g,
        "value_1kg": value_1kg,
        "total_value": total_value,
        "silver_value": silver_value,
        "gold_value": gold_value,
        "diamond_value": diamond_value,
        "platinum_value": platinum_value,
        "silver_budget": silver_budget,
        "gold_budget": gold_budget,
        "diamond_budget": diamond_budget,
        "platinum_budget": platinum_budget,
        "total_budget": total_budget,
        "retail_value": retail_value,
        "tobacco_shop_value": tobacco_shop_value
    }

def main():
    st.title("Investment Calculator")
    
    st.markdown("""
    This calculator helps you forecast the investment required for your gift program.
    Enter your projected sales and distribution to see the estimated budget requirements.
    """)
    
    with st.container():
        st.header("Sales Projection")
        
        # Master case input
        total_master_cases = st.number_input("Total Master Cases", min_value=1.0, value=100.0, step=1.0)
        
        # Size distribution
        st.subheader("Size Distribution (%)")
        size_col1, size_col2, size_col3 = st.columns(3)
        
        with size_col1:
            mc_50g_percent = st.number_input("50g Master Cases", min_value=0.0, max_value=100.0, value=70.0, step=1.0)
        
        with size_col2:
            mc_250g_percent = st.number_input("250g Master Cases", min_value=0.0, max_value=100.0, value=20.0, step=1.0)
        
        with size_col3:
            mc_1kg_percent = st.number_input("1kg Master Cases", min_value=0.0, max_value=100.0, value=10.0, step=1.0)
        
        # Display size distribution sum
        size_sum = mc_50g_percent + mc_250g_percent + mc_1kg_percent
        if abs(size_sum - 100) > 0.001:
            st.warning(f"Size distribution total: {size_sum}% (should equal 100%)")
        else:
            st.success(f"Size distribution total: {size_sum}%")
    
    with st.container():
        st.header("Tier Distribution")
        
        # Tier distribution
        st.subheader("Tier Distribution (%)")
        tier_col1, tier_col2, tier_col3, tier_col4 = st.columns(4)
        
        with tier_col1:
            silver_percent = st.number_input("Silver", min_value=0.0, max_value=100.0, value=40.0, step=1.0)
        
        with tier_col2:
            gold_percent = st.number_input("Gold", min_value=0.0, max_value=100.0, value=30.0, step=1.0)
        
        with tier_col3:
            diamond_percent = st.number_input("Diamond", min_value=0.0, max_value=100.0, value=20.0, step=1.0)
        
        with tier_col4:
            platinum_percent = st.number_input("Platinum", min_value=0.0, max_value=100.0, value=10.0, step=1.0)
        
        # Display tier distribution sum
        tier_sum = silver_percent + gold_percent + diamond_percent + platinum_percent
        if abs(tier_sum - 100) > 0.001:
            st.warning(f"Tier distribution total: {tier_sum}% (should equal 100%)")
        else:
            st.success(f"Tier distribution total: {tier_sum}%")
    
    with st.container():
        st.header("Customer Distribution")
        
        # Customer type distribution
        st.subheader("Customer Type Distribution (%)")
        customer_col1, customer_col2 = st.columns(2)
        
        with customer_col1:
            retail_percent = st.number_input("Retailers", min_value=0.0, max_value=100.0, value=60.0, step=1.0)
        
        with customer_col2:
            tobacco_shop_percent = st.number_input("Tobacco Shops", min_value=0.0, max_value=100.0, value=40.0, step=1.0)
        
        # Display customer distribution sum
        customer_sum = retail_percent + tobacco_shop_percent
        if abs(customer_sum - 100) > 0.001:
            st.warning(f"Customer distribution total: {customer_sum}% (should equal 100%)")
        else:
            st.success(f"Customer distribution total: {customer_sum}%")
    
    # Calculate button
    if st.button("Calculate Investment"):
        # Validate inputs
        valid_inputs = True
        if abs(size_sum - 100) > 0.001:
            st.error("Size distribution must equal 100%")
            valid_inputs = False
        if abs(tier_sum - 100) > 0.001:
            st.error("Tier distribution must equal 100%")
            valid_inputs = False
        if abs(customer_sum - 100) > 0.001:
            st.error("Customer distribution must equal 100%")
            valid_inputs = False
        
        if valid_inputs:
            # Perform calculation
            results = calculate_investment(
                total_master_cases,
                mc_50g_percent,
                mc_250g_percent,
                mc_1kg_percent,
                silver_percent,
                gold_percent,
                diamond_percent,
                platinum_percent,
                retail_percent,
                tobacco_shop_percent
            )
            
            if "error" in results:
                st.error(results["error"])
            else:
                # Display results
                st.header("Investment Results")
                
                # Order value breakdown
                st.subheader("Order Value Breakdown")
                value_cols = st.columns(4)
                with value_cols[0]:
                    st.metric("Total Order Value", f"${results['total_value']:,.2f}")
                with value_cols[1]:
                    st.metric("50g Value", f"${results['value_50g']:,.2f}")
                with value_cols[2]:
                    st.metric("250g Value", f"${results['value_250g']:,.2f}")
                with value_cols[3]:
                    st.metric("1kg Value", f"${results['value_1kg']:,.2f}")
                
                # Pack quantity breakdown
                st.subheader("Pack Quantity Breakdown")
                pack_cols = st.columns(3)
                with pack_cols[0]:
                    st.metric("50g Packs", f"{int(results['packs_50g']):,}")
                with pack_cols[1]:
                    st.metric("250g Packs", f"{int(results['packs_250g']):,}")
                with pack_cols[2]:
                    st.metric("1kg Packs", f"{int(results['packs_1kg']):,}")
                
                # Budget breakdown
                st.subheader("Gift Budget Breakdown")
                budget_cols = st.columns(5)
                with budget_cols[0]:
                    st.metric("Total Budget", f"${results['total_budget']:,.2f}")
                with budget_cols[1]:
                    st.metric("Silver Budget", f"${results['silver_budget']:,.2f}")
                with budget_cols[2]:
                    st.metric("Gold Budget", f"${results['gold_budget']:,.2f}")
                with budget_cols[3]:
                    st.metric("Diamond Budget", f"${results['diamond_budget']:,.2f}")
                with budget_cols[4]:
                    st.metric("Platinum Budget", f"${results['platinum_budget']:,.2f}")
                
                # Calculate ROI percentages
                silver_roi = 5.0
                gold_roi = 7.0
                diamond_roi = 9.0
                platinum_roi = 13.0
                
                # Budget allocation pie chart
                st.subheader("Budget Allocation by Tier")
                tier_labels = ["Silver", "Gold", "Diamond", "Platinum"]
                tier_values = [
                    results['silver_budget'],
                    results['gold_budget'],
                    results['diamond_budget'],
                    results['platinum_budget']
                ]
                tier_colors = ["#C0C0C0", "#FFD700", "#B9F2FF", "#E5E4E2"]
                tier_roi_values = [silver_roi, gold_roi, diamond_roi, platinum_roi]
                
                fig1 = go.Figure(data=[go.Pie(
                    labels=tier_labels,
                    values=tier_values,
                    hole=0.4,
                    marker_colors=tier_colors
                )])
                fig1.update_layout(
                    title_text="Budget Distribution by Tier",
                    annotations=[dict(text=f"${results['total_budget']:,.0f}", x=0.5, y=0.5, font_size=16, showarrow=False)]
                )
                st.plotly_chart(fig1, use_container_width=True)
                
                # Budget breakdown table
                budget_data = pd.DataFrame({
                    "Tier": tier_labels,
                    "Value": [results['silver_value'], results['gold_value'], results['diamond_value'], results['platinum_value']],
                    "ROI %": tier_roi_values,
                    "Budget": tier_values
                })
                budget_data["Value"] = budget_data["Value"].map("${:,.2f}".format)
                budget_data["Budget"] = budget_data["Budget"].map("${:,.2f}".format)
                budget_data["ROI %"] = budget_data["ROI %"].map("{}%".format)
                
                st.subheader("Budget Calculation Details")
                st.table(budget_data)
                
                # Customer type breakdown
                st.subheader("Customer Type Breakdown")
                customer_cols = st.columns(2)
                with customer_cols[0]:
                    st.metric("Retailer Value", f"${results['retail_value']:,.2f}")
                with customer_cols[1]:
                    st.metric("Tobacco Shop Value", f"${results['tobacco_shop_value']:,.2f}")
                
                # Order size breakdown
                size_labels = ["50g", "250g", "1kg"]
                size_values = [results['value_50g'], results['value_250g'], results['value_1kg']]
                
                fig2 = go.Figure(data=[go.Pie(
                    labels=size_labels,
                    values=size_values,
                    hole=0.4
                )])
                fig2.update_layout(
                    title_text="Order Value by Product Size",
                    annotations=[dict(text=f"${results['total_value']:,.0f}", x=0.5, y=0.5, font_size=16, showarrow=False)]
                )
                st.plotly_chart(fig2, use_container_width=True)
                
                # Overall program metrics
                st.subheader("Overall Program Metrics")
                metrics_cols = st.columns(3)
                with metrics_cols[0]:
                    budget_percentage = (results['total_budget'] / results['total_value']) * 100
                    st.metric("Overall Budget %", f"{budget_percentage:.2f}%")
                with metrics_cols[1]:
                    packs_total = results['packs_50g'] + results['packs_250g'] + results['packs_1kg']
                    st.metric("Total Packs", f"{int(packs_total):,}")
                with metrics_cols[2]:
                    budget_per_pack = results['total_budget'] / packs_total
                    st.metric("Budget per Pack", f"${budget_per_pack:.2f}")
                
                # Gift type allocation estimates                
                st.subheader("Estimated Gift Quantities")
                
                # Estimate Pack FOC and Hookah quantities
                pack_foc_price = 38.0
                hookah_price = 400.0
                
                # Assuming average distribution based on customer types
                tobacco_budget = results['total_budget'] * (tobacco_shop_percent / 100)
                retail_budget = results['total_budget'] * (retail_percent / 100)
                
                # Estimate for tobacco shops
                tobacco_hookah_budget = min(tobacco_budget * 0.2, (tobacco_budget / hookah_price) * hookah_price)
                tobacco_pack_foc_budget = tobacco_budget - tobacco_hookah_budget
                
                # Estimate for retailers (only Pack FOC)
                retail_pack_foc_budget = retail_budget
                
                # Calculate estimated quantities
                est_hookahs = int(tobacco_hookah_budget / hookah_price)
                est_pack_foc = int((tobacco_pack_foc_budget + retail_pack_foc_budget) / pack_foc_price)
                
                gift_cols = st.columns(2)
                with gift_cols[0]:
                    st.metric("Estimated Pack FOC", f"{est_pack_foc:,}")
                with gift_cols[1]:
                    st.metric("Estimated Hookahs", f"{est_hookahs:,}")

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
