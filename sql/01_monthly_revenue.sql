-- Q1. How are orders and revenue trending month by month?
-- GMV = gross merchandise value (item prices, excluding freight).
-- Growth is month-over-month; Nov 2017 (Black Friday) is the stand-out spike.
SELECT
    purchase_month,
    COUNT(*)                                   AS orders,
    COUNT(DISTINCT customer_unique_id)         AS customers,
    ROUND(SUM(gmv), 2)                         AS gmv,
    ROUND(AVG(gmv), 2)                         AS avg_order_value,
    ROUND(100.0 * (SUM(gmv) / LAG(SUM(gmv)) OVER (ORDER BY purchase_month) - 1), 1) AS gmv_mom_growth_pct
FROM revenue_orders
GROUP BY purchase_month
ORDER BY purchase_month;
