
with orders as (
    select * from {{ ref('stg_orders') }}
),

line_items as (
    select * from {{ ref('stg_line_items') }}
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
