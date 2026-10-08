-- Q2c. How much do late deliveries cost in reviews?
-- share_of_low_reviews_from_late_pct: of all 1-2 star reviews, how many are late orders.
-- what-if columns: if late orders were reviewed like on-time orders (an upper bound).
WITH d AS (
    SELECT is_late, review_score
    FROM orders
    WHERE in_window AND has_delivery AND review_score IS NOT NULL
),
on_time AS (
    SELECT AVG(review_score) AS avg_review,
           AVG(CASE WHEN review_score <= 2 THEN 1.0 ELSE 0 END) AS low_share
    FROM d WHERE NOT is_late
)
SELECT
    ROUND(100.0 * AVG(CASE WHEN is_late THEN 1.0 ELSE 0 END), 1)                                  AS late_share_of_orders_pct,
    ROUND(100.0 * COUNT(*) FILTER (WHERE is_late AND review_score <= 2)
                / COUNT(*) FILTER (WHERE review_score <= 2), 1)                                    AS share_of_low_reviews_from_late_pct,
    COUNT(*) FILTER (WHERE review_score <= 2)                                                      AS low_reviews_now,
    ROUND(COUNT(*) FILTER (WHERE review_score <= 2 AND NOT is_late)
          + (SELECT low_share FROM on_time) * COUNT(*) FILTER (WHERE is_late))                     AS low_reviews_if_on_time,
    ROUND(AVG(review_score), 2)                                                                    AS avg_review_now,
    ROUND((SELECT avg_review FROM on_time), 2)                                                     AS avg_review_if_on_time
FROM d;
