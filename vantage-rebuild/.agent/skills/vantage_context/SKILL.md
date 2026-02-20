---
name: vantage_context
description: Critical project context, path definitions, and workflow standards for the Vantage Rebuild project. Use this to understand where data lives and how to run commands.
---

# Vantage Rebuild Project Context

## 1. Repository Structure
- **`data_generation/`**: Python scripts for generating synthetic data.
  - `src/`: Source code (`main.py`, `generators.py`, `load_duckdb.py`, `export_powerbi.py`).
  - `venv/`: **CRITICAL**. The Python virtual environment containing `duckdb` and `dbt-duckdb`.
- **`dbt_project/`**: The dbt project.
  - `models/`: Staging, Intermediate, and Mart models.
  - `snapshots/`: SCD2 snapshots (`snap_product`).
  - `profiles.yml`: Configured to look for `../data/vantage.duckdb`.
- **`data/`**: Storage for the DuckDB database and exports.
  - `vantage.duckdb`: The main database file.
  - `export/`: Output directory for Power BI (Parquet/CSV/Zip).

## 2. Execution Environment (CRITICAL)
**ALWAYS use the virtual environment in `data_generation/venv`**.
Do not use the system python or global dbt unless explicitly instructed. This ensures the correct `dbt-duckdb` adapter version is used.

### Command Patterns
#### Running Data Generation
```bash
cd data_generation/src
../venv/bin/python main.py
../venv/bin/python load_duckdb.py
```

#### Running dbt
```bash
cd dbt_project
../data_generation/venv/bin/dbt build
```

#### Running Exports
```bash
cd data_generation/src
../venv/bin/python export_powerbi.py
```

## 3. Common Pitfalls & Fixes
- **"DuckDB File Not Found"**: The database is located at `data/vantage.duckdb`.
  - From `data_generation/src/`, the relative path is `../../data/vantage.duckdb`.
  - From `dbt_project/`, the relative path is `../data/vantage.duckdb`.
- **SCD2 Logic**: 
  - The `snap_product` table is bootstrapped by Python (history 2024-2025) and loaded into the `snapshots` schema.
  - `dbt snapshot` picks up from there.
  - Validation checks must account for the "bootstrap" -> "live dbt" transition.
- **`fct_orders` vs `fct_transactions`**:
  - **`fct_orders`**: Strategic view. Uses *historical* Price Tier at moment of purchase. Uses *fixed* strategic marketing costs (€3/7/12).
  - **`fct_transactions`**: Financial view. Uses *actual* allocated costs (based on daily spend/revenue ratio) and current attribution.
- **Date Columns**:
  - `ship_date`: `order_date` + 1-5 days.
  - `return_date`: `ship_date` + 7-30 days (only if returned).
