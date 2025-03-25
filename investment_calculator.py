import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from models import CustomerType, Offer
from algorithms import calculate_budget_from_roi

# Define constants that could be turned into variables
PRICE_50G_MC = 3936  # Price for 1 Master Case of 50g (120 packs)
PRICE_250G_MC = 4243.5  # Price for 1 Master Case of 250g (24 packs)
PRICE_1KG_MC = 3833  # Price for 1 Master Case of 1kg (6 packs)

PACKS_50G_MC = 120  # Packs per Master Case of 50g
PACKS_250G_MC = 24  # Packs per Master Case of 250g
PACKS_1KG_MC = 6    # Packs per Master Case of 1kg

# Function to calculate order value and gifts based on master cases
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
    # Calculate number of master cases by type
    mc_50g = total_master_cases * (mc_50g_percent / 100)
    mc_250g = total_master_cases * (mc_250g_percent / 100)
    mc_1kg = total_master_cases * (mc_1kg_percent / 100)
    
    # Calculate total value by product type
    value_50g = mc_50g * PRICE_50G_MC
    value_250g = mc_250g * PRICE_250G_MC
    value_1kg = mc_1kg * PRICE_1KG_MC
    total_value = value_50g + value_250g + value_1kg
    
    # Calculate total weight in grams
    weight_50g = mc_50g * PACKS_50G_MC * 50
    weight_250g = mc_250g * PACKS_250G_MC * 250
    weight_1kg = mc_1kg * PACKS_1KG_MC * 1000
    total_weight = weight_50g + weight_250g + weight_1kg
    
    # Create customer segments
    retail_value = total_value * (retail_percent / 100)
    tobacco_shop_value = total_value * (tobacco_shop_percent / 100)
    
    # Create tier segments
    silver_value = total_value * (silver_percent / 100)
    gold_value = total_value * (gold_percent / 100)
    diamond_value = total_value * (diamond_percent / 100)
    platinum_value = total_value * (platinum_percent / 100)
    
    # Define tier ROI percentages
    silver_roi = 5
    gold_roi = 7
    diamond_roi = 9
    platinum_roi = 13
    
    # Calculate gift budgets by tier
    silver_budget = silver_value * (silver_roi / 100)
    gold_budget = gold_value * (gold_roi / 100)
    diamond_budget = diamond_value * (diamond_roi / 100)
    platinum_budget = platinum_value * (platinum_roi / 100)
    total_budget = silver_budget + gold_budget + diamond_budget + platinum_budget
    
    # Calculate gift budgets by customer type
    retail_budget = (
        (silver_value * (retail_percent / 100) * (silver_roi / 100)) +
        (gold_value * (retail_percent / 100) * (gold_roi / 100)) +
        (diamond_value * (retail_percent / 100) * (diamond_roi / 100)) +
        (platinum_value * (retail_percent / 100) * (platinum_roi / 100))
    )
    
    tobacco_shop_budget = (
        (silver_value * (tobacco_shop_percent / 100) * (silver_roi / 100)) +
        (gold_value * (tobacco_shop_percent / 100) * (gold_roi / 100)) +
        (diamond_value * (tobacco_shop_percent / 100) * (diamond_roi / 100)) +
        (platinum_value * (tobacco_shop_percent / 100) * (platinum_roi / 100))
    )
    
    # Net revenue after gifts
    net_revenue = total_value - total_budget
    
    # Return comprehensive results
    return {
        "master_cases": {
            "50g": mc_50g,
            "250g": mc_250g,
            "1kg": mc_1kg,
            "total": total_master_cases
        },
        "value": {
            "50g": value_50g,
            "250g": value_250g,
            "1kg": value_1kg,
            "total": total_value
        },
        "weight_grams": {
            "50g": weight_50g,
            "250g": weight_250g,
            "1kg": weight_1kg,
            "total": total_weight
        },
        "customer_segments": {
            "retail": retail_value,
            "tobacco_shop": tobacco_shop_value
        },
        "tier_segments": {
            "silver": silver_value,
            "gold": gold_value,
            "diamond": diamond_value,
            "platinum": platinum_value
        },
        "gift_budgets": {
            "silver": silver_budget,
            "gold": gold_budget,
            "diamond": diamond_budget,
            "platinum": platinum_budget,
            "total": total_budget,
            "retail": retail_budget,
            "tobacco_shop": tobacco_shop_budget
        },
        "net_revenue": net_revenue,
        "roi_summary": {
            "silver": silver_roi,
            "gold": gold_roi,
            "diamond": diamond_roi,
            "platinum": platinum_roi,
            "weighted_average": (
                (silver_roi * silver_percent) +
                (gold_roi * gold_percent) +
                (diamond_roi * diamond_percent) +
                (platinum_roi * platinum_percent)
            ) / 100
        }
    }

