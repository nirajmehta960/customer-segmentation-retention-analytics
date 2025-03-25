-- ============================================================
-- SQL ETL PIPELINE (SQLite) — MARTS / ANALYTICS VIEWS
-- Consumption-ready views for BI and analysis.
-- ============================================================

DROP VIEW IF EXISTS mart_kpis;
DROP VIEW IF EXISTS mart_segment_summary;
DROP VIEW IF EXISTS mart_revenue_by_country;
DROP VIEW IF EXISTS mart_cohort_retention_input;

-- 1) High-level KPIs
CREATE VIEW mart_kpis AS
SELECT
  COUNT(DISTINCT customer_id) AS unique_customers,
  COUNT(DISTINCT invoice_no) AS unique_invoices,
  COUNT(*) AS total_lines,
  ROUND(SUM(revenue), 2) AS total_revenue,
  ROUND(SUM(revenue) / COUNT(DISTINCT customer_id), 2) AS revenue_per_customer
FROM fct_transactions;

-- 2) Segment summary (counts + revenue share)
CREATE VIEW mart_segment_summary AS
WITH seg AS (
  SELECT
    segment,
    COUNT(*) AS customer_count,
    ROUND(AVG(recency), 1) AS avg_recency,
    ROUND(AVG(frequency), 1) AS avg_frequency,
    ROUND(AVG(monetary), 2) AS avg_monetary,
    ROUND(SUM(monetary), 2) AS total_revenue
  FROM fct_customer_rfm
  GROUP BY segment
),
tot AS (
  SELECT SUM(total_revenue) AS all_revenue FROM seg
)
SELECT
  s.*,
  ROUND(s.customer_count * 100.0 / (SELECT SUM(customer_count) FROM seg), 1) AS pct_customers,
  ROUND(s.total_revenue * 100.0 / t.all_revenue, 1) AS pct_revenue
FROM seg s
CROSS JOIN tot t
ORDER BY total_revenue DESC;

-- 3) Revenue by country
CREATE VIEW mart_revenue_by_country AS
SELECT
  country,
  COUNT(DISTINCT customer_id) AS customers,
  ROUND(SUM(revenue), 2) AS revenue,
  ROUND(SUM(revenue) / COUNT(DISTINCT customer_id), 2) AS revenue_per_customer
FROM fct_transactions
GROUP BY country
ORDER BY revenue DESC;

-- 4) Cohort retention input (customer-month activity matrix input)
-- This view produces (cohort_month, activity_month, cohort_index, customers_active) which can be pivoted in BI.
CREATE VIEW mart_cohort_retention_input AS
WITH customer_first AS (
  SELECT
    customer_id,
    MIN(year_month) AS cohort_month
  FROM fct_transactions
  GROUP BY customer_id
),
activity AS (
  SELECT DISTINCT
    t.customer_id,
    cf.cohort_month,
    t.year_month AS activity_month
  FROM fct_transactions t
  JOIN customer_first cf ON cf.customer_id = t.customer_id
)
SELECT
  cohort_month,
  activity_month,
  ( (strftime('%Y', activity_month || '-01') - strftime('%Y', cohort_month || '-01')) * 12 +
    (strftime('%m', activity_month || '-01') - strftime('%m', cohort_month || '-01')) ) AS cohort_index,
  COUNT(DISTINCT customer_id) AS customers_active
FROM activity
GROUP BY cohort_month, activity_month, cohort_index
ORDER BY cohort_month, activity_month;

