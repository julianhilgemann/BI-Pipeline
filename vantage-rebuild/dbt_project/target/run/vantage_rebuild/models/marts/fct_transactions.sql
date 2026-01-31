
  
    
    

    create  table
      "vantage"."main"."fct_transactions__dbt_tmp"
  
    as (
      with  __dbt__cte__int_exchange_rates as (
with rate_source as (
    select * from "vantage"."main"."exchange_rates"
),

final as (
    select
        date_day,
        from_currency,
        to_currency,
        rate
    from rate_source
    -- We assume only 'to_currency' = EUR matters for now
    where to_currency = 'EUR'
)

select * from final
),  __dbt__cte__int_orders_standardized as (
with orders as (
    select * from "vantage"."main"."stg_orders"
),

line_items as (
    select * from "vantage"."main"."stg_line_items"
),

rates as (
    select * from __dbt__cte__int_exchange_rates
),

-- Join all together
joined as (
    select
        l.line_item_id,
        l.order_id,
        o.shop_id,
        o.customer_id,
        o.order_date,
        o.currency_code,
        l.sku_id,
        l.quantity,
        l.unit_price_local,
        l.unit_cost_local,
        l.is_returned,
        
        -- Exchange Rate Lookup
        -- If currency is EUR, rate is 1.0. If not, join to rates.
        coalesce(r.rate, 1.0) as exchange_rate

    from line_items l
    left join orders o on l.order_id = o.order_id
    left join rates r 
        on o.order_date = r.date_day 
        and o.currency_code = r.from_currency
        and r.to_currency = 'EUR'
),

calculated as (
    select
        *,
        -- Monetary conversions
        unit_price_local * exchange_rate as unit_price_eur,
        unit_cost_local * exchange_rate as unit_cost_eur,
        
        -- Line Totals
        (unit_price_local * exchange_rate) * quantity as gross_revenue_eur,
        (unit_cost_local * exchange_rate) * quantity as cogs_eur
        
    from joined
)

select * from calculated
),  __dbt__cte__int_marketing_allocated as (
with orders_std as (
    select * from __dbt__cte__int_orders_standardized
),

marketing_daily as (
    select * from "vantage"."main"."stg_marketing"
),

-- 1. Daily Sales Summary (Dominator for allocation)
daily_sales as (
    select
        order_date,
        shop_id,
        sum(gross_revenue_eur) as total_daily_revenue_eur
    from orders_std
    group by 1, 2
),

-- 2. Daily Spend (Numerator)
daily_spend as (
    select
        date_day,
        shop_id,
        -- Assume marketing spend in stg is already standardized or matches shop currency
        -- If shop_id=CH, marketing is likely in CHF. We should convert it to EUR too if generating strictly in EUR.
        -- Usage: For simplicity, let's assume raw_marketing_daily is in EUR or close enough for this MVP 
        -- (Since shop_id=CH has base currency CHF, but marketing might be global). 
        -- Actually, generator output has 'currency' col.
        marketing_spend_local
    from marketing_daily
),

-- 3. Allocation Factor
allocation_factors as (
    select
        ds.order_date,
        ds.shop_id,
        ds.total_daily_revenue_eur,
        msp.marketing_spend_local as daily_marketing_spend,
        -- Avoid divide by zero
        case 
            when ds.total_daily_revenue_eur > 0 
            then msp.marketing_spend_local / ds.total_daily_revenue_eur 
            else 0 
        end as cost_per_eur_revenue
    from daily_sales ds
    inner join daily_spend msp 
        on ds.order_date = msp.date_day 
        and ds.shop_id = msp.shop_id
),

-- 4. Apply to Lines
final_allocation as (
    select
        ord.line_item_id,
        ord.order_id,
        ord.order_date,
        ord.shop_id,
        ord.customer_id,
        ord.sku_id,
        ord.quantity,
        ord.unit_price_local,
        ord.unit_cost_local,
        ord.gross_revenue_eur,
        af.cost_per_eur_revenue,
        
        -- Allocated Cost
        ord.gross_revenue_eur * af.cost_per_eur_revenue as marketing_cost_allocated_eur
        
    from orders_std ord
    left join allocation_factors af 
        on ord.order_date = af.order_date 
        and ord.shop_id = af.shop_id
)

select * from final_allocation
),  __dbt__cte__int_logistics_costs as (
with orders as (
    select * from "vantage"."main"."stg_orders"
),

line_items as (
    select * from "vantage"."main"."stg_line_items"
),

-- Aggregate items per order
order_stats as (
    select
        order_id,
        count(*) as item_count
    from line_items
    group by 1
),

joined as (
    select
        o.order_id,
        o.shop_id,
        s.item_count
    from orders o
    left join order_stats s on o.order_id = s.order_id
),

-- Rule Engine for Logistics
calculated as (
    select
        order_id,
        shop_id,
        item_count,
        -- Rule: Base 3.50 EUR (8.50 CH) + 0.50 per item
        case
            when shop_id = 'CH' then 8.50 + (item_count * 0.50)
            else 3.50 + (item_count * 0.50)
        end as logistics_cost_eur
    from joined
)

select * from calculated
), orders_allocated as (
    select * from __dbt__cte__int_marketing_allocated
),

logistics as (
    select * from __dbt__cte__int_logistics_costs
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
    left join __dbt__cte__int_orders_standardized orders_std 
        using (line_item_id)
        
    -- Join Logistics
    left join logistics l 
        on oa.order_id = l.order_id
)

select * from final
    );
  
  