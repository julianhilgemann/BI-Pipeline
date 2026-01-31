
with orders as (
    select * from {{ ref('stg_orders') }}
),

line_items as (
    select * from {{ ref('stg_line_items') }}
),

rates as (
    select * from {{ ref('int_exchange_rates') }}
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
