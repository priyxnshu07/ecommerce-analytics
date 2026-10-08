-- Q4a. Which product categories drive revenue? (Pareto / 80-20 view)
WITH cat AS (
    SELECT i.category,
           SUM(i.price)                   AS gmv,
           COUNT(DISTINCT i.order_id)     AS orders,
           AVG(o.review_score)            AS avg_review,
           AVG(CASE WHEN o.is_late THEN 1.0 ELSE 0 END) AS late_rate
    FROM order_items i
    JOIN revenue_orders o USING (order_id)
    GROUP BY i.category
)
SELECT
    category,
    ROUND(gmv, 2)                                                         AS gmv,
    orders,
    ROUND(100.0 * gmv / SUM(gmv) OVER (), 2)                              AS gmv_share_pct,
    ROUND(100.0 * SUM(gmv) OVER (ORDER BY gmv DESC) / SUM(gmv) OVER (), 2) AS cumulative_share_pct,
    ROUND(avg_review, 2)                                                  AS avg_review,
    ROUND(100.0 * late_rate, 1)                                           AS late_rate_pct
FROM cat
ORDER BY gmv DESC;
