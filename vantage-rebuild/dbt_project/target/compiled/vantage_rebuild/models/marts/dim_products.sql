with products as (
    select * from "vantage"."main"."stg_products"
)

select
    sku_id,
    product_name,
    category,
    -- Simple tiers based on price/category
    case 
        when category = 'Ausrüstung' then 'Hardware'
        when category = 'Schuhe' then 'Footwear'
        else 'Apparel'
    end as business_unit,
    list_price_eur
from products