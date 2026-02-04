# Data Generation Model Specification

This document outlines the statistical distributions, time-series components, and relational constraints required to simulate the vantage e-commerce dataset realistically.

**Objective:** Generate a dataset of ~35,000 orders over a 1-year period that exhibits realistic seasonality, product affinity, and variance, suitable for `dbt` ingestion.
---
## 1. The Modeling Philosophy: "Controlled Stochasticity"
We will not train a generative AI model (GAN/VAE) as it is overkill. Instead, we will use a **Non-Homogeneous Poisson Process (NHPP)** for volume generation and **Weighted Probabilistic Sampling** for basket composition.
**Core Equation for Daily Order Volume ($\lambda_t$):**
$$ \lambda_t = \text{Base} \times \text{Trend}(t) \times \text{Season}_{week}(t) \times \text{Season}_{year}(t) \times \text{Event}(t) $$
Where:
* $\lambda_t$: Expected number of orders on day $t$.
* Actual Orders $N_t \sim \text{Poisson}(\lambda_t)$.
---
## 2. Module 1: The Product Catalog (The Supply Side)
Before generating orders, we need a static inventory universe.
**Generation Logic:**
* **Total SKUs:** ~500 SKUs.
* **Hierarchy:** Category $\rightarrow$ Sub-Category $\rightarrow$ Product.
* **Price Modeling:** Prices follow a log-normal distribution (long tail of expensive gear).
**Schema: `raw_products`**
| Column | Type | Distribution / Logic |
| :--- | :--- | :--- |
| `sku_id` | INT | Sequential (10000 to 10500) |
| `category` | STR | `['Ausrüstung', 'Bekleidung', 'Schuhe']` |
| `base_price_eur` | FLOAT | Log-Normal($\mu=4.5, \sigma=0.6$). Clip range: [€20, €800]. |
| `cost_price_eur` | FLOAT | `base_price` $\times$ Uniform(0.40, 0.60). (Margin variability). |
| `sales_rank` | FLOAT | Power Law ($\alpha=2.5$). Used for sampling weight. |
| `return_probability`| FLOAT | Beta Distribution. Shoes $\mu=0.30$, Gear $\mu=0.05$. |
**Technical Note:**
Use `sales_rank` to assign a "popularity weight" ($w_i$) to each SKU.
$$ P(\text{pick SKU}_i) = \frac{w_i}{\sum w} $$
This ensures 20% of products drive 80% of volume (Pareto Principle).
---
## 3. Module 2: The Temporal Backbone (Time Series Generation)
We generate a daily dataframe `df_days` to act as the lambda driver.
**Components:**
1. **Linear Trend:**
* $T_t = 1 + (0.0003 \times t)$
* *Effect:* ~10% organic growth YoY.
2. **Weekly Seasonality:**
* Multipliers: `[Mon: 0.9, Tue: 0.85, Wed: 0.9, Thu: 0.95, Fri: 1.0, Sat: 1.2, Sun: 1.3]`
* *Logic:* E-commerce peaks on weekends.
3. **Monthly Seasonality (The "Payday Effect"):**
* Multiplier: $1.15$ if Day > 25, else $1.0$.
4. **Special Events (Shocks):**
* Create a binary mask or multiplier map.
* `Summer Sale` (July 15-30): 1.5x multiplier.
* `Black Week` (Nov 20-27): 3.0x multiplier.
* `Christmas` (Dec 1-15): 1.8x multiplier.
**Output:** A vector of $\lambda_t$ for every day of the year for each Shop (DE, AT, CH).
* *Note:* Scale $\lambda$ differently per shop (e.g., DE=1.0, AT=0.3, CH=0.2).
---
## 4. Module 3: Order Factory (The Transactional Layer)
Iterate through `df_days` and generate $N_t$ orders.
### 4.1 Order Header Generation
**Schema: `raw_orders`**
| Column | Logic |
| :--- | :--- |
| `order_id` | UUID or Sequential. |
| `shop_id` | From the daily loop (DE/AT/CH). |
| `customer_id` | Sample from a pool of 5,000 IDs. Use a **Zipfian distribution** so some customers buy 10x, most buy 1x. |
| `order_ts` | Random timestamp between 06:00 and 23:59 on day $t$. |
### 4.2 Basket Composition (The "Itemizer")
This is critical for realistic AOV and Margin analysis.
**Algorithm:**
1. **Determine Basket Size ($K$):**
* Sample $K$ from a Shifted Geometric Distribution or Custom Discrete:
* `P(1)=0.50, P(2)=0.30, P(3)=0.15, P(4+)=0.05`.
2. **Select Products:**
* **Item 1:** Weighted sample from `raw_products` using `sales_rank`.
* **Item 2..K (Cross-Sell):**
* If Item 1 == 'Schuhe', boost probability of 'Bekleidung' (Socks/Pants) by factor 3.0.
* Otherwise, independent weighted sampling.
3. **Apply Discounts:**
* If `is_event_day` (Black Friday), apply -20% to `unit_price`.
* Else, 5% probability of a -10% discount.
**Schema: `raw_line_items`**
| Column | Logic |
| :--- | :--- |
| `order_id` | FK to Header. |
| `sku_id` | Selected Product. |
| `qty` | Usually 1 (90%), rarely 2. |
| `unit_price_paid`| `base_price` * (1 - discount). |
| `is_returned` | Bernoulli Trial ($p=$ `product.return_probability`). |
---
## 5. Module 4: Cost & Budget Layers
### 5.1 Marketing Spend (Aggregated)
Marketing is not transactional; it is an aggregate investment curve.
**Logic:**
* Target Marketing Ratio ($MER$) = 15% of Revenue.
* Generate `daily_revenue` first (from the steps above).
* `marketing_spend_t` = `daily_revenue_t` $\times$ Normal($\mu=0.15, \sigma=0.02$).
* *Lag Effect:* Shift the curve back by 2 days (spend happens *before* the conversion).
**Schema: `raw_marketing_daily`**
`date`, `shop_id`, `spend_eur`
### 5.2 The Budget (The "Plan")
The budget must look like a forecast, meaning it is smoother than actuals.
**Modeling Approach:**
1. Take the `daily_revenue` generated in Module 3.
2. Apply a **Rolling Average** (window=7 days) to smooth out noise.
3. Apply a small bias (e.g., multiply by 1.02 to show "We missed target" or 0.98 for "We beat target").
4. Aggregate to Monthly grain.
**Schema: `raw_budget_monthly`**
`month`, `shop_id`, `plan_revenue`, `plan_orders`, `plan_margin`
---
## 6. Implementation Strategy (Python)
**Libraries:** `pandas`, `numpy`, `scipy.stats`.
**Performance:**
Do *not* loop row-by-row. Use Vectorization.
1. Generate the index (35k rows).
2. `df['shop_id'] = np.random.choice(...)`
3. `df['basket_size'] = np.random.choice(...)`
4. Then explode the dataframe to create line items.
**Seed Control:**
Set `np.random.seed(42)` at the start of the script. This ensures that every time you run the pipeline, the "Random" data is identical, which is crucial for debugging dbt transformations.
## 7. Validation Checks (The "Sanity Check")
Before exporting to CSV, the script must assert:
1. **AOV Check:** `Total Revenue / Total Orders` should be $\approx$ €200-240.
2. **Margin Check:** `Sum(Revenue - Cost) / Revenue` should be $\approx$ 40%.
3. **Weekend Check:** `groupby(weekday)['orders'].mean()` should show Sat/Sun > Mon-Fri.
---
### Data Scientist's Handoff Summary
* **Input:** Config parameters (Year, Growth Rate, Shop Weights).
* **Model:** NHPP for Time Series + Weighted Sampling for Content.
* **Output:** 5 CSVs normalized for Star Schema ingestion.
* **Complexity:** Low-Medium (No ML training, just statistical simulation).