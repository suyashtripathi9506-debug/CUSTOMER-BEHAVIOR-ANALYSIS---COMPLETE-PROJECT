-- ================================================================
-- CUSTOMER BEHAVIOR ANALYSIS - SQL QUERIES REFERENCE
-- ================================================================

-- 1. BASIC CUSTOMER INFORMATION QUERIES
-- ================================================================

-- Get all customers with their segment and channel
SELECT customer_id, customer_name, email, customer_segment, acquisition_channel
FROM customers
ORDER BY customer_name;

-- Customers by country
SELECT country, COUNT(*) as customer_count
FROM customers
GROUP BY country
ORDER BY customer_count DESC;

-- Customers by acquisition channel
SELECT acquisition_channel, COUNT(*) as count,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM customers), 2) as percentage
FROM customers
GROUP BY acquisition_channel
ORDER BY count DESC;


-- 2. TRANSACTION ANALYSIS QUERIES
-- ================================================================

-- Total transactions per customer
SELECT c.customer_id, c.customer_name, c.customer_segment,
       COUNT(t.transaction_id) as transaction_count,
       SUM(t.amount) as total_spent,
       AVG(t.amount) as avg_transaction,
       MIN(t.amount) as min_transaction,
       MAX(t.amount) as max_transaction
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY c.customer_id
ORDER BY total_spent DESC;

-- Revenue by product category
SELECT product_category, COUNT(*) as transaction_count,
       SUM(amount) as total_revenue,
       AVG(amount) as avg_transaction,
       SUM(quantity) as total_units
FROM transactions
GROUP BY product_category
ORDER BY total_revenue DESC;

-- Revenue by payment method
SELECT payment_method, COUNT(*) as transactions,
       SUM(amount) as revenue,
       AVG(amount) as avg_amount
FROM transactions
GROUP BY payment_method
ORDER BY revenue DESC;

-- Monthly revenue trend
SELECT strftime('%Y-%m', transaction_date) as month,
       COUNT(*) as transaction_count,
       SUM(amount) as monthly_revenue,
       AVG(amount) as avg_transaction
FROM transactions
GROUP BY month
ORDER BY month DESC;


-- 3. CUSTOMER ENGAGEMENT ANALYSIS
-- ================================================================

-- Engagement metrics per customer
SELECT c.customer_id, c.customer_name,
       COUNT(DISTINCT e.engagement_date) as engagement_days,
       SUM(e.page_views) as total_page_views,
       AVG(e.page_views) as avg_page_views,
       AVG(e.session_duration_minutes) as avg_session_duration,
       SUM(e.items_added_to_cart) as total_cart_adds,
       SUM(CASE WHEN e.items_purchased > 0 THEN 1 ELSE 0 END) as days_with_purchase
FROM customers c
LEFT JOIN engagement e ON c.customer_id = e.customer_id
GROUP BY c.customer_id
ORDER BY engagement_days DESC;

-- Device usage analysis
SELECT device_type, COUNT(DISTINCT customer_id) as unique_customers,
       COUNT(*) as total_sessions,
       AVG(page_views) as avg_page_views,
       AVG(session_duration_minutes) as avg_session_duration
FROM engagement
GROUP BY device_type
ORDER BY total_sessions DESC;

-- Conversion analysis
SELECT c.customer_id, c.customer_name,
       COUNT(DISTINCT e.engagement_date) as engagement_days,
       SUM(CASE WHEN e.items_purchased > 0 THEN 1 ELSE 0 END) as conversion_days,
       ROUND(100.0 * SUM(CASE WHEN e.items_purchased > 0 THEN 1 ELSE 0 END) /
             COUNT(DISTINCT e.engagement_date), 2) as conversion_rate
FROM customers c
LEFT JOIN engagement e ON c.customer_id = e.customer_id
GROUP BY c.customer_id
HAVING engagement_days > 0
ORDER BY conversion_rate DESC;


-- 4. RECENCY, FREQUENCY, MONETARY (RFM) ANALYSIS
-- ================================================================

-- RFM Scoring (most important query for customer segmentation)
SELECT c.customer_id, c.customer_name, c.customer_segment,
       -- Recency: days since last purchase
       CAST((julianday('now') - julianday(MAX(t.transaction_date))) AS INTEGER) as recency_days,
       -- Frequency: number of purchases
       COUNT(DISTINCT t.transaction_id) as frequency,
       -- Monetary: total spent
       SUM(t.amount) as monetary_value,
       -- Calculate RFM segments
       CASE 
           WHEN COUNT(DISTINCT t.transaction_id) > 5 AND SUM(t.amount) > 50000 THEN 'VIP'
           WHEN COUNT(DISTINCT t.transaction_id) > 3 AND SUM(t.amount) > 25000 THEN 'Gold'
           WHEN COUNT(DISTINCT t.transaction_id) > 1 THEN 'Silver'
           ELSE 'Bronze'
       END as rfm_segment
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY c.customer_id
ORDER BY monetary_value DESC;

-- Churn risk analysis (customers inactive for 90+ days)
SELECT c.customer_id, c.customer_name, c.customer_segment,
       CAST((julianday('now') - julianday(MAX(t.transaction_date))) AS INTEGER) as days_since_purchase,
       COUNT(DISTINCT t.transaction_id) as lifetime_purchases,
       SUM(t.amount) as lifetime_value,
       CASE
           WHEN (julianday('now') - julianday(MAX(t.transaction_date))) > 180 THEN 'Critical'
           WHEN (julianday('now') - julianday(MAX(t.transaction_date))) > 90 THEN 'High'
           WHEN (julianday('now') - julianday(MAX(t.transaction_date))) > 30 THEN 'Medium'
           ELSE 'Low'
       END as churn_risk
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY c.customer_id
ORDER BY days_since_purchase DESC;


-- 5. CUSTOMER LIFETIME VALUE (CLV) ESTIMATION
-- ================================================================

-- CLV calculation (simplified 3-year projection)
SELECT c.customer_id, c.customer_name, c.customer_segment,
       COUNT(DISTINCT t.transaction_id) as total_transactions,
       SUM(t.amount) as total_spent,
       ROUND(AVG(t.amount), 2) as avg_transaction_value,
       ROUND(
           (AVG(t.amount) * (COUNT(DISTINCT t.transaction_id) / 
            GREATEST(CAST((julianday('now') - julianday(c.signup_date)) / 30 AS FLOAT), 1)) *
           12 * 3), 2
       ) as clv_estimate_3year
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY c.customer_id
ORDER BY clv_estimate_3year DESC;


-- 6. COHORT ANALYSIS (Customer by Signup Month)
-- ================================================================

-- Customer cohort retention
SELECT 
    strftime('%Y-%m', c.signup_date) as signup_month,
    COUNT(DISTINCT c.customer_id) as customers_acquired,
    SUM(CASE WHEN t.transaction_date IS NOT NULL THEN 1 ELSE 0 END) as customers_with_purchase,
    ROUND(100.0 * SUM(CASE WHEN t.transaction_date IS NOT NULL THEN 1 ELSE 0 END) / 
          COUNT(DISTINCT c.customer_id), 2) as retention_rate,
    SUM(COALESCE(t.amount, 0)) as cohort_revenue
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY signup_month
ORDER BY signup_month DESC;


-- 7. SEGMENT PERFORMANCE ANALYSIS
-- ================================================================

-- Customer segment performance
SELECT c.customer_segment,
       COUNT(DISTINCT c.customer_id) as customer_count,
       COUNT(DISTINCT t.transaction_id) as total_transactions,
       SUM(t.amount) as segment_revenue,
       ROUND(AVG(t.amount), 2) as avg_transaction,
       ROUND(SUM(t.amount) / COUNT(DISTINCT c.customer_id), 2) as revenue_per_customer,
       COUNT(DISTINCT e.engagement_date) as total_engagement_days
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
LEFT JOIN engagement e ON c.customer_id = e.customer_id
GROUP BY c.customer_segment
ORDER BY segment_revenue DESC;

-- Acquisition channel effectiveness
SELECT c.acquisition_channel,
       COUNT(DISTINCT c.customer_id) as customers,
       COUNT(DISTINCT t.transaction_id) as transactions,
       SUM(t.amount) as revenue,
       ROUND(SUM(t.amount) / COUNT(DISTINCT c.customer_id), 2) as revenue_per_customer,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN t.transaction_id IS NOT NULL 
             THEN c.customer_id END) / COUNT(DISTINCT c.customer_id), 2) as conversion_rate
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY c.acquisition_channel
ORDER BY revenue DESC;


-- 8. TOP CUSTOMERS & PRODUCTS
-- ================================================================

-- Top 20 customers by revenue
SELECT c.customer_id, c.customer_name, c.country, c.customer_segment,
       COUNT(DISTINCT t.transaction_id) as purchases,
       SUM(t.amount) as total_spent,
       AVG(t.amount) as avg_purchase,
       MIN(t.transaction_date) as first_purchase,
       MAX(t.transaction_date) as last_purchase
FROM customers c
JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY c.customer_id
ORDER BY total_spent DESC
LIMIT 20;

-- Top products by quantity and revenue
SELECT product_category,
       COUNT(*) as transaction_count,
       SUM(quantity) as total_units_sold,
       SUM(amount) as total_revenue,
       ROUND(AVG(amount), 2) as avg_transaction
FROM transactions
GROUP BY product_category
ORDER BY total_revenue DESC;


-- 9. CUSTOMER QUALITY & VALUE ANALYSIS
-- ================================================================

-- High-value vs Low-value customer comparison
SELECT 
    CASE 
        WHEN (SELECT AVG(total_spent) FROM (
            SELECT SUM(amount) as total_spent FROM transactions 
            GROUP BY customer_id)) >= SUM(t.amount) OVER (PARTITION BY c.customer_id) 
        THEN 'Below Average'
        ELSE 'Above Average'
    END as value_category,
    COUNT(DISTINCT c.customer_id) as customer_count,
    ROUND(AVG(COUNT(DISTINCT t.transaction_id)) OVER (PARTITION BY c.customer_id), 2) as avg_purchases,
    ROUND(SUM(t.amount) / COUNT(DISTINCT c.customer_id), 2) as avg_customer_value
FROM customers c
LEFT JOIN transactions t ON c.customer_id = t.customer_id
GROUP BY c.customer_id;

-- Recently active customers (last 30 days)
SELECT c.customer_id, c.customer_name, c.customer_segment,
       COUNT(DISTINCT t.transaction_id) as recent_transactions,
       SUM(t.amount) as recent_spending,
       MAX(t.transaction_date) as last_transaction_date
FROM customers c
JOIN transactions t ON c.customer_id = t.customer_id
WHERE julianday('now') - julianday(t.transaction_date) <= 30
GROUP BY c.customer_id
ORDER BY recent_spending DESC;


-- 10. USEFUL ANALYTICS & KPI QUERIES
-- ================================================================

-- Overall business KPIs
SELECT 
    (SELECT COUNT(DISTINCT customer_id) FROM customers) as total_customers,
    (SELECT COUNT(DISTINCT customer_id) FROM transactions) as customers_with_purchases,
    COUNT(DISTINCT customer_id) as active_customers,
    COUNT(*) as total_transactions,
    SUM(amount) as total_revenue,
    ROUND(AVG(amount), 2) as avg_transaction_value,
    ROUND(SUM(amount) / COUNT(DISTINCT customer_id), 2) as revenue_per_customer
FROM transactions
WHERE julianday('now') - julianday(transaction_date) <= 30;

-- Customer growth over time
SELECT strftime('%Y-%m', signup_date) as month,
       COUNT(*) as new_customers,
       SUM(COUNT(*)) OVER (ORDER BY strftime('%Y-%m', signup_date)) as cumulative_customers
FROM customers
GROUP BY month
ORDER BY month;

-- Product purchase frequency
SELECT product_category,
       COUNT(*) as total_purchases,
       COUNT(DISTINCT customer_id) as unique_customers,
       ROUND(CAST(COUNT(*) AS FLOAT) / COUNT(DISTINCT customer_id), 2) as purchases_per_customer
FROM transactions
GROUP BY product_category
ORDER BY total_purchases DESC;
