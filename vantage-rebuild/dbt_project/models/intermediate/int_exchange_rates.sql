
with rate_source as (
    select * from {{ ref('exchange_rates') }}
),

final as (
    select
        date_day,
        from_currency,
        to_currency,
        rate
    from rate_source
    -- We assume only 'to_currency' = EUR matters for now
    where to_currency = 'EUR'
)

select * from final
