-- Q4b. How concentrated is revenue among sellers?
-- Sellers ranked by revenue and split into 10 equal-sized groups (deciles).
WITH s AS (
    SELECT i.seller_id, SUM(i.price) AS gmv
    FROM order_items i JOIN revenue_orders o USING (order_id)
    GROUP BY i.seller_id
),
ranked AS (
    SELECT *, NTILE(10) OVER (ORDER BY gmv DESC) AS seller_decile FROM s
)
SELECT
    seller_decile,
    COUNT(*)                                                         AS sellers,
    ROUND(SUM(gmv), 2)                                               AS gmv,
    ROUND(100.0 * SUM(gmv) / SUM(SUM(gmv)) OVER (), 2)               AS gmv_share_pct,
    ROUND(100.0 * SUM(SUM(gmv)) OVER (ORDER BY seller_decile) / SUM(SUM(gmv)) OVER (), 2) AS cumulative_share_pct
FROM ranked
GROUP BY seller_decile
ORDER BY seller_decile;
