# Analytics Engineering Implementation Spec

This document translates the business requirements and data generation outputs into a concrete execution plan using `dbt-duckdb`.

**Role:** Analytics Engineer
**Tools:** Python (Loader), DuckDB (Storage/Compute), dbt Core (Transformation), SQL (Logic).
---
## 1. Infrastructure & Setup
### 1.1 The Database Strategy (DuckDB)
Since this is a local/portfolio project, we treat DuckDB as a persistent file-based data warehouse.
* **File Path:** `./data/vantage.duckdb`
* **Ingestion Pattern:** "Drop and Reload" for Raw.
* We do not need incremental loading for `raw` since the Python generator outputs the full history every time.
* Create a `load_data.py` script that takes the CSVs from the generator and executes:
```python
con.execute("CREATE OR REPLACE TABLE raw_orders AS SELECT * FROM read_csv_auto('output/orders.csv')")
```
* **Why:** Ensures idempotency. Every run starts from a clean state.
### 1.2 dbt Project Configuration (`dbt_project.yml`)
* **Profile:** `duckdb_local`
* **Materialization Strategy:**
* `staging`: `view` (ephemeral, fast)
* `intermediate`: `ephemeral` or `table` (depending on complexity, `table` helps debugging)
* `marts`: `table` (performance for Power BI)
---
## 2. Layer 1: Staging (Cleaning & Standardization)
**Goal:** 1:1 mapping with Raw, but with correct data types and consistent naming.
**Convention:** Rename all ID columns to `_id` suffix, timestamps to `_at`.
### `stg_orders.sql`
* **Source:** `raw_orders`
* **Logic:** Cast string dates to `TIMESTAMP`.
* **Columns:**
* `order_id` (PK)
* `customer_id`
* `shop_id` (FK: DE, AT, CH)
* `ordered_at` (Timestamp)
* `order_date` (Date - derived from timestamp)
* `currency_code` (EUR, CHF)
### `stg_line_items.sql`
* **Source:** `raw_line_items`
* **Logic:** Handle nulls (though generator shouldn't produce them).
* **Columns:**
* `line_item_id` (PK - generate using `md5(order_id || sku_id)` if missing)
* `order_id`
* `sku_id`
* `quantity` (Int)
* `unit_price_local` (Decimal 10,2 - "Paid Price")
* `unit_cost_local` (Decimal 10,2 - "COGS")
* `is_returned` (Boolean)
### `stg_marketing_daily.sql`
* **Source:** `raw_marketing_daily`
* **Columns:**
* `spend_date`
* `shop_id`
* `marketing_spend_local`
---
## 3. Layer 2: Intermediate (The "Business Logic" Engine)
This is the most critical layer. We must solve **Currency Normalization** and **Cost Allocation**.
### 3.1 Currency Normalization
**Model:** `int_exchange_rates.sql`
* **Logic:** Filter for "To EUR". If source is EUR, rate is 1.0.
* **Grain:** Date + Currency.
**Model:** `int_orders_standardized.sql`
* **Input:** `stg_orders`, `stg_line_items`, `int_exchange_rates`.
* **Transformation:**
* Join Line Items to Orders.
* Join to Exchange Rates on `order_date` and `currency_code`.
* **Calculation:**
* `gross_revenue_eur` = `unit_price_local` * `exchange_rate` * `quantity`
* `cogs_eur` = `unit_cost_local` * `exchange_rate` * `quantity`
* **Output:** Line-item grain with all values in EUR.
### 3.2 Logistics Cost Calculation
**Model:** `int_logistics_costs.sql`
* **Input:** `stg_orders`, `stg_line_items`
* **Logic:**
1. Aggregate Line Items to Order Grain (Count Items).
2. Apply Case Logic:
```sql
CASE
WHEN shop_id = 'CH' THEN 8.50 + (item_count * 0.50)
ELSE 3.50 + (item_count * 0.50)
END as logistics_cost_eur
```
* **Output:** `order_id`, `logistics_cost_eur`.
### 3.3 Marketing Allocation (The Weighted Split)
**Model:** `int_marketing_allocated.sql`
* **Goal:** Push daily spend down to the order level.
* **CTE 1: Daily Shop Sales**
* Sum `gross_revenue_eur` group by `order_date`, `shop_id`.
* **CTE 2: Daily Shop Spend**
* Select from `stg_marketing_daily`.
* **CTE 3: Allocation Factor**
* Join CTE 1 & 2.
* `cost_per_revenue_euro` = `total_marketing_spend` / `total_daily_revenue`.
* **Final Select:**
* Join `int_orders_standardized` to CTE 3.
* `allocated_marketing_eur` = `order_gross_revenue_eur` * `cost_per_revenue_euro`.
* **Tech Note:** Handle "Divide by Zero" if a shop has spend but 0 revenue (unlikely but possible) by using `NULLIF`.
---
## 4. Layer 3: Marts (Consumption Layer)
These tables connect directly to Power BI. We use **Dimensional Modeling (Star Schema)**.
### `dim_calendar.sql`
* Generated via SQL (dbt_utils or generic date spine).
* **Cols:** `date_day`, `year`, `month_name`, `iso_week`, `is_weekend`.
### `dim_products.sql`
* From `stg_products`.
* **Cols:** `sku_id`, `product_name`, `category`, `sub_category`, `brand`, `brand_tier`.
### `fct_transactions.sql` (The Central Fact)
* **Grain:** Order Line Item.
* **Joins:**
* `int_orders_standardized` (Base)
* `int_logistics_costs` (Joined on Order ID, then allocated by price-weight or simply stored as a separate line or header metric. *Better approach for BI:* Store logistics at Order Header level, or split evenly across lines. Let's split evenly by line count for simplicity).
* `int_marketing_allocated` (Joined on Order ID).
* **Columns:**
* **Keys:** `date_key`, `product_key`, `shop_key`, `customer_key`, `order_id`, `line_item_id`.
* **Metrics (EUR):**
* `quantity`
* `gross_revenue`
* `cogs`
* `logistics_cost_allocated` (Logistics Cost / Items in Order)
* `marketing_cost_allocated` (Marketing Cost * (Line Rev / Order Rev))
* `contribution_margin` (Calculated: Rev - COGS - Log - Mkt)
* **Attributes:** `is_returned`.
### `fct_budget_daily.sql`
* **Input:** `stg_budget` (Monthly).
* **Transformation:** Fan out Monthly budget to Daily grain.
* Join to `dim_calendar`.
* `daily_budget_revenue` = `monthly_budget` / `days_in_month`.
* **Columns:** `date_day`, `shop_id`, `budget_revenue`, `budget_orders`.
---
## 5. Data Quality & Testing Strategy (`schema.yml`)
This is where you prove you are a pro. Don't just test unique keys.
### 5.1 Generic Tests
* **`fct_transactions`**:
* `order_id`: `not_null`
* `sku_id`: `relationships` (to `dim_products`)
* `gross_revenue`: `>= 0` (Assuming negative revenue is handled via a separate returns flag, or valid if strictly sales).
### 5.2 Singular Tests (Business Logic Assertions)
Create `.sql` files in `tests/`.
**Test 1: The Allocation Check (`assert_marketing_fully_allocated.sql`)**
* **Logic:** The sum of marketing cost in the Fact table must equal the sum of raw marketing spend in the Source table (within a small rounding error).
```sql
with source as (
select sum(marketing_spend_local) as total from {{ ref('stg_marketing_daily') }}
),
fact as (
select sum(marketing_cost_allocated) as total from {{ ref('fct_transactions') }}
)
select * from source, fact
where abs(source.total - fact.total) > 1.0 -- Tolerate 1 EUR rounding diff
```
**Test 2: Margin Consistency (`assert_positive_contribution.sql`)**
* **Logic:** Warn if `contribution_margin` is negative (unless it's a return).
```sql
select * from {{ ref('fct_transactions') }}
where contribution_margin < 0
and is_returned = false
-- This might happen with high marketing, so maybe severity: warn
```
---
## 6. The "Golden" Project Structure
```text
dbt_project/
├── models/
│ ├── staging/
│ │ ├── _sources.yml # Define DuckDB sources here
│ │ ├── stg_orders.sql
│ │ └── ...
│ ├── intermediate/
│ │ ├── finance/
│ │ │ ├── int_exchange_rates.sql
│ │ │ └── int_marketing_allocated.sql
│ │ └── sales/
│ │ └── int_orders_standardized.sql
│ └── marts/
│ ├── _schema.yml # Documentation & Tests
│ ├── dim_products.sql
│ ├── fct_transactions.sql
│ └── fct_budget_daily.sql
├── seeds/
│ └── country_mapping.csv # Static mapping for shops
├── macros/
│ └── get_fiscal_year.sql # Custom logic if needed
└── tests/
└── assert_marketing_fully_allocated.sql
```
## 7. Execution Workflow
1. **Generate Data:** `python src/generate.py` (Outputs CSVs).
2. **Load DB:** `python src/load_duckdb.py` (CSVs -> Raw Tables).
3. **dbt Deps:** `dbt deps` (Get dbt-utils, dbt-date).
4. **Build:** `dbt build` (Runs seeds, models, snapshots, and tests in order).
* *Note:* `dbt build` is superior to `dbt run` + `dbt test` because it fails fast if an upstream test fails.
5. **Serve:** Point Power BI to `vantage.duckdb`.