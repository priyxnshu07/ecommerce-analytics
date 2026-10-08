-- Q3a. Do customers come back?
-- Counted per real person (customer_unique_id), revenue orders only.
WITH numbered AS (
    SELECT customer_unique_id, purchase_ts, gmv,
           ROW_NUMBER() OVER (PARTITION BY customer_unique_id ORDER BY purchase_ts) AS n
    FROM revenue_orders
),
per_customer AS (
    SELECT customer_unique_id,
           COUNT(*)                                   AS orders,
           SUM(gmv)                                   AS gmv,
           MIN(purchase_ts)                           AS first_ts,
           MIN(purchase_ts) FILTER (WHERE n = 2)      AS second_ts
    FROM numbered GROUP BY customer_unique_id
)
SELECT
    COUNT(*)                                                         AS customers,
    COUNT(*) FILTER (WHERE orders > 1)                               AS repeat_customers,
    ROUND(100.0 * COUNT(*) FILTER (WHERE orders > 1) / COUNT(*), 2)  AS repeat_rate_pct,
    ROUND(100.0 * SUM(gmv) FILTER (WHERE orders > 1) / SUM(gmv), 2)  AS repeat_customers_gmv_share_pct,
    MEDIAN(DATE_DIFF('day', first_ts, second_ts))                    AS median_days_to_second_order
FROM per_customer;
