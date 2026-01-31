
-- KPI Validation Query (The Golden Record)
-- Run this in DuckDB to check numbers against Power BI

select
    extract(year from date_key) as year,
    extract(month from date_key) as month,
    shop_key,
    
    count(distinct order_id) as total_orders,
    sum(gross_revenue_eur) as gross_revenue,
    sum(marketing_cost_allocated_eur) as marketing_spend,
    sum(contribution_margin_eur) as contribution_margin,
    
    -- Check Returns
    sum(case when is_returned then gross_revenue_eur else 0 end) as returned_revenue

from fct_transactions
group by 1, 2, 3
order by 1, 2, 3
