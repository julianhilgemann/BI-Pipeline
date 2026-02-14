# KPI Glossary

This document contains the definitions and formulas for the Key Performance Indicators (KPIs) and measures used in the PowerBI logic.

| Name | Formula | Definition |
|---|---|---|
| AOV ACT (€) | `DIVIDE([Gross Revenue ACT (€)], [Orders Total ACT (#)], 0)` | Average Order Value. The average revenue generated per order, calculated by dividing total gross revenue by the total number of orders. |
| COGS Total ACT (€) | `SUM(fct_transactions[cogs_eur])` | Cost of Goods Sold. The total direct costs attributable to the production of the goods sold, summed from transaction data. |
| Gross Revenue ACT (€) | `SUM(fct_transactions[gross_revenue_eur])` | Actual Gross Revenue. The total revenue from sales before any deductions, summed from transaction data. |
| Logistics Cost ACT (€) | `SUM(fct_transactions[logistics_allocated_eur])` | Logistics Costs. The total costs associated with logistics and delivery, allocated to transactions. |
| Marketing Cost ACT (€) | `SUM(fct_transactions[marketing_cost_allocated_eur])` | Marketing Costs. The total costs associated with marketing activities, allocated to transactions. |
| Orders Total ACT (#) | `DISTINCTCOUNT(fct_transactions[order_id])` | Total Orders. The count of unique orders placed. |
| Returned ACT (€) | `CALCULATE([Gross Revenue ACT (€)], fct_transactions[is_returned] = TRUE())` | Returned Revenue. The value of gross revenue associated with returned transactions. |
| CM1 ACT (€) | `[Gross Revenue ACT (€)] - [COGS Total ACT (€)]` | Contribution Margin 1. The profit remaining after deducting the Cost of Goods Sold from Gross Revenue. |
| CM1 Margin ACT (%) | `DIVIDE([CM1 ACT (€)], [Gross Revenue ACT (€)], 0)` | CM1 Margin Percentage. The percentage of Gross Revenue that remains as Contribution Margin 1. |
| CM2 ACT (€) | `[CM1 ACT (€)] - [Marketing Cost ACT (€)] - [Logistics Cost ACT (€)]` | Contribution Margin 2. The profit remaining after deducting Marketing and Logistics costs from CM1. |
| CM2 Margin ACT (%) | `DIVIDE([CM2 ACT (€)], [Gross Revenue ACT (€)], 0)` | CM2 Margin Percentage. The percentage of Gross Revenue that remains as Contribution Margin 2. |
| Gross Revenue BUD (€) | `SUM(fct_budget_daily[daily_budget_revenue])` | Budgeted Gross Revenue. The target gross revenue defined in the daily budget. |
| Gross Revenue BUD Performance (String) | `FORMAT([Gross Revenue VAR vs BUD (%)], "+0.0% vs BUD;-0.0% vs BUD")` | Budget Performance String. A formatted string showing the percentage variance against the budget for display purposes. |
| Gross Revenue VAR vs BUD (%) | `DIVIDE([Gross Revenue VAR vs BUD (€)], [Gross Revenue BUD (€)], 0)` | Variance vs Budget (%). The percentage difference between actual gross revenue and budgeted gross revenue. |
| Gross Revenue VAR vs BUD (€) | `[Gross Revenue ACT (€)] - [Gross Revenue BUD (€)]` | Variance vs Budget (€). The monetary difference between actual gross revenue and budgeted gross revenue. |
| Gross Revenue LM (€) | `CALCULATE([Gross Revenue ACT (€)], DATEADD('synth_dim_date'[Date], -1, MONTH))` | Gross Revenue Last Month. The gross revenue generated in the previous month relative to the current context. |
| Gross Revenue LM Delta (€) | `[Gross Revenue ACT (€)] - [Gross Revenue LM (€)]` | Gross Revenue Month-over-Month Delta. The difference in gross revenue between the current period and the previous month. |
| Gross Revenue MoM (%) | `DIVIDE([Gross Revenue LM Delta (€)], [Gross Revenue LM (€)], 0)` | Month-over-Month Growth (%). The percentage growth in gross revenue compared to the previous month. |
| Gross Revenue MTD (€) | `TOTALMTD([Gross Revenue ACT (€)], 'synth_dim_date'[Date])` | Gross Revenue Month-to-Date. The cumulative gross revenue from the beginning of the current month to the current date. |
| Gross Revenue QTD (€) | `TOTALQTD([Gross Revenue ACT (€)], 'synth_dim_date'[Date])` | Gross Revenue Quarter-to-Date. The cumulative gross revenue from the beginning of the current quarter to the current date. |
| Gross Revenue R12M Avg (€) | `CALCULATE(AVERAGEX(VALUES('dim_calendar'[month_name]), [Gross Revenue ACT (€)]), DATESINPERIOD('dim_calendar'[date_key], LASTDATE('dim_calendar'[date_key]), -12, MONTH))` | Rolling 12-Month Average. The average monthly gross revenue over the last 12 months. |
| Gross Revenue R30D (€) | `CALCULATE([Gross Revenue ACT (€)], DATESINPERIOD('synth_dim_date'[Date], LASTDATE('dim_calendar'[date_key]), -30, DAY))` | Gross Revenue Last 30 Days. The total gross revenue generated in the last 30 days. |
| Gross Revenue YTD (€) | `TOTALYTD([Gross Revenue ACT (€)], 'synth_dim_date'[Date])` | Gross Revenue Year-to-Date. The cumulative gross revenue from the beginning of the current year to the current date. |
| is_blank | `BLANK()` | Is Blank. Returns a blank value, typically used for conditional formatting or as a placeholder. |
| COGS Waterfall | `-1 * [COGS Total ACT (€)]` | COGS (Waterfall). Negative COGS value used for visualizing cost deductions in waterfall charts. |
| Delta ACT vs BUD MTD | `CALCULATE([Gross Revenue VAR vs BUD (%)], DATESMTD('synth_dim_date'[Date]))` | MTD Variance vs Budget. The month-to-date percentage variance of actual revenue against the budget. |
| Delta ACT vs BUD QTD | `CALCULATE([Gross Revenue VAR vs BUD (%)], DATESQTD('synth_dim_date'[Date]))` | QTD Variance vs Budget. The quarter-to-date percentage variance of actual revenue against the budget. |
| Delta ACT vs BUD YTD | `CALCULATE([Gross Revenue VAR vs BUD (%)], DATESYTD('synth_dim_date'[Date]))` | YTD Variance vs Budget. The year-to-date percentage variance of actual revenue against the budget. |
| Logistics Waterfall | `-1 * [Logistics Cost ACT (€)]` | Logistics (Waterfall). Negative logistics cost value used for visualizing cost deductions in waterfall charts. |
| Marketing Waterfall | `-1 * [Marketing Cost ACT (€)]` | Marketing (Waterfall). Negative marketing cost value used for visualizing cost deductions in waterfall charts. |
| Profit ACT (€) | `[CM2 Margin ACT (%)] * [Gross Revenue ACT (€)]` | Actual Profit. The calculated profit based on CM2 margin and gross revenue. |
| Profit Waterfall | `[Gross Revenue ACT (€)] + [COGS Waterfall] + [Logistics Waterfall] + [Marketing Waterfall]` | Profit (Waterfall). A validation measure that reconstructs profit by summing revenue and negative cost components for waterfall charts. |
