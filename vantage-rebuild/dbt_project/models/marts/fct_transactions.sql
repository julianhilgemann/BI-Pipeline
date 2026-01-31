
with orders_allocated as (
    select * from {{ ref('int_marketing_allocated') }}
),

logistics as (
    select * from {{ ref('int_logistics_costs') }}
),

final as (
    select
        -- Keys
        oa.order_id,
        oa.line_item_id,
        
        -- Dimensions
        cast(oa.order_date as date) as date_key,
        oa.shop_id as shop_key,
        oa.customer_id as customer_key,
        oa.sku_id as product_key,
        
        -- Metrics
        oa.quantity,
        oa.gross_revenue_eur,
        
        -- Costs
        -- COGS
        oa.gross_revenue_eur * (oa.unit_cost_local / oa.unit_price_local) as cogs_eur, 
        -- (Doing Ratio calc to be safe on currency, or just use unit_cost_eur column if I had it exposed... 
        -- Wait, int_orders_standardized calculates cogs_eur. 
        -- But int_marketing_allocated only selects a few cols! 
        -- I should update int_marketing_allocated to select * or join back.)
        
        -- Let's assume standard joins back to `int_orders_standardized` for cleanliness, 
        -- OR update `int_marketing_allocated` to pass through everything.
        -- Looking at `int_marketing_allocated.sql`, it selects specific cols. 
        -- I will join back to `int_orders_standardized` here.
        
        orders_std.cogs_eur,
        
        -- Logistics (Allocated by Item Count weighting)
        -- Logic: Total Order Logistics Cost / Total Items in Order
        (l.logistics_cost_eur / l.item_count) as logistics_allocated_eur,
        
        -- Marketing (Already allocated)
        oa.marketing_cost_allocated_eur,
        
        -- Margin
        oa.gross_revenue_eur 
            - orders_std.cogs_eur 
            - (l.logistics_cost_eur / l.item_count)
            - oa.marketing_cost_allocated_eur 
        as contribution_margin_eur,
        
        orders_std.is_returned

    from orders_allocated oa
    
    -- Join back to Standardized for COGS/Attributes
    left join {{ ref('int_orders_standardized') }} orders_std 
        using (line_item_id)
        
    -- Join Logistics
    left join logistics l 
        on oa.order_id = l.order_id
)

select * from final
