{% snapshot snap_product %}
{{
    config(
        target_schema='snapshots',
        unique_key='product_id',
        strategy='check',
        check_cols=['price_tier', 'base_retail_price']
    )
}}

SELECT
    product_id,
    product_name,
    category,
    subcategory,
    price_tier,
    base_retail_price
FROM {{ ref('stg_products') }}

{% endsnapshot %}
