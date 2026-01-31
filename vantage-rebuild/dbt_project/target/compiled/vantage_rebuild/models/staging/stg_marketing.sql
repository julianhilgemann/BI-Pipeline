with source as (
    select * from "vantage"."main"."raw_marketing_daily"
),

renamed as (
    select
        cast(date as date) as date_day,
        shop_id,
        spend_amount as marketing_spend_local,
        currency as currency_code
    from source
)

select * from renamed