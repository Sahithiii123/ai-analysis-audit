CREATE OR REPLACE TEMP VIEW review_per_order AS
SELECT order_id,
       AVG(TRY_CAST(review_score AS DOUBLE)) AS review_score,
       COUNT(*) AS review_count
FROM fact_reviews
GROUP BY order_id;

CREATE OR REPLACE TEMP VIEW reviewed_delivered_orders AS
SELECT orders.order_id,
       orders.customer_id,
       orders.purchased_at,
       orders.delivered_at,
       orders.estimated_at,
       orders.is_late,
       orders.days_late,
       reviews.review_score,
       reviews.review_count,
       customers.customer_state
FROM fact_orders AS orders
JOIN review_per_order AS reviews USING (order_id)
JOIN dim_customers AS customers USING (customer_id)
WHERE orders.delivered_at IS NOT NULL;

CREATE OR REPLACE TEMP VIEW order_sellers AS
SELECT DISTINCT orders.order_id, items.seller_id, sellers.seller_state
FROM reviewed_delivered_orders AS orders
JOIN fact_order_items AS items USING (order_id)
JOIN dim_sellers AS sellers USING (seller_id);

CREATE OR REPLACE TEMP VIEW review_by_delivery_status AS
SELECT CASE WHEN is_late THEN 'Late' ELSE 'On time' END AS delivery_status,
       COUNT(*) AS order_count,
       COUNT(review_score) AS scored_order_count,
       AVG(review_score) AS mean_review_score,
       STDDEV_SAMP(review_score) AS sd_review_score
FROM reviewed_delivered_orders
WHERE is_late IS NOT NULL
GROUP BY delivery_status;

CREATE OR REPLACE TEMP VIEW review_by_lateness_bucket AS
SELECT CASE WHEN days_late = 0 THEN 'On time'
            WHEN days_late BETWEEN 1 AND 3 THEN '1-3 days'
            WHEN days_late BETWEEN 4 AND 7 THEN '4-7 days'
            ELSE '8+ days' END AS lateness_bucket,
       CASE WHEN days_late = 0 THEN 1
            WHEN days_late BETWEEN 1 AND 3 THEN 2
            WHEN days_late BETWEEN 4 AND 7 THEN 3
            ELSE 4 END AS bucket_order,
       COUNT(*) AS order_count,
       COUNT(review_score) AS scored_order_count,
       AVG(review_score) AS mean_review_score,
       STDDEV_SAMP(review_score) AS sd_review_score
FROM reviewed_delivered_orders
WHERE days_late IS NOT NULL
GROUP BY lateness_bucket, bucket_order;

CREATE OR REPLACE TEMP VIEW seller_delivery_rates AS
SELECT seller_id,
       seller_state,
       COUNT(*) AS delivered_reviewed_order_count,
       COUNT(*) FILTER (WHERE is_late IS NOT NULL) AS known_delivery_status_count,
       COUNT(*) FILTER (WHERE is_late IS TRUE) AS late_order_count,
       AVG(CASE WHEN is_late IS TRUE THEN 1.0
                WHEN is_late IS FALSE THEN 0.0 END) AS late_rate,
       AVG(review_score) AS mean_review_score
FROM order_sellers
JOIN reviewed_delivered_orders USING (order_id)
GROUP BY seller_id, seller_state;