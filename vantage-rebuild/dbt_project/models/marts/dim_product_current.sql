
SELECT
    product_id,
    product_name,
    category,
    subcategory,
    price_tier,
    base_retail_price
FROM {{ ref('snap_product') }}
WHERE dbt_valid_to IS NULL
