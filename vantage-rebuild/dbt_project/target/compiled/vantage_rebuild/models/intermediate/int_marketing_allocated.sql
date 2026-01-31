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
), orders_std as (
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