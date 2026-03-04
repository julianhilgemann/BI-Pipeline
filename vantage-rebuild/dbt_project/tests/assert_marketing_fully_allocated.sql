
-- assert_marketing_fully_allocated.sql
with source as (
    select sum(marketing_spend_local) as total_spend
    from {{ ref('stg_marketing') }}
    -- This test verifies the distribution math by ensuring that the sum of local spend matches the sum of allocated cost.
    -- It checks that no spend is lost or duplicated due to rounding errors during the allocation process.
),

fact as (
    select sum(marketing_cost_allocated_eur) as total_allocated
    from {{ ref('fct_transactions') }}
)

select * 
from source, fact
where abs(source.total_spend - fact.total_allocated) > 5.0 
-- Allow 5 EUR tolerance for rounding errors across 365 days
