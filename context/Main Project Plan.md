# Project Specification: E-Commerce BI Pipeline
**Version:** 1.0
**Status:** Approved for Development
**Owner:** Analytics Engineering Portfolio
**Objective:** Re-engineer a full-stack BI pipeline (Python → DuckDB → dbt → Power BI) to replicate the "vantage" Financial & Operational Dashboard using realistic synthetic data.
---
## 1. Business Requirements & Logic
### 1.1 Scope
The system must model the flow of **Orders, Revenues, Costs (COGS, Logistics, Marketing), and Budgets** for a DACH-region e-commerce retailer. It must handle multi-currency (CHF/EUR) input but normalize to EUR for reporting.
### 1.2 Core Metrics & KPIs (The "Truth")
*Reference: PDF Page 6 (Glossary)*
| Metric | Definition | Logic / Formula |
| :--- | :--- | :--- |
| **Gross Revenue (Bestellwert)** | Total value of items sold after discounts, before returns. | $\sum (Unit Price \times Qty)$ |
| **Net Revenue** | Gross Revenue minus Returns. | $\sum (Gross Revenue)$ where `is_returned = False` |
| **Orders (#)** | Count of distinct valid orders. | `Count(Order_ID)` |
| **AOV (Average Order Value)** | Average revenue per order. | $Gross Revenue / Orders$ |
| **COGS (Wareneinsatz)** | Cost of goods sold. | $\sum (Unit Cost \times Qty)$ |
| **Gross Margin** | Revenue minus COGS. | $Net Revenue - COGS$ |
| **Transaction Costs** | Variable logistics & payment fees. | Per Order Fee + (Weight Factor $\times$ Items) |
| **Marketing Costs** | Performance marketing spend. | Allocated from Daily Spend to Order level based on Revenue Share. |
| **Contribution Margin (Deckungsbeitrag)** | Net Profit after all variable costs. | $Gross Margin - Transaction Costs - Marketing Costs$ |
| **Budget Variance (VAR)** | Performance vs Plan. | $Actuals - Budget$ |
### 1.3 Regional Logic
* **Markets:** Germany (DE), Austria (AT), Switzerland (CH).
* **Currency:** Input for CH is CHF. Input for DE/AT is EUR. Reporting currency is **EUR**.
* **Fiscal Calendar:** Standard Gregorian (Jan 1 – Dec 31).
---
## 2. Synthetic Data Generation Specifications (Python)
**Goal:** Create a "Raw" dataset that feels organic, not mathematical.
### 2.1 Generator Parameters
* **Timeframe:** 1 Year (Jan 1, 2024 – Dec 31, 2024).
* **Volume:** ~30,000–50,000 Orders total (matches PDF scale).
### 2.2 Entity Logic & Distributions
#### A. Products (`raw_products`)
* **Categories:** Equipment (Ausrüstung), Apparel (Bekleidung), Footwear (Schuhe).
* **Price Logic:**
* *Base Price:* Gaussian distribution centered on €120 (Shoes), €80 (Apparel), €150 (Equipment).
* *Margin:* Standard Cost = MSRP $\times$ (0.4 to 0.6).
* **Pareto Distribution:** 20% of SKUs should generate 80% of sales volume.
#### B. Orders & Seasonality (`raw_orders`, `raw_line_items`)
* **Daily Volume:** Use a **Poisson Distribution** modified by seasonality factors:
* *Trend:* Slight linear growth (10% YoY).
* *Weekly:* Weekends = 1.2x multiplier; Tuesdays = 0.8x multiplier.
* *Monthly:* Spike last 5 days of month (payday effect).
* *Events:* Black Friday (Nov), Christmas (Dec), Summer Sale (July).
* **Basket Composition:**
* *Items per Order:* 1 to 5 items (weighted probability: 1 item=40%, 2 items=30%, etc.).
* *Cross-Sell:* If "Shoes" are bought, 30% chance of adding "Apparel" (Socks).
* **Returns:**
* Assign `return_rate` per category (e.g., Shoes 30%, Equipment 5%).
* Flag random orders as `is_returned` based on this probability.
#### C. Costs (`raw_marketing`, `raw_logistics_rules`)
* **Marketing Spend:** Do NOT generate at order level. Generate at **Day/Shop** level.
* Logic: $\approx$ 10-15% of *expected* revenue, but with noise.
* **Logistics:**
* Base fee per order (€3.50).
* Variable fee per item (€0.50).
* Surcharge for CH shipments (€5.00).
#### D. Budget (`raw_budget`)
* **Grain:** Month / Shop / Country.
* **Logic:** Calculate based on Actuals but **smooth the curve**.
* $Budget = Actuals \times (0.95 \text{ to } 1.05) - \text{Random Noise}$.
* *Crucial:* Ensure Budget does NOT match Actuals perfectly to allow for the Variance visuals on Page 4.
---
## 3. Data Schema: The "Raw" Output (DuckDB)
The Python script must output these CSVs/Tables into DuckDB:
1. **`raw_orders`**: `order_id`, `customer_id`, `shop_id`, `order_date` (timestamp), `currency_code`.
2. **`raw_line_items`**: `line_id`, `order_id`, `sku_id`, `quantity`, `unit_price_paid` (after discount), `unit_cost` (COGS), `is_returned` (bool).
3. **`raw_products`**: `sku_id`, `product_name`, `category`, `brand`, `brand_tier`.
4. **`raw_marketing_daily`**: `date`, `shop_id`, `spend_amount`, `currency`.
5. **`raw_budget_monthly`**: `month_start_date`, `shop_id`, `target_revenue`, `target_orders`, `target_margin`.
6. **`raw_exchange_rates`**: `date`, `from_currency`, `to_currency`, `rate`.
---
## 4. Transformation Logic (dbt)
### 4.1 Staging Layer (`stg_`)
* Standardize column names to `snake_case`.
* Cast string dates to `DATE` objects.
* Filter out any test data.
### 4.2 Intermediate Layer (`int_`) — The Business Logic Engine
**1. `int_exchange_rates_applied`**
* Join Orders/Costs with Exchange Rates.
* Convert all CHF values to EUR.
**2. `int_sales_enriched`**
* Join `stg_orders` + `stg_line_items` + `stg_products`.
* Calculate `gross_revenue_eur`, `cogs_eur` at line level.
* Calculate `logistics_cost_eur`:
* Formula: $Base + (Items \times Variable) + RegionSurcharge$.
**3. `int_marketing_allocated` (Crucial)**
* Grain: Order Level.
* Algorithm:
1. Take `stg_marketing_daily`.
2. Calculate total revenue for that Day+Shop.
3. Calculate each order's share of that day's revenue.
4. Allocate daily marketing cost to the order based on that share.
**4. `int_budget_daily`**
* Transform Monthly Budget → Daily Budget.
* Divide monthly targets by days in month (simple linear distribution) OR apply a "Day of Week" weight curve to make it realistic.
### 4.3 Marts Layer (`marts_`) — Power BI Ready
**1. `dim_calendar`**
* Date, Week, Month, Quarter, Year, Working Day Flag.
**2. `dim_product` & `dim_shop`**
* Standard dimension tables.
**3. `fct_transactions` (The Main Fact)**
* **Grain:** Order Line Item.
* **Columns:** `date_key`, `product_key`, `shop_key`, `order_id`, `qty`, `revenue_eur`, `cogs_eur`, `logistics_allocated_eur`, `marketing_allocated_eur`, `contribution_margin_eur`, `is_returned`.
* *Why:* Allows slicing Profitability by Product/Brand (Page 2 & 3).
**4. `fct_budget_daily`**
* **Grain:** Date, Shop.
* **Columns:** `budget_revenue`, `budget_orders`, `budget_margin`.
---
## 5. Repository Structure
This structure demonstrates "Analytics Engineering" seniority.
```text
vantage-rebuild/
├── data_generation/ # Python Scripts
│ ├── src/
│ │ ├── generators.py # Classes: Customer, Order, Product
│ │ ├── seasonality.py # Noise/Trend logic
│ │ └── main.py # Execution script
│ └── output/ # Generated CSVs
├── dbt_project/
│ ├── models/
│ │ ├── staging/ # 1:1 with Raw
│ │ ├── intermediate/ # Business Logic (Allocations, FX)
│ │ └── marts/ # Star Schema for PBI
│ ├── tests/ # Data Quality (assert margin < revenue)
│ └── dbt_project.yml
├── analysis/
│ └── queries.sql # Ad-hoc duckdb checks
├── viz/
│ └── vantage_dashboard.pbix
└── README.md # Documentation & Lineage
```
---
## 6. Visualization Requirements (Power BI)
### Global Settings
* **Theme:** Light grey background, Green/Grey palette (matching PDF).
* **Currency:** formatting to `€ #,##0.00`.
### Measure Definitions (DAX)
* `Actual Revenue = CALCULATE(SUM(fct_transactions[revenue_eur]), fct_transactions[is_returned] = FALSE)`
* `Budget Revenue = SUM(fct_budget_daily[budget_revenue])`
* `Variance % = DIVIDE([Actual Revenue] - [Budget Revenue], [Budget Revenue], 0)`
* `Forecast` (Page 1): Since we don't have a live ML model, use `Budget * 1.02` for future dates to simulate the dotted line.
### Page Implementation Guide
1. **Overview:** KPI Cards (Act vs Bud) + Line Chart (Act vs Forecast).
2. **Products:** Stacked Column Chart (Rev by Category) + Bubble Chart (Scatter: Qty vs Margin).
3. **Regional:** Map/Bar Chart using `dim_shop`.
4. **Variance:** "Waterfall Chart" breakdown.
* Start: Budget Margin
* Steps: Volume Effect, Price Effect, Cost Effect
* End: Actual Margin
---
## 7. Success Criteria
1. **Pipeline Runs:** `python main.py` -> `dbt build` runs without errors.
2. **Data Quality:** `dbt test` passes (no negative prices, no orphaned orders).
3. **Visual Match:** The PBI dashboard looks 90% identical to the PDF.
4. **Logic Check:** The "Sum of Marketing Allocated" in `fct_transactions` equals the "Total Marketing Spend" in `raw_marketing_daily`.