# Insights memo: Olist marketplace, Jan 2017 – Aug 2018

**To:** Head of Operations & Head of Growth · **From:** Priyanshu Parashar · **Data:** 97,905 revenue orders, R$13.45M GMV

## Summary

The marketplace grew fast (**+138%** revenue, Jan–Aug 2018 vs the same months of 2017), but two problems cap its value. **Late deliveries are the main driver of bad reviews**, and **almost no customer buys twice**. Fixing delivery in three states and building a basic retention programme are the highest-value next steps.

## Findings

### 1. Late deliveries cause a third of all bad reviews

- Late orders average **2.26 stars** vs **4.28** for on-time orders.
- **63%** of late orders get 1–2 stars, vs **9.5%** of on-time orders.
- Late orders are only **6.8%** of deliveries but **32.5%** of all 1–2-star reviews.
- The damage starts immediately: even **1–3 days late** drops the average to 3.28 stars.

**What-if:** if late orders were reviewed like on-time ones, 1–2-star reviews would fall from **12,645 to about 9,161 (−28%)** and the average rating would rise from **4.14 to 4.28**.

### 2. Lateness is regional and seasonal, not random

| State | Delivered orders | Late rate | Avg delivery (days) |
| --- | --- | --- | --- |
| CE | 1,273 | **13.8%** | 21.2 |
| BA | 3,253 | **12.2%** | 19.3 |
| RJ | 12,310 | **12.1%** | 15.3 |
| SP (benchmark) | 40,399 | 4.5% | 8.7 |

- **Rio de Janeiro is the biggest single opportunity:** the 2nd-largest market, with nearly 3× São Paulo's late rate.
- The late rate spiked to **19.0% in Mar 2018**, 14.1% in Feb 2018 and 12.4% in Nov 2017 (Black Friday), against a 6.8% average. Capacity didn't keep up with demand peaks.
- Delivery promises are heavily padded: orders arrive in **12.5 days on average against a promised 24.3**. Lateness comes from a minority of orders and routes, not a slow network.

### 3. Customers almost never come back

- Only **3.0%** of 94,703 customers ordered more than once; repeat customers bring just **5.6%** of revenue.
- Those who do return take a median of **28 days** to place a second order.
- RFM segmentation: **"Lost big spenders"** (high spend, no order in about a year) are **14.7%** of customers but **28.8%** of revenue.

### 4. Revenue is concentrated in a few sellers and categories

- The **top 10% of sellers generate 67%** of revenue; the top 20% generate 82.5%.
- **7 of 74 categories** (led by health & beauty, watches & gifts, bed & bath) make up about **50%** of revenue.
- São Paulo customers account for **38.3%** of revenue.

## Recommendations

| # | Recommendation | Owner | Evidence | How to measure |
| --- | --- | --- | --- | --- |
| 1 | **Fix delivery in RJ, BA and CE first:** review carrier performance and seller dispatch times on those routes | Operations | Findings 1–2 | Late rate in each state, monthly; target the SP benchmark (~5%) |
| 2 | **Pre-book carrier capacity before demand peaks** (Black Friday, Q1) | Operations | Late rate 12–19% in peak months | Peak-month late rate vs non-peak |
| 3 | **Make promise dates route-specific** instead of uniformly padded, and alert customers proactively when an order will miss its date | Product | 12.5 actual vs 24.3 promised days | Share of late orders; 1–2-star share on late orders |
| 4 | **Start a post-delivery re-engagement flow** around day 20–30 (e.g. a personalised offer) | Growth / CRM | 3.0% repeat rate; 28-day median to 2nd order | Repeat-purchase rate per monthly cohort |
| 5 | **Win back "lost big spenders"** with a targeted campaign | Growth / CRM | 14.7% of customers, 28.8% of revenue | Reactivation rate; revenue from the segment |
| 6 | **Key-account management for the top 10% of sellers** to protect and grow the core of GMV | Seller success | Top decile = 67% of revenue | Top-seller churn; GMV per top seller |

## Limitations

- **Correlation, not proven causation.** Late delivery and low reviews move together strongly, but other factors (product type, seller) may contribute. An A/B test on proactive delay alerts would measure the effect directly.
- **Customer identity** relies on Olist's `customer_unique_id`; a person using two accounts counts as two customers, so the true repeat rate may be slightly higher.
- **The what-if** assumes late orders would earn the same scores as on-time ones once fixed. It's an upper bound, not a forecast.
- **Data ends in Aug 2018**; the patterns, not the absolute numbers, are the takeaway.

*Every figure comes from the SQL in [`sql/`](../sql) and the results in [`reports/results/`](results).*
