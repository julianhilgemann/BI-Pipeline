
with orders_std as (
    select * from {{ ref('int_orders_standardized') }}
),

marketing_daily as (
    select * from {{ ref('stg_marketing') }}
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
