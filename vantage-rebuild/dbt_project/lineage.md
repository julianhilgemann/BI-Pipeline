```mermaid
flowchart LR
    model_vantage_rebuild_stg_products["stg_products"]
    model_vantage_rebuild_stg_line_items["stg_line_items"]
    model_vantage_rebuild_stg_marketing["stg_marketing"]
    model_vantage_rebuild_stg_orders["stg_orders"]
    model_vantage_rebuild_stg_budget["stg_budget"]
    model_vantage_rebuild_dim_calendar["dim_calendar"]
    model_vantage_rebuild_dim_products["dim_products"]
    model_vantage_rebuild_dim_product_history["dim_product_history"]
    model_vantage_rebuild_fct_orders["fct_orders"]
    model_vantage_rebuild_dim_product_current["dim_product_current"]
    model_vantage_rebuild_fct_budget_daily["fct_budget_daily"]
    model_vantage_rebuild_fct_transactions["fct_transactions"]
    model_vantage_rebuild_int_logistics_costs["int_logistics_costs"]
    model_vantage_rebuild_int_exchange_rates["int_exchange_rates"]
    model_vantage_rebuild_int_orders_standardized["int_orders_standardized"]
    model_vantage_rebuild_int_marketing_allocated["int_marketing_allocated"]
    snapshot_vantage_rebuild_snap_product["snap_product"]
    seed_vantage_rebuild_exchange_rates["exchange_rates"]
    source_vantage_rebuild_vantage_source_raw_orders["vantage_source.raw_orders"]
    source_vantage_rebuild_vantage_source_raw_line_items["vantage_source.raw_line_items"]
    source_vantage_rebuild_vantage_source_raw_products["vantage_source.raw_products"]
    source_vantage_rebuild_vantage_source_raw_marketing_daily["vantage_source.raw_marketing_daily"]
    source_vantage_rebuild_vantage_source_raw_budget["vantage_source.raw_budget"]
    source_vantage_rebuild_vantage_source_raw_products --> model_vantage_rebuild_stg_products
    source_vantage_rebuild_vantage_source_raw_line_items --> model_vantage_rebuild_stg_line_items
    source_vantage_rebuild_vantage_source_raw_marketing_daily --> model_vantage_rebuild_stg_marketing
    source_vantage_rebuild_vantage_source_raw_orders --> model_vantage_rebuild_stg_orders
    source_vantage_rebuild_vantage_source_raw_budget --> model_vantage_rebuild_stg_budget
    model_vantage_rebuild_stg_products --> model_vantage_rebuild_dim_products
    snapshot_vantage_rebuild_snap_product --> model_vantage_rebuild_dim_product_history
    model_vantage_rebuild_stg_orders --> model_vantage_rebuild_fct_orders
    model_vantage_rebuild_stg_line_items --> model_vantage_rebuild_fct_orders
    snapshot_vantage_rebuild_snap_product --> model_vantage_rebuild_fct_orders
    snapshot_vantage_rebuild_snap_product --> model_vantage_rebuild_dim_product_current
    model_vantage_rebuild_stg_budget --> model_vantage_rebuild_fct_budget_daily
    model_vantage_rebuild_int_marketing_allocated --> model_vantage_rebuild_fct_transactions
    model_vantage_rebuild_int_logistics_costs --> model_vantage_rebuild_fct_transactions
    model_vantage_rebuild_int_orders_standardized --> model_vantage_rebuild_fct_transactions
    model_vantage_rebuild_stg_orders --> model_vantage_rebuild_int_logistics_costs
    model_vantage_rebuild_stg_line_items --> model_vantage_rebuild_int_logistics_costs
    seed_vantage_rebuild_exchange_rates --> model_vantage_rebuild_int_exchange_rates
    model_vantage_rebuild_stg_orders --> model_vantage_rebuild_int_orders_standardized
    model_vantage_rebuild_stg_line_items --> model_vantage_rebuild_int_orders_standardized
    model_vantage_rebuild_int_exchange_rates --> model_vantage_rebuild_int_orders_standardized
    model_vantage_rebuild_int_orders_standardized --> model_vantage_rebuild_int_marketing_allocated
    model_vantage_rebuild_stg_marketing --> model_vantage_rebuild_int_marketing_allocated
    model_vantage_rebuild_stg_products --> snapshot_vantage_rebuild_snap_product
```
