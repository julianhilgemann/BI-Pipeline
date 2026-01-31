with budget as (
    select * from "vantage"."main"."stg_budget"
),

-- Generate Daily Budget (Linear Split)
-- We need a date spine, but for MVP we can fan out by joining to a calendar or just dividing by 30
-- Ideally use dbt_utils.date_spine.
-- Hack for MVP: Just keep it Monthly? No, spec says Daily.
-- We will assume 30 days per month for simplicity here to avoid massive join complexity without a calendar source.
-- BETTER: Use recursive CTE to generate days.

dates as (
    -- Recursively generate days for 2024
    with recursive date_series as (
        select cast('2024-01-01' as date) as date_day
        union all
        select date_day + interval 1 day
        from date_series
        where date_day < '2024-12-31'
    )
    select * from date_series
),

final as (
    select
        d.date_day,
        b.shop_id,
        b.currency_code,
        -- Simple allocation: Monthly Budget / Days in Month
        b.budget_revenue / extract(day from last_day(d.date_day)) as daily_budget_revenue
    from budget b
    inner join dates d 
        on extract(month from d.date_day) = extract(month from b.budget_month)
        and extract(year from d.date_day) = extract(year from b.budget_month)
)

select * from final