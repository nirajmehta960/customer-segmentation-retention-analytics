-- ============================================================
-- SQL ETL PIPELINE (SQLite) — VALIDATION / SMOKE TESTS
-- Lightweight checks to confirm key tables/views are populated.
-- ============================================================

SELECT 'stg_transactions' AS object_name, COUNT(*) AS row_count FROM stg_transactions
UNION ALL
SELECT 'fct_transactions', COUNT(*) FROM fct_transactions
UNION ALL
SELECT 'dim_customer', COUNT(*) FROM dim_customer
UNION ALL
SELECT 'dim_country', COUNT(*) FROM dim_country
UNION ALL
SELECT 'dim_product', COUNT(*) FROM dim_product
UNION ALL
SELECT 'fct_customer_rfm', COUNT(*) FROM fct_customer_rfm;

-- Quick KPI sanity check
SELECT * FROM mart_kpis;

-- Segment breakdown
SELECT segment, COUNT(*) AS customers, ROUND(SUM(monetary), 2) AS revenue
FROM fct_customer_rfm
GROUP BY segment
ORDER BY revenue DESC;

