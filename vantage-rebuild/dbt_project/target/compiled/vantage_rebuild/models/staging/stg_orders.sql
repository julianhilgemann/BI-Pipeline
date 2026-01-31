with source as (
    select * from "vantage"."main"."raw_orders"
),

renamed as (
    select
        order_id,
        customer_id,
        shop_id,
        -- Correct datatypes
        cast(order_date as date) as order_date,
        currency_code
    from source
)

select * from renamed