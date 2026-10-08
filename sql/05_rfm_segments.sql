-- Q5. Which customer segments matter most? RFM segmentation.
-- Recency = days since last order (as of 2018-09-01, end of the window),
-- Frequency = number of orders, Monetary = total GMV.
-- R and M are scored 1-5 by quintile. F is scored by order count, because
-- ~97% of customers ordered once, so F quintiles would be meaningless.
WITH c AS (
    SELECT customer_unique_id,
           DATE_DIFF('day', MAX(purchase_ts)::DATE, DATE '2018-09-01') AS recency_days,
           COUNT(*)                                                    AS frequency,
           SUM(gmv)                                                    AS monetary
    FROM revenue_orders GROUP BY customer_unique_id
),
scored AS (
    SELECT *,
           NTILE(5) OVER (ORDER BY recency_days DESC)               AS r,
           CASE WHEN frequency >= 3 THEN 3 WHEN frequency = 2 THEN 2 ELSE 1 END AS f,
           NTILE(5) OVER (ORDER BY monetary)                         AS m
    FROM c
),
segmented AS (
    SELECT *,
        CASE
            WHEN f >= 2 AND r >= 4             THEN 'Champions'
            WHEN f >= 2                        THEN 'Loyal, lapsing'
            WHEN r >= 4 AND m >= 4             THEN 'New big spenders'
            WHEN r >= 4                        THEN 'New customers'
            WHEN r <= 2 AND m >= 4             THEN 'Lost big spenders'
            WHEN r <= 2                        THEN 'Lost'
            ELSE                                    'Needs attention'
        END AS segment
    FROM scored
)
SELECT
    segment,
    COUNT(*)                                                  AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)        AS pct_customers,
    ROUND(SUM(monetary), 2)                                   AS gmv,
    ROUND(100.0 * SUM(monetary) / SUM(SUM(monetary)) OVER (), 1) AS pct_gmv,
    ROUND(AVG(recency_days))                                  AS avg_recency_days,
    ROUND(AVG(monetary), 2)                                   AS avg_spend
FROM segmented
GROUP BY segment
ORDER BY gmv DESC;
