with source as (
    select * from "vantage"."main"."raw_products"
),

renamed as (
    select
        sku_id,
        category,
        product_name,
        avg_price_eur as list_price_eur,
        unit_cost_eur,
        popularity_score
    from source
)

select * from renamed