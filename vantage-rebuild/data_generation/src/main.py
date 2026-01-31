
import pandas as pd
import numpy as np
from datetime import date
import os
from seasonality import SeasonalityEngine
from generators import ProductGenerator, CustomerGenerator, OrderFactory

OUTPUT_DIR = '../output'

def main():
    print("Starting Data Generation...")
    np.random.seed(42) # Ensure reproducibility

    # 1. Setup Data Objects
    print("Generating Products & Customers...")
    prod_gen = ProductGenerator(num_products=500)
    products_df = prod_gen.generate()
    
    cust_gen = CustomerGenerator(num_customers=5000)
    customers_df = cust_gen.generate()
    
    # Export static data
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    products_df.to_csv(f'{OUTPUT_DIR}/raw_products.csv', index=False)
    # We assume customer data isn't needed for the dashboard (GDPR simplification), but we use it for logic
    
    # 2. Setup Seasonality
    print("Calculating Seasonality...")
    engine = SeasonalityEngine(start_date=date(2024, 1, 1), days=365)
    calendar_df = engine.get_daily_multipliers()
    
    # 3. Generate Orders Loop
    print("Generating Orders (This may take a moment)...")
    factory = OrderFactory(products_df, customers_df)
    
    all_orders = []
    all_lines = []
    
    # Define Shops and their Base Volumes (Lambda)
    # DE: High Vol, EUR
    # AT: Med Vol, EUR
    # CH: Low Vol, CHF
    shops = [
        {'id': 'DE', 'base': 50, 'currency': 'EUR'},
        {'id': 'AT', 'base': 15, 'currency': 'EUR'},
        {'id': 'CH', 'base': 10, 'currency': 'CHF'}
    ]
    
    marketing_spend = []
    monthly_budget = []
    
    for _, row in calendar_df.iterrows():
        curr_date = row['date'].date()
        mult = row['total_multiplier']
        
        for shop in shops:
            # A. Transaction Generation
            # Apply multiplier to base lambda
            lambda_val = shop['base'] * mult
            orders, lines = factory.generate_orders_for_day(
                curr_date, lambda_val, shop['id'], shop['currency']
            )
            
            all_orders.extend(orders)
            all_lines.extend(lines)
            
            # B. Marketing Spend Generation (Daily Aggregated)
            # Logic: Spend is roughly 15% of *expected* revenue (based on lambda + avg price)
            # Avg Price ~100 EUR. 
            est_rev = lambda_val * 100
            # Add noise to spend (Marketing isn't perfect)
            spend_noise = np.random.normal(1.0, 0.1) # +/- 10%
            daily_spend = est_rev * 0.15 * spend_noise
            
            marketing_spend.append({
                'date': curr_date,
                'shop_id': shop['id'],
                'spend_amount': round(daily_spend, 2),
                'currency': shop['currency']
            })

    # Convert to DF
    orders_df = pd.DataFrame(all_orders)
    lines_df = pd.DataFrame(all_lines)
    marketing_df = pd.DataFrame(marketing_spend)
    
    # Export
    print(f"Exporting {len(orders_df)} orders and {len(lines_df)} line items...")
    orders_df.to_csv(f'{OUTPUT_DIR}/raw_orders.csv', index=False)
    lines_df.to_csv(f'{OUTPUT_DIR}/raw_line_items.csv', index=False)
    marketing_df.to_csv(f'{OUTPUT_DIR}/raw_marketing_daily.csv', index=False)
    
    # 4. Generate Budget (Monthly)
    # We aggregate the actuals we just created, smooth them, and save as budget
    print("Generating Budget...")
    # Add month col to marketing_df (just for easy grouping proxy - ideally use orders, but let's assume budget follows marketing plan)
    # Better: Aggregate orders_df + lines_df to get actual revenue per month
    
    # Join orders and lines for calculation
    full_df = orders_df.merge(lines_df, on='order_id')
    # Calculate revenue
    full_df['revenue'] = full_df['unit_price_paid'] * full_df['qty']
    # Filter returns for net revenue budget? Usually budget is Gross or Net. Let's do Gross for simplicity.
    full_df['month'] = pd.to_datetime(full_df['order_date']).dt.to_period('M')
    
    budget_agg = full_df.groupby(['shop_id', 'month', 'currency_code'])['revenue'].sum().reset_index()
    
    budget_rows = []
    for _, row in budget_agg.iterrows():
        # Scramble: Budget is rarely accurate. 
        # Add random variance +/- 5%
        noise = np.random.uniform(0.95, 1.05)
        budget_rev = row['revenue'] * noise
        
        budget_rows.append({
            'month': row['month'].start_time.date(),
            'shop_id': row['shop_id'],
            'currency': row['currency_code'],
            'budget_revenue': round(budget_rev, 2)
        })
        
    budget_df = pd.DataFrame(budget_rows)
    budget_df.to_csv(f'{OUTPUT_DIR}/raw_budget.csv', index=False)

    print("Data Generation Complete.")

if __name__ == "__main__":
    main()
