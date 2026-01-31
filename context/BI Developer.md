This is the **BI Developer / Data Analyst Project Plan**.
**Role:** BI Developer
**Focus:** Accuracy, User Experience (UX), DAX Logic, and Performance.
**Motto:** "If the numbers in the dashboard don't match the database, it's my fault. If the database is wrong, it's the Engineer's fault."
---
## 1. The Strategy: "The Golden Record" Validation
Before I build a single visual, I need to ensure my DAX matches the dbt logic perfectly. Power BI is notorious for "hidden logic" in context transitions. To prevent this, I request a specific **Validation Table** from the Data Engineer.
### 1.1 The Validation Artifact (`mnt_golden_kpi`)
I will ask the engineer to build a simple aggregation table in dbt that pre-calculates the KPIs at a Monthly/Shop grain. I will import this into Power BI purely for testing.
**Schema Request:**
* **Grain:** `Month` | `Shop`
* **Columns (Pre-calculated):**
* `dbt_total_revenue`
* `dbt_total_orders`
* `dbt_contribution_margin_abs`
* `dbt_marketing_spend`
### 1.2 The "Debug Page" in Power BI
I will create a hidden page in the report called `_DEBUG`.
* **Visual:** A Matrix Table.
* **Rows:** Month, Shop.
* **Columns:**
1. `[Total Revenue]` (My DAX Measure)
2. `Sum(dbt_total_revenue)` (The Database Column)
3. `Delta = [Total Revenue] - Sum(dbt_total_revenue)`
* **Conditional Formatting:** If `Delta != 0`, highlight RED.
* *Why this matters:* This proves that my DAX context logic (e.g., handling returns, currency) behaves exactly as the "Source of Truth" defines.
---
## 2. The Semantic Model (Power BI Backend)
My goal is a clean Star Schema. I will hide all "Fact" columns and only expose "Measures" to ensure users (and I) don't accidentally drag raw columns into charts.
### 2.1 Table Configuration
* **`fct_transactions`**:
* *Import Mode* (DuckDB via ODBC or Parquet).
* **Hide:** `sk_product`, `sk_shop`, `order_id`, `revenue_eur`, `cogs_eur`.
* **Expose:** None (All access via Measures).
* **`dim_calendar`**:
* Mark as "Date Table" (Crucial for Time Intelligence).
* Sort `MonthName` by `MonthNumber`.
* **`fct_budget_daily`**:
* Relationship to `dim_calendar` on Date.
* Relationship to `dim_shop` on ShopID.
### 2.2 Relationships
* `fct_transactions(date_key)` *:1 `dim_calendar(date_key)`
* `fct_transactions(product_key)` *:1 `dim_products(sku_id)`
* `fct_transactions(shop_key)` *:1 `dim_shop(shop_id)`
* **Cross-filter direction:** Single (Always Dimension filters Fact).
---
## 3. DAX Framework (The Calculation Logic)
I need to replicate the PDF's specific financial logic.
### 3.1 Base Measures (The Primitives)
```dax
// Count orders simply
[# Orders] = DISTINCTCOUNT(fct_transactions[order_id])
// Sales (Exclude Returns!)
[Total Revenue] =
CALCULATE(
SUM(fct_transactions[gross_revenue_eur]),
fct_transactions[is_returned] = FALSE()
)
// Cost of Goods
[Total COGS] =
CALCULATE(
SUM(fct_transactions[cogs_eur]),
fct_transactions[is_returned] = FALSE()
)
// The "Plan"
[Budget Revenue] = SUM(fct_budget_daily[budget_revenue])
```
### 3.2 Ratio Measures (The KPIs)
```dax
[AOV] = DIVIDE([Total Revenue], [# Orders], 0)
[Gross Margin %] =
VAR _margin = [Total Revenue] - [Total COGS]
RETURN DIVIDE(_margin, [Total Revenue], 0)
[Marketing Share %] = DIVIDE([Sum Marketing Cost], [Total Revenue], 0)
```
### 3.3 The "Variance" Logic (For Page 4)
The PDF uses specific "Waterfalls" to explain variance.
```dax
[Revenue Variance €] = [Total Revenue] - [Budget Revenue]
[Revenue Variance %] =
DIVIDE([Revenue Variance €], [Budget Revenue], 0)
// Conditional Formatting Measure
[CFG_Variance_Color] = IF([Revenue Variance %] < 0, "#D04A4A", "#5F8D4E") // Red/Green
```
---
## 4. Visualization & UI/UX Plan
I am reconstructing the "vantage Look & Feel" (Clean, White/Grey, Green Accents).
### 4.1 Page 1: Executive Overview (The "Landing")
* **Top Band:** KPI Cards (Orders, Revenue, AOV, Margin).
* *New:* Add "Sparklines" under the KPI cards to show the last 7 days trend.
* **Main Visual:** Area Chart (Revenue Actual vs Forecast).
* *The "Forecast" Trick:* Since dbt generates a budget for the future, I will plot `[Total Revenue]` as a solid line and `[Budget Revenue]` (for future dates) as a dotted line, creating that "Confidence Interval" look from the PDF.
* **Bottom Band:** Small Multiples (Bar Charts) by Shop.
### 4.2 Page 2: Product Deep Dive
* **Visual:** "Scatter Plot" (The Strategic View).
* X-Axis: Sales Volume (# Orders)
* Y-Axis: Return Rate %
* Bubble Size: Total Revenue
* *Insight:* Identify "High Volume / High Return" products (Problem Children) vs "High Volume / Low Return" (Stars).
### 4.3 Page 4: Variance Analysis (The "CFO View")
* **Visual:** Waterfall Chart.
* Break down the difference between Budget Margin and Actual Margin.
* Categories: `Volume Effect`, `Price Effect`, `Cost Creep`.
* **Visual:** "Small Multiple" Decomposition Trees.
* Allow the user to click "Germany" -> Breakdown by "Product Group" -> Breakdown by "Brand" to see exactly *where* we missed the budget.
---
## 5. Implementation Workflow
1. **Connect:** Setup ODBC/Parquet connection to DuckDB.
2. **Verify:** Load `mnt_golden_kpi` and `fct_transactions`. Build the Debug Page. **Stop if numbers don't match.**
3. **Model:** Hide columns, set relationships, mark Date table.
4. **Measure:** Write the core DAX library.
5. **Visualize:** Build the background canvas (Figma or PPT import) and overlay visuals.
6. **Publish:** Save as `.pbix`.
## 6. The Analyst's "Definition of Done"
* [ ] The "Debug Page" shows 0 Delta for all months.
* [ ] Selecting "Switzerland" in the slicer correctly converts/displays the underlying EUR values (as standardized in dbt).
* [ ] The "Forecast" line cleanly connects to today's Actuals.
* [ ] The dashboard loads in under 2 seconds (verified via Performance Analyzer).