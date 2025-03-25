-- ============================================================
-- SQL ETL PIPELINE (SQLite) — STAGING
-- - Applies the same logical filters as the Python cleaning step:
--   - remove cancellations (InvoiceNo starts with 'C' or 'A')
--   - keep Quantity > 0, UnitPrice > 0
--   - require CustomerID
-- - Standardizes types and derives Revenue + YearMonth
-- ============================================================

DROP TABLE IF EXISTS stg_transactions;

CREATE TABLE stg_transactions AS
WITH base AS (
  SELECT
    TRIM(CAST(InvoiceNo AS TEXT)) AS invoice_no,
    TRIM(CAST(StockCode AS TEXT)) AS stock_code,
    Description AS description,
    CAST(Quantity AS INTEGER) AS quantity,
    -- Keep InvoiceDate as stored; downstream recency uses JULIANDAY().
    InvoiceDate AS invoice_date,
    CAST(UnitPrice AS REAL) AS unit_price,
    CAST(CustomerID AS INTEGER) AS customer_id,
    COALESCE(NULLIF(TRIM(CAST(Country AS TEXT)), ''), 'Unknown') AS country
  FROM online_retail
  WHERE CustomerID IS NOT NULL
    AND CAST(Quantity AS REAL) > 0
    AND CAST(UnitPrice AS REAL) > 0
    AND UPPER(TRIM(CAST(InvoiceNo AS TEXT))) NOT LIKE 'C%'
    AND UPPER(TRIM(CAST(InvoiceNo AS TEXT))) NOT LIKE 'A%'
)
SELECT
  invoice_no,
  stock_code,
  description,
  quantity,
  invoice_date,
  unit_price,
  customer_id,
  country,
  (quantity * unit_price) AS revenue,
  -- YearMonth: YYYY-MM (works for ISO datetime strings; for non-ISO, load should normalize)
  STRFTIME('%Y-%m', invoice_date) AS year_month
FROM base;

CREATE INDEX IF NOT EXISTS idx_stg_transactions_customer ON stg_transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_stg_transactions_invoice ON stg_transactions(invoice_no);
CREATE INDEX IF NOT EXISTS idx_stg_transactions_date ON stg_transactions(invoice_date);

