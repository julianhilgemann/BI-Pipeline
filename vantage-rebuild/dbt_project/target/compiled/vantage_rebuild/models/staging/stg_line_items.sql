with source as (
    select * from "vantage"."main"."raw_line_items"
),

renamed as (
    select
        line_id as line_item_id,
        order_id,
        sku_id,
        qty as quantity,
        unit_price_paid as unit_price_local,
        unit_cost as unit_cost_local,
        is_returned
    from source
)

select * from renamed