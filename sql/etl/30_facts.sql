-- ============================================================
-- SQL ETL PIPELINE (SQLite) — FACTS
-- - Transaction fact (line-level)
-- - Customer-level RFM fact + scores + segments (SQL-native)
-- ============================================================

-- Line-level transaction fact
DROP TABLE IF EXISTS fct_transactions;

CREATE TABLE fct_transactions AS
SELECT
  invoice_no,
  stock_code,
  description,
  quantity,
  invoice_date,
  unit_price,
  customer_id,
  country,
  revenue,
  year_month
FROM stg_transactions;

CREATE INDEX IF NOT EXISTS idx_fct_transactions_customer ON fct_transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_fct_transactions_year_month ON fct_transactions(year_month);

-- Customer-level RFM
DROP TABLE IF EXISTS fct_customer_rfm;

CREATE TABLE fct_customer_rfm (
  customer_id INTEGER PRIMARY KEY,
  last_purchase_at TEXT,
  recency INTEGER,
  frequency INTEGER,
  monetary REAL,
  r_score INTEGER,
  f_score INTEGER,
  m_score INTEGER,
  rfm_segment TEXT,
  segment TEXT
);

INSERT INTO fct_customer_rfm
WITH reference AS (
  SELECT MAX(invoice_date) AS max_date FROM fct_transactions
),
aggs AS (
  SELECT
    customer_id,
    MAX(invoice_date) AS last_purchase_at,
    COUNT(DISTINCT invoice_no) AS frequency,
    SUM(revenue) AS monetary
  FROM fct_transactions
  GROUP BY customer_id
),
base AS (
  SELECT
    a.customer_id,
    a.last_purchase_at,
    CAST(JULIANDAY(r.max_date) - JULIANDAY(a.last_purchase_at) + 1 AS INTEGER) AS recency,
    a.frequency,
    a.monetary
  FROM aggs a
  CROSS JOIN reference r
),
scored AS (
  SELECT
    *,
    -- Recency: lower is better. We want 4=best, 1=worst.
    5 - NTILE(4) OVER (ORDER BY recency ASC) AS r_score,
    NTILE(4) OVER (ORDER BY frequency ASC) AS f_score,
    NTILE(4) OVER (ORDER BY monetary ASC) AS m_score
  FROM base
)
SELECT
  customer_id,
  last_purchase_at,
  recency,
  frequency,
  ROUND(monetary, 2) AS monetary,
  r_score,
  f_score,
  m_score,
  CAST(r_score AS TEXT) || '-' || CAST(f_score AS TEXT) || '-' || CAST(m_score AS TEXT) AS rfm_segment,
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
FROM scored;

CREATE INDEX IF NOT EXISTS idx_fct_customer_rfm_segment ON fct_customer_rfm(segment);
CREATE INDEX IF NOT EXISTS idx_fct_customer_rfm_recency ON fct_customer_rfm(recency);

