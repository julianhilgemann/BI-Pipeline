with source as (
    select * from "vantage"."main"."raw_budget"
),

renamed as (
    select
        cast(month as date) as budget_month,
        shop_id,
        currency as currency_code,
        budget_revenue,
        -- Generate MD5 key for unique identification if needed in future, though (month, shop) is unique
        concat(shop_id, '-', cast(month as varchar)) as budget_id
    from source
)

select * from renamed