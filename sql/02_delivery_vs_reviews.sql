-- Q2. Do late deliveries hurt customer reviews, and by how much?
-- delay_days = actual delivery date minus the date promised at checkout
-- (negative = early). Buckets run from very early to very late.
WITH delivered AS (
    SELECT
        CASE
            WHEN delay_days <= -8 THEN '1. 8+ days early'
            WHEN delay_days <= -1 THEN '2. 1-7 days early'
            WHEN delay_days = 0   THEN '3. on the promised day'
            WHEN delay_days <= 3  THEN '4. 1-3 days late'
            WHEN delay_days <= 7  THEN '5. 4-7 days late'
            WHEN delay_days <= 14 THEN '6. 8-14 days late'
            ELSE                       '7. 15+ days late'
        END AS delivery_bucket,
        is_late,
        review_score
    FROM orders
    WHERE in_window AND has_delivery AND review_score IS NOT NULL
)
SELECT
    delivery_bucket,
    is_late,
    COUNT(*)                                                    AS orders,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)          AS pct_of_orders,
    ROUND(AVG(review_score), 2)                                 AS avg_review,
    ROUND(100.0 * AVG(CASE WHEN review_score <= 2 THEN 1 ELSE 0 END), 1) AS pct_1_or_2_stars
FROM delivered
GROUP BY delivery_bucket, is_late
ORDER BY delivery_bucket;
