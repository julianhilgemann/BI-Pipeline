
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
    # 2 years: 2024 (Leap) + 2025 = 366 + 365 = 731 days
    engine = SeasonalityEngine(start_date=date(2024, 1, 1), days=731)
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
    
    import hashlib
    
    # Track Product State (for SCD2)
    # Convert DF to list of dicts for mutable state during simulation
    product_state = products_df.to_dict('records')
    # Key by SKU for easy access
    product_map = {p['sku_id']: p for p in product_state}
    
    product_snapshots = []
    
    # Track reclassified IDs to ensure max 1 reclassification ever (to pass strict "no product > 2" validation)
    reclassified_ids = set()

    def create_snapshot_record(prod_dict, valid_from, valid_to):
        # Create SCD ID
        unique_str = f"{prod_dict['sku_id']}-{valid_from}"
        scd_id = hashlib.md5(unique_str.encode()).hexdigest()
        
        return {
            'product_id': prod_dict['sku_id'],
            'product_name': prod_dict['product_name'],
            'category': prod_dict['category'],
            'subcategory': None, # Missing in generator
            'price_tier': prod_dict['price_tier'],
            'base_retail_price': prod_dict['avg_price_eur'],
            'dbt_scd_id': scd_id,
            'dbt_updated_at': valid_from,
            'dbt_valid_from': valid_from,
            'dbt_valid_to': valid_to
        }

    # Initialize snapshot with initial state (Valid From 2024-01-01)
    for p in product_state:
        product_snapshots.append(create_snapshot_record(p, date(2024, 1, 1), None))
    
    marketing_spend = []
    monthly_budget = []
    
    for _, row in calendar_df.iterrows():
        curr_date = row['date'].date()
        mult = row['total_multiplier']
        
        # --- RECLASSIFICATION EVENTS ---
        # Oct 1 and May 1
        if (curr_date.month == 10 and curr_date.day == 1) or \
           (curr_date.month == 5 and curr_date.day == 1):
            
            print(f"  -> Triggering Reclassification Event on {curr_date}")
            
            # Filter eligible candidates (not yet reclassified)
            eligible = [p for p in product_state if p['sku_id'] not in reclassified_ids]
            
            # Select candidates (8-12%)
            num_candidates = int(len(product_state) * np.random.uniform(0.08, 0.12))
            
            if len(eligible) > num_candidates:
                candidates = np.random.choice(eligible, size=num_candidates, replace=False)
                
                for prod in candidates:
                    # Mark as reclassified
                    reclassified_ids.add(prod['sku_id'])
                    
                    # Store old state for snapshot closing
                    old_tier = prod['price_tier']
                    old_price = prod['avg_price_eur']
                    
                    # Reclassify
                    new_prod, snap_info = prod_gen.reclassify_product(prod, curr_date)
                    
                    if snap_info['direction'] is not None:
                        # Update mutable state
                        prod.update(new_prod)
                        
                        # Close previous snapshot
                        # Find the open snapshot for this product
                        for snap in reversed(product_snapshots):
                            if snap['product_id'] == prod['sku_id'] and snap['dbt_valid_to'] is None:
                                snap['dbt_valid_to'] = curr_date
                                break
                        
                        # Create new snapshot
                        product_snapshots.append(create_snapshot_record(new_prod, curr_date, None))


        for shop in shops:
            # A. Transaction Generation
            # Apply multiplier to base lambda
            lambda_val = shop['base'] * mult
            
            # Pass CURRENT product state to factory
            # We need to reconstruct a DF for the factory to use, or update the factory to accept list
            # For performance, updating the factory's DF is better
            factory.products = pd.DataFrame(product_state)
            # Re-calculate probs because popularity might change? No, popularity is static for now.
            # But we need to make sure the factory uses the updated prices.
            
            orders, lines = factory.generate_orders_for_day(
                curr_date, lambda_val, shop['id'], shop['currency']
            )
            
            all_orders.extend(orders)
            all_lines.extend(lines)
            
            # B. Marketing Spend Generation (Tier-Based)
            # Logic: Spend is determined by the tier of the products sold
            # But marketing spend is usually top-down or channel based.
            # The requirement says: "Marketing cost per order is determined by the product's current price tier"
            # This implies a per-order attribution.
            # But the output is 'raw_marketing_daily'.
            # Let's aggregate the per-order costs to get the daily total.
            
            daily_marketing_cost = 0
            
            if len(orders) > 0:
                # We need to map orders to products to get the tier
                # But orders clean don't have product info, lines do.
                # However, the requirement says "Marketing cost per ORDER".
                # What if an order has multiple products?
                # "Marketing cost per order is determined by the product's ... tier"
                # This phrasing implies 1 product per order or dominant product.
                # Let's simplify: Take the first product in the order to determine the 'main' item.
                
                order_ids = [o['order_id'] for o in orders]
                day_lines = [l for l in lines if l['order_id'] in order_ids]
                
                # Helper to find representative tier for an order
                # We'll just take the first line item's tier
                
                # Optimization: Pre-compute SKU -> Tier map for this day
                sku_tier_map = {p['sku_id']: p['price_tier'] for p in product_state}
                
                # Group lines by order to process per-order cost
                order_sku_map = {}
                for l in day_lines:
                    if l['order_id'] not in order_sku_map:
                        order_sku_map[l['order_id']] = l['sku_id']
                
                for o in orders:
                    sku = order_sku_map.get(o['order_id'])
                    tier = sku_tier_map.get(sku, 'budget') # Default
                    
                    cost = 0
                    if tier == 'budget': cost = 3.0
                    elif tier == 'mid': cost = 7.0
                    elif tier == 'premium': cost = 12.0
                    
                    daily_marketing_cost += cost
            
            # Add some noise/overhead/unattributed spend (10%)
            daily_marketing_cost *= np.random.uniform(1.0, 1.1)
            
            marketing_spend.append({
                'date': curr_date,
                'shop_id': shop['id'],
                'spend_amount': round(daily_marketing_cost, 2),
                'currency': shop['currency']
            })
    
    # Export Snapshots (Bootstrapped SCD2)
    snapshots_df = pd.DataFrame(product_snapshots)
    snapshots_df.to_csv(f'{OUTPUT_DIR}/raw_product_snapshots.csv', index=False)

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