def main():
    # Create two columns for the sidebar
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Product Mix")
        
        total_mc = st.number_input(
            "Total Master Cases", 
            min_value=1, 
            value=1000,
            help="Total number of master cases across all product sizes"
        )
        
        # Create expandable section for product mix
        with st.expander("Product Mix Percentages (must sum to 100%)", expanded=True):
            mc_50g_percent = st.slider("50g Master Cases %", 0, 100, 85)
            mc_250g_percent = st.slider("250g Master Cases %", 0, 100, 10)
            mc_1kg_percent = st.slider("1kg Master Cases %", 0, 100, 5)
            
            # Validate that percentages sum to 100%
            product_sum = mc_50g_percent + mc_250g_percent + mc_1kg_percent
            if product_sum != 100:
                st.warning(f"Product mix percentages sum to {product_sum}%, not 100%. Please adjust.")
    
    with col2:
        st.subheader("Customer Distribution")
        
        # Create expandable section for customer distribution
        with st.expander("Customer Type Percentages (must sum to 100%)", expanded=True):
            retail_percent = st.slider("Retail Customers %", 0, 100, 50)
            tobacco_shop_percent = st.slider("Tobacco Shop Customers %", 0, 100, 50)
            
            # Validate that percentages sum to 100%
            customer_sum = retail_percent + tobacco_shop_percent
            if customer_sum != 100:
                st.warning(f"Customer type percentages sum to {customer_sum}%, not 100%. Please adjust.")
        
        # Create expandable section for tier distribution
        with st.expander("Tier Distribution Percentages (must sum to 100%)", expanded=True):
            silver_percent = st.slider("Silver Tier %", 0, 100, 80)
            gold_percent = st.slider("Gold Tier %", 0, 100, 10)
            diamond_percent = st.slider("Diamond Tier %", 0, 100, 7)
            platinum_percent = st.slider("Platinum Tier %", 0, 100, 3)
            
            # Validate that percentages sum to 100%
            tier_sum = silver_percent + gold_percent + diamond_percent + platinum_percent
            if tier_sum != 100:
                st.warning(f"Tier percentages sum to {tier_sum}%, not 100%. Please adjust.")
    
    # Calculate investment based on inputs
    if (product_sum == 100 and customer_sum == 100 and tier_sum == 100):
        results = calculate_investment(
            total_mc,
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
        
        # Display results
        st.header("Investment Analysis")
        
        # Overall metrics
        metric_cols = st.columns(3)
        with metric_cols[0]:
            st.metric("Total Order Value", f"${results['value']['total']:,.2f}")
        with metric_cols[1]:
            st.metric("Total Gift Budget", f"${results['gift_budgets']['total']:,.2f}")
        with metric_cols[2]:
            st.metric("Net Revenue", f"${results['net_revenue']:,.2f}")
            
        # ROI information
        st.subheader("ROI Analysis")
        st.info(f"Weighted Average ROI: {results['roi_summary']['weighted_average']:.2f}%")
        
        roi_data = {
            'Tier': ['Silver', 'Gold', 'Diamond', 'Platinum'],
            'ROI (%)': [
                results['roi_summary']['silver'],
                results['roi_summary']['gold'],
                results['roi_summary']['diamond'],
                results['roi_summary']['platinum']
            ],
            'Distribution (%)': [
                silver_percent, 
                gold_percent, 
                diamond_percent, 
                platinum_percent
            ],
            'Order Value ($)': [
                results['tier_segments']['silver'],
                results['tier_segments']['gold'],
                results['tier_segments']['diamond'],
                results['tier_segments']['platinum']
            ],
            'Gift Budget ($)': [
                results['gift_budgets']['silver'],
                results['gift_budgets']['gold'],
                results['gift_budgets']['diamond'],
                results['gift_budgets']['platinum']
            ],
        }
        
        roi_df = pd.DataFrame(roi_data)
        st.dataframe(roi_df.style.format({
            'ROI (%)': '{:.1f}',
            'Distribution (%)': '{:.1f}',
            'Order Value ($)': '${:,.2f}',
            'Gift Budget ($)': '${:,.2f}'
        }))
        
        # Create visualizations
        st.subheader("Visualizations")
        viz_tabs = st.tabs(["Order Value", "Gift Budget", "Customer Analysis"])
        
        with viz_tabs[0]:
            # Order value by product
            product_value_data = {
                'Product': ['50g', '250g', '1kg'],
                'Value': [
                    results['value']['50g'],
                    results['value']['250g'],
                    results['value']['1kg']
                ]
            }
            product_value_df = pd.DataFrame(product_value_data)
            
            # Stacked bar chart for order value by tier and product
            order_fig = px.bar(
                product_value_df,
                x='Product',
                y='Value',
                title='Order Value by Product Size',
                color='Product',
                height=400
            )
            order_fig.update_layout(yaxis_title="Order Value ($)")
            st.plotly_chart(order_fig, use_container_width=True)
            
        with viz_tabs[1]:
            # Gift budget visualizations
            budget_data = {
                'Category': ['Silver', 'Gold', 'Diamond', 'Platinum'],
                'Budget': [
                    results['gift_budgets']['silver'],
                    results['gift_budgets']['gold'],
                    results['gift_budgets']['diamond'],
                    results['gift_budgets']['platinum']
                ]
            }
            budget_df = pd.DataFrame(budget_data)
            
            # Pie chart for gift budget distribution
            budget_fig = px.pie(
                budget_df,
                values='Budget',
                names='Category',
                title='Gift Budget Distribution by Tier',
                hole=0.4
            )
            budget_fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(budget_fig, use_container_width=True)
            
        with viz_tabs[2]:
            # Customer type analysis
            customer_value_data = {
                'Customer Type': ['Retail', 'Tobacco Shop'],
                'Order Value': [
                    results['customer_segments']['retail'],
                    results['customer_segments']['tobacco_shop']
                ],
                'Gift Budget': [
                    results['gift_budgets']['retail'],
                    results['gift_budgets']['tobacco_shop']
                ]
            }
            customer_df = pd.DataFrame(customer_value_data)
            
            # Bar chart comparing order values and gift budgets by customer type
            customer_fig = px.bar(
                customer_df,
                x='Customer Type',
                y=['Order Value', 'Gift Budget'],
                title='Order Value and Gift Budget by Customer Type',
                barmode='group',
                height=400
            )
            customer_fig.update_layout(yaxis_title="Amount ($)")
            st.plotly_chart(customer_fig, use_container_width=True)
            
            # Calculate and display percentages
            retail_roi_percent = (results['gift_budgets']['retail'] / results['customer_segments']['retail']) * 100 if results['customer_segments']['retail'] > 0 else 0
            tobacco_roi_percent = (results['gift_budgets']['tobacco_shop'] / results['customer_segments']['tobacco_shop']) * 100 if results['customer_segments']['tobacco_shop'] > 0 else 0
            
            roi_cols = st.columns(2)
            with roi_cols[0]:
                st.metric("Retail ROI", f"{retail_roi_percent:.2f}%")
            with roi_cols[1]:
                st.metric("Tobacco Shop ROI", f"{tobacco_roi_percent:.2f}%")

if __name__ == "__main__":
    main()
