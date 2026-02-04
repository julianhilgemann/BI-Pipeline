# DAX Guidelines: Vantage Data Model

**Version:** 1.0  
**Date:** 2024-02-04  
**Target Audience:** BI Analysts / Developers  

---

## 1. Naming Conventions

To ensure a clean and searchable field list in Power BI, we strictly adhere to the following naming pattern:

`[Metric] [Context] [Scenario] ([Unit])`

### Components
1.  **Metric**: What are we counting? (e.g., `Revenue`, `Orders`, `Margin`, `Quantity`)
2.  **Context** (Optional): Specific subset or attribute (e.g., `Product`, `Customer`, `LFL`)
3.  **Scenario**: Timeframe or comparison type (e.g., `ACT`, `BUD`, `PY`, `VAR`, `YoY %`)
4.  **Unit** (Optional): Clarification if ambiguous (e.g., `(€)`, `(#)`, `(%)`)

### Examples
| Bad Name | Good Name | Logic |
| :--- | :--- | :--- |
| `Sum of Revenue` | `Gross Revenue ACT (€)` | Explicit Metric + Scenario + Unit |
| `Orders 2023` | `Orders Total ACT (#)` | "Total" implies all orders, "ACT" = Actuals |
| `Profit %` | `CM1 Margin ACT (%)` | Specific Profit Type (CM1) defined |
| `Diff to Budget` | `Revenue VAR vs BUD (€)` | Clear Variance Context |

---

## 2. Formatting Standards

All measures must have explicit formatting defined in the model.

| Data Type | Format String | Example |
| :--- | :--- | :--- |
| **Currency** | `Currency (EUR) \u20ac#,0.00` | `€ 1,250.50` |
| **Whole Number** | `Whole Number #,0` | `1,250` |
| **Percentage** | `Percentage 0.0%` | `25.5%` |
| **Delta Strings** | `+0.0% vs Limit;-0.0% vs Limit` | `+5.2% vs BUD` |

---

## 3. Standard Calculations

All measures are based on the **Vantage Data Model** (`fct_transactions`, `fct_budget_daily`, `dim_calendar`, `dim_products`).

> [!NOTE]
> **Budget Limitation**: The Budget table (`fct_budget_daily`) **only contains Revenue**. Therefore, Cost and Margin variance measures are not supported.

### A. Base Metrics (Actuals)

**Volume**
```dax
Orders Total ACT (#) = DISTINCTCOUNT(fct_transactions[order_id])
Quantity Total ACT (#) = SUM(fct_transactions[quantity])
```

**Revenue**
```dax
Gross Revenue ACT (€) = SUM(fct_transactions[gross_revenue_eur])
```

**Costs**
```dax
// Cost of Goods Sold
COGS Total ACT (€) = SUM(fct_transactions[cogs_eur])

// Allocated Costs
Marketing Cost ACT (€) = SUM(fct_transactions[marketing_cost_allocated_eur])
Logistics Cost ACT (€) = SUM(fct_transactions[logistics_allocated_eur])
```

### B. Profitability (Margins)

**Contribution Margin 1 (Product Profit)**
```dax
CM1 ACT (€) = [Gross Revenue ACT (€)] - [COGS Total ACT (€)]
CM1 Margin ACT (%) = DIVIDE([CM1 ACT (€)], [Gross Revenue ACT (€)], 0)
```

**Contribution Margin 2 (Operating Profit)**
```dax
CM2 ACT (€) = [CM1 ACT (€)] - [Marketing Cost ACT (€)] - [Logistics Cost ACT (€)]
CM2 Margin ACT (%) = DIVIDE([CM2 ACT (€)], [Gross Revenue ACT (€)], 0)
```

**Average Order Value**
```dax
AOV ACT (€) = DIVIDE([Gross Revenue ACT (€)], [Orders Total ACT (#)], 0)
```

### C. Budget & Variance (Revenue Only)

**Budget**
```dax
Gross Revenue BUD (€) = SUM(fct_budget_daily[daily_budget_revenue])
```

**Variances**
```dax
// Amount Variance
Gross Revenue VAR vs BUD (€) = [Gross Revenue ACT (€)] - [Gross Revenue BUD (€)]

// Percentage Variance
Gross Revenue VAR vs BUD (%) = DIVIDE([Gross Revenue VAR vs BUD (€)], [Gross Revenue BUD (€)], 0)
```

**Dynamic Title String**
```dax
Gross Revenue BUD Performance (String) = 
FORMAT([Gross Revenue VAR vs BUD (%)], "+0.0% vs BUD;-0.0% vs BUD")
```

---

## 4. Time Intelligence Patterns

**Prerequisite**: Ensure `dim_calendar` is marked as the Date Table and related to fact tables on `date_key`.

### A. To-Date Calculations (YTD, QTD, MTD)

**Year-to-Date (YTD)**
```dax
Gross Revenue YTD (€) = 
TOTALYTD([Gross Revenue ACT (€)], 'dim_calendar'[date_key])
```

**Quarter-to-Date (QTD)**
```dax
Gross Revenue QTD (€) = 
TOTALQTD([Gross Revenue ACT (€)], 'dim_calendar'[date_key])
```

**Month-to-Date (MTD)**
```dax
Gross Revenue MTD (€) = 
TOTALMTD([Gross Revenue ACT (€)], 'dim_calendar'[date_key])
```

### B. Period-over-Period (MoM, QoQ, YoY)

**Previous Month**
```dax
Gross Revenue LM (€) = 
CALCULATE(
    [Gross Revenue ACT (€)],
    DATEADD('dim_calendar'[date_key], -1, MONTH)
)
```

**Month-over-Month (MoM)**
```dax
// Amount Delta
Gross Revenue YoY Delta (€) = [Gross Revenue ACT (€)] - [Gross Revenue LM (€)]

// % Delta
Gross Revenue MoM (%) = DIVIDE([Gross Revenue YoY Delta (€)], [Gross Revenue LM (€)], 0)
```
*(Repeat pattern for Previous Year `DATEADD(..., -1, YEAR)` and Previous Quarter `DATEADD(..., -1, QUARTER)`)*

---

## 5. Rolling Calculations (Moving Averages)

Use these for smoothing trends.

**Rolling 30 Days Sum**
```dax
Gross Revenue R30D (€) = 
CALCULATE(
    [Gross Revenue ACT (€)],
    DATESINPERIOD(
        'dim_calendar'[date_key],
        LASTDATE('dim_calendar'[date_key]),
        -30,
        DAY
    )
)
```

**Rolling 12 Months Average**
```dax
Gross Revenue R12M Avg (€) = 
CALCULATE(
    AVERAGEX(
        VALUES('dim_calendar'[month_name]), 
        [Gross Revenue ACT (€)]
    ),
    DATESINPERIOD(
        'dim_calendar'[date_key],
        LASTDATE('dim_calendar'[date_key]),
        -12,
        MONTH
    )
)
```

---

## 6. Implementation Checklist
- [ ] Base Measures created (Revenue, Orders, COGS)
- [ ] Calculated Measures created (Margins, AOV)
- [ ] Formatting Strings applied to all measures
- [ ] Folder Structure created in Power BI (`00 - Key Metrics`, `01 - Time Intelligence`, etc.)
- [ ] Hidden base columns (`quantity`, `gross_revenue`) to force use of explicit measures
