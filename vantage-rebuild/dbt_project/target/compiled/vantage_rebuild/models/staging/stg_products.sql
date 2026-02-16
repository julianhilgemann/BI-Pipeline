with source as (
    select * from "vantage"."main"."raw_products"
),

renamed as (
    select
        sku_id as product_id,
        product_name,
        category,
        NULL as subcategory,
        price_tier,
        avg_price_eur as base_retail_price,
        unit_cost_eur,
        popularity_score
    from source
)

select * from renamed