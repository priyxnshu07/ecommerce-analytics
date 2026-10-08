-- Q3b. Monthly cohort retention: of customers whose first order was in
-- month M, what share ordered again k months later?
WITH firsts AS (
    SELECT customer_unique_id, MIN(purchase_month) AS cohort_month
    FROM revenue_orders GROUP BY customer_unique_id
),
activity AS (
    SELECT DISTINCT r.customer_unique_id, f.cohort_month,
           DATE_DIFF('month', f.cohort_month, r.purchase_month) AS months_since_first
    FROM revenue_orders r JOIN firsts f USING (customer_unique_id)
),
cohort_size AS (
    SELECT cohort_month, COUNT(*) AS customers FROM firsts GROUP BY cohort_month
)
SELECT
    a.cohort_month,
    s.customers                                             AS cohort_customers,
    a.months_since_first,
    COUNT(*)                                                AS active_customers,
    ROUND(100.0 * COUNT(*) / s.customers, 2)                AS retention_pct
FROM activity a JOIN cohort_size s USING (cohort_month)
GROUP BY a.cohort_month, s.customers, a.months_since_first
ORDER BY a.cohort_month, a.months_since_first;
