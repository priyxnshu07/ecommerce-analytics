-- Q2b. Where are deliveries late? Late rate and delivery time by customer
-- state (states with at least 1,000 delivered orders, worst first).
SELECT
    customer_state,
    COUNT(*)                                                   AS delivered_orders,
    ROUND(100 * AVG(CASE WHEN is_late THEN 1.0 ELSE 0 END), 1) AS late_rate_pct,
    ROUND(AVG(delivery_days), 1)                               AS avg_delivery_days,
    ROUND(AVG(DATE_DIFF('day', purchase_ts::DATE, estimated_date)), 1) AS avg_promised_days
FROM orders
WHERE in_window AND has_delivery
GROUP BY customer_state
HAVING COUNT(*) >= 1000
ORDER BY late_rate_pct DESC;
