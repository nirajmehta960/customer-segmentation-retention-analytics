-- 02_rfm.sql
-- Create RFM (Recency, Frequency, Monetary) scores and segments using SQL.
-- Compatible with SQLite / PostgreSQL (see comments for date handling).

WITH filtered_data AS (
    SELECT
        CustomerID,
        InvoiceNo,
        InvoiceDate,
        Quantity,
        UnitPrice,
        (Quantity * UnitPrice) AS Revenue
    FROM online_retail
    WHERE CustomerID IS NOT NULL
      AND CAST(InvoiceNo AS TEXT) NOT LIKE 'C%'
      AND Quantity > 0
      AND UnitPrice > 0
),

reference AS (
    -- Get the maximum date in the dataset to act as "today"
    SELECT MAX(InvoiceDate) AS max_date
    FROM filtered_data
),

customer_aggs AS (
    SELECT
        CustomerID,
        MAX(InvoiceDate) AS last_purchase,
        COUNT(DISTINCT InvoiceNo) AS frequency,
        SUM(Revenue) AS monetary
    FROM filtered_data
    GROUP BY CustomerID
),

rfm_base AS (
    SELECT
        a.CustomerID,
        a.last_purchase,
        -- Recency: Days between last_purchase and reference date (+1 to avoid 0 days for same-day purchases)
        -- PostgreSQL: DATE_PART('day', r.max_date::TIMESTAMP - a.last_purchase::TIMESTAMP) + 1 AS recency
        -- SQLite: CAST(JULIANDAY(r.max_date) - JULIANDAY(a.last_purchase) + 1 AS INTEGER) AS recency
        CAST(JULIANDAY(r.max_date) - JULIANDAY(a.last_purchase) + 1 AS INTEGER) AS recency,
        a.frequency,
        a.monetary
    FROM customer_aggs a
    CROSS JOIN reference r
),

rfm_scores AS (
    SELECT
        CustomerID,
        recency,
        frequency,
        monetary,
        -- Score 1-4.
        -- Recency: lower is better. NTILE(4) ASC puts lowest recency in bucket 1.
        -- We want lowest recency to score 4, so 5 - NTILE.
        5 - NTILE(4) OVER (ORDER BY recency ASC) AS r_score,
        -- Frequency/Monetary: higher is better. NTILE(4) ASC puts highest in bucket 4.
        NTILE(4) OVER (ORDER BY frequency ASC) AS f_score,
        NTILE(4) OVER (ORDER BY monetary ASC) AS m_score
    FROM rfm_base
),

rfm_segments AS (
    SELECT
        CustomerID,
        recency,
        frequency,
        monetary,
        r_score,
        f_score,
        m_score,
        CAST(r_score AS TEXT) || '-' || CAST(f_score AS TEXT) || '-' || CAST(m_score AS TEXT) AS rfm_segment,
        -- Map R, F, M scores to business segments (based on PRD rules)
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
            WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal Customers'
            WHEN r_score >= 4 AND f_score <= 2 THEN 'New Customers'
            WHEN r_score >= 3 AND m_score >= 3 THEN 'Potential Loyalists'
            WHEN r_score = 2 AND f_score >= 2 THEN 'At Risk'
            WHEN r_score = 1 AND f_score >= 2 THEN 'Can''t Lose Them'
            WHEN r_score <= 2 AND f_score <= 2 AND m_score <= 2 THEN 'Lost / Hibernating'
            ELSE 'Need Attention'
        END AS segment
    FROM rfm_scores
)

-- View final customer segments and distribution
SELECT *
FROM rfm_segments
ORDER BY CustomerID;

/* 
-- Optional: Segment distribution summary to match the PRD Dashboard Requirements
SELECT 
    segment,
    COUNT(CustomerID) AS num_customers,
    ROUND(AVG(recency), 1) AS avg_recency,
    ROUND(AVG(frequency), 1) AS avg_frequency,
    ROUND(AVG(monetary), 2) AS avg_monetary,
    ROUND(SUM(monetary), 2) AS total_revenue
FROM rfm_segments
GROUP BY segment
ORDER BY total_revenue DESC;
*/
