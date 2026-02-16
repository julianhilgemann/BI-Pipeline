
import numpy as np
import pandas as pd
from faker import Faker
import uuid

# Initialize Faker
fake = Faker(['de_DE'])

class ProductGenerator:
    def __init__(self, num_products=500):
        self.num_products = num_products
        
    def generate(self):
        """
        Generates a product catalog with Log-Normal prices and Pareto weights.
        """
        # SKU IDs
        skus = range(10000, 10000 + self.num_products)
        
        # Categories
        categories = ['Ausrüstung', 'Bekleidung', 'Schuhe']
        cat_weights = [0.3, 0.4, 0.3]
        
        cats = np.random.choice(categories, size=self.num_products, p=cat_weights)
        
        # Base Price Logic (Log-Normal)
        # We handle this by iterating or array-wise
        prices = []
        return_probs = []
        
        for cat in cats:
            if cat == 'Schuhe':
                # Expensive, high return rate
                p = np.random.lognormal(mean=4.8, sigma=0.5) # approx 120
                r = 0.30
            elif cat == 'Bekleidung':
                # Mid price, mid return rate
                p = np.random.lognormal(mean=4.4, sigma=0.6) # approx 80
                r = 0.15
            else: # Ausrüstung
                # Expensive but low returns
                p = np.random.lognormal(mean=5.0, sigma=0.7) # approx 150
                r = 0.05
            
            # Clip limits
            p = max(20, min(p, 800))
            prices.append(round(p, 2))
            return_probs.append(r)
            
        # Assign Price Tiers
        tiers = []
        for p in prices:
            if p < 80:
                tiers.append('budget')
            elif p <= 180:
                tiers.append('mid')
            else:
                tiers.append('premium')
        
        # Sales Rank (Pareto 80/20)
        # Using a Zipfian/Power law for weights
        # Lower rank = higher sales. We need 'weights' for sampling.
        # We can simulate this by assigning a random 'popularity_score' from a Pareto distribution
        popularity = np.random.pareto(a=2.5, size=self.num_products)
        
        df = pd.DataFrame({
            'sku_id': skus,
            'category': cats,
            'avg_price_eur': prices,
            'price_tier': tiers,
            'return_prob': return_probs,
            'popularity_score': popularity
        })
        
        # Standard Cost (COGS) is 40-60% of Price
        df['unit_cost_eur'] = df['avg_price_eur'] * np.random.uniform(0.40, 0.60, size=self.num_products)
        df['unit_cost_eur'] = df['unit_cost_eur'].round(2)
        
        df['product_name'] = [f"{c} Model {i}" for i, c in enumerate(df['category'])]
        
        return df

    def reclassify_product(self, product_row, date_obj):
        """
        Reclassifies a single product:
        - Updates price
        - Updates tier
        - Sets volume elasticity flag (to be handled in OrderFactory)
        Returns: (updated_row, snapshot_dict)
        """
        current_tier = product_row['price_tier']
        current_price = product_row['avg_price_eur']
        
        # Determine direction
        # 70% UP, 30% DOWN
        # Constraint: Budget -> Mid -> Premium (One step only)
        
        direction = None # 'up' or 'down'
        
        if current_tier == 'budget':
            # Can only go UP
            direction = 'up'
        elif current_tier == 'premium':
            # Can only go DOWN
            direction = 'down'
        else: # 'mid'
            if np.random.random() < 0.70:
                direction = 'up'
            else:
                direction = 'down'
        
        new_tier = current_tier
        new_price = current_price
        
        if direction == 'up':
            if current_tier == 'budget': new_tier = 'mid'
            elif current_tier == 'mid': new_tier = 'premium'
            
            # Price increase 20-30%
            increase = np.random.uniform(1.20, 1.30)
            new_price = current_price * increase
            
        elif direction == 'down':
            if current_tier == 'premium': new_tier = 'mid'
            elif current_tier == 'mid': new_tier = 'budget'
            
            # Price decrease 15-20%
            decrease = np.random.uniform(0.80, 0.85)
            new_price = current_price * decrease
            
        # Update Row
        updated_row = product_row.copy()
        updated_row['price_tier'] = new_tier
        updated_row['avg_price_eur'] = round(new_price, 2)
        
        # Create Screenshot Record for Tracking
        snapshot = {
            'product_id': product_row['sku_id'],
            'old_tier': current_tier,
            'new_tier': new_tier,
            'old_price': current_price,
            'new_price': round(new_price, 2),
            'change_date': date_obj,
            'direction': direction
        }
        
        return updated_row, snapshot

class CustomerGenerator:
    def __init__(self, num_customers=5000):
        self.num_customers = num_customers
        
    def generate(self):
        ids = [uuid.uuid4().hex[:8] for _ in range(self.num_customers)]
        # Assign an activity score (how often they buy)
        # Zipfian distribution again for realistic LTV
        activity = np.random.zipf(a=2.0, size=self.num_customers)
        # normalize activity to probabilities
        activity_prob = activity / activity.sum()
        
        return pd.DataFrame({
            'customer_id': ids,
            'activity_prob': activity_prob
        })

class OrderFactory:
    def __init__(self, product_df, customer_df):
        self.products = product_df
        self.customers = customer_df
        # Create sampling probabilities for products
        self.prod_probs = self.products['popularity_score'] / self.products['popularity_score'].sum()
        
    def generate_orders_for_day(self, date_obj, expected_vol, shop_id, currency):
        """
        Generates N orders for a specific day.
        Returns: (orders_list, line_items_list)
        """
        # Sample actual N from Poisson
        n_orders = np.random.poisson(expected_vol)
        if n_orders == 0:
            return [], []
            
        # Select customers
        cust_ids = np.random.choice(
            self.customers['customer_id'], 
            size=n_orders, 
            p=self.customers['activity_prob']
        )
        
        orders = []
        line_items = []
        
        for cid in cust_ids:
            oid = uuid.uuid4().hex[:12]
            
            # Basket Size (Geometric-like)
            # P(1)=0.5, P(2)=0.3...
            basket_size = np.random.choice([1, 2, 3, 4], p=[0.50, 0.30, 0.15, 0.05])
            
            # Select Products
            # Simple weighted sampling for now (Ignoring cross-sell logic for MVP speed)
            selected_indices = np.random.choice(
                self.products.index, 
                size=basket_size, 
                p=self.prod_probs, 
                replace=False # Unique items per basket usually
            )
            
            basket_revenue = 0
            
            for idx in selected_indices:
                prod = self.products.loc[idx]
                qty = 1 # 90% chance of 1
                
                # Dynamic Price (Event Day?)
                # Passed from caller? For MVP, we assume constant price + random small variance
                # In real life, prices change. Here we use base price.
                price_paid = prod['avg_price_eur']
                
                # Apply Discount Logic (Simple 5% chance of 10% off)
                if np.random.random() < 0.05:
                    price_paid *= 0.90
                    
                # Return Logic
                did_return = np.random.random() < prod['return_prob']
                
                line_items.append({
                    'line_id': uuid.uuid4().hex[:12],
                    'order_id': oid,
                    'sku_id': prod['sku_id'],
                    'qty': qty,
                    'unit_price_paid': round(price_paid, 2),
                    'unit_cost': prod['unit_cost_eur'],
                    'is_returned': did_return
                })
                
            orders.append({
                'order_id': oid,
                'customer_id': cid,
                'shop_id': shop_id,
                'order_date': date_obj, # We keep it simple (Date only, no time for now)
                'currency_code': currency
            })
            
        return orders, line_items

