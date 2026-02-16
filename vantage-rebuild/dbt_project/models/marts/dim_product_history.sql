
SELECT
    product_id,
    product_name,
    category,
    price_tier,
    base_retail_price,
    dbt_valid_from AS valid_from,
    COALESCE(dbt_valid_to, '9999-12-31'::date) AS valid_to,
    CASE WHEN dbt_valid_to IS NULL THEN TRUE ELSE FALSE END AS is_current
FROM {{ ref('snap_product') }}
ORDER BY product_id, dbt_valid_from
