-- ============================================================
-- SQL ETL PIPELINE (SQLite) — DIMENSIONS
-- Small lookups derived from staged transactions.
-- ============================================================

DROP TABLE IF EXISTS dim_customer;
DROP TABLE IF EXISTS dim_country;
DROP TABLE IF EXISTS dim_product;

CREATE TABLE dim_customer AS
SELECT
  customer_id,
  COUNT(DISTINCT invoice_no) AS invoice_count,
  MIN(invoice_date) AS first_purchase_at,
  MAX(invoice_date) AS last_purchase_at,
  ROUND(SUM(revenue), 2) AS lifetime_revenue
FROM stg_transactions
GROUP BY customer_id;

CREATE TABLE dim_country AS
SELECT
  country,
  COUNT(DISTINCT customer_id) AS customer_count,
  ROUND(SUM(revenue), 2) AS total_revenue
FROM stg_transactions
GROUP BY country;

CREATE TABLE dim_product AS
SELECT
  stock_code,
  MAX(description) AS description,
  COUNT(*) AS line_count,
  ROUND(SUM(revenue), 2) AS total_revenue
FROM stg_transactions
GROUP BY stock_code;

CREATE INDEX IF NOT EXISTS idx_dim_customer_rev ON dim_customer(lifetime_revenue);
CREATE INDEX IF NOT EXISTS idx_dim_country_rev ON dim_country(total_revenue);
CREATE INDEX IF NOT EXISTS idx_dim_product_rev ON dim_product(total_revenue);

