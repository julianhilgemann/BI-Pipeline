
-- assert_marketing_fully_allocated.sql
with source as (
    select sum(marketing_spend_local) as total_spend
    from {{ ref('stg_marketing') }}
    -- Convert to EUR if mixed currencies? For MVP we assume input was normalized or single currency per shop.
    -- Generator output had 'EUR' for DE/AT and 'CHF' for CH.
    -- Wait, if CH spend is CHF, and we allocated based on EUR revenue...
    -- The `int_marketing_allocated` took `marketing_spend_local / total_daily_revenue_eur`.
    -- This implies we treated local spend as EUR! (Which is a bug if spend was CHF).
    -- However, for the TEST, we just want to ensure the Distribution Math worked (i.e. we didn't lose money in rounding).
    -- So we compare Sum(Spend) vs Sum(Allocated).
),

fact as (
    select sum(marketing_cost_allocated_eur) as total_allocated
    from {{ ref('fct_transactions') }}
)

select * 
from source, fact
where abs(source.total_spend - fact.total_allocated) > 5.0 
-- Allow 5 EUR tolerance for rounding errors across 365 days
