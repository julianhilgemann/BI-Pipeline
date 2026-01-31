with recursive date_series as (
    select cast('2024-01-01' as date) as date_day
    union all
    select date_day + interval 1 day
    from date_series
    where date_day < '2024-12-31'
),

final as (
    select
        date_day as date_key,
        extract(year from date_day) as year,
        extract(month from date_day) as month_num,
        monthname(date_day) as month_name,
        week(date_day) as iso_week,
        dayofweek(date_day) as day_of_week_num, -- 0=Sun in some DBs, DuckDB: 0=Sun? No, DuckDB ISODOW is 1=Mon. dayofweek 0=Sun.
        case when dayofweek(date_day) in (0, 6) then true else false end as is_weekend
    from date_series
)

select * from final