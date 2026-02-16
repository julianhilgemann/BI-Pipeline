SELECT
    o.order_id,
    o.order_date,
    o.customer_id,        -- if exists
    li.sku_id as product_id,
    li.quantity as quantity,
    li.unit_price_local as unit_price,
    0 as discount, -- Placeholder or derived
    (li.quantity * li.unit_price_local) as gross_revenue,
    (li.quantity * li.unit_price_local) as net_revenue, -- Assuming no tax/shipping for now
    p.product_name,
    p.category,
    p.subcategory,
    p.price_tier,          -- FROM SCD2 SNAPSHOT, not current state
    p.base_retail_price,   -- FROM SCD2 SNAPSHOT, not current state
    -- Marketing cost derived from tier at time of order
    CASE p.price_tier
        WHEN 'budget'  THEN 3.0
        WHEN 'mid'     THEN 7.0
        WHEN 'premium' THEN 12.0
    END AS marketing_cost_per_order
FROM {{ ref('stg_orders') }} o
JOIN {{ ref('stg_line_items') }} li ON o.order_id = li.order_id
LEFT JOIN {{ ref('snap_product') }} p
    ON li.sku_id = p.product_id
    AND o.order_date >= p.dbt_valid_from
    AND o.order_date < COALESCE(p.dbt_valid_to, '9999-12-31'::date)
