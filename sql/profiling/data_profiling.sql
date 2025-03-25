-- Data profiling for Online Retail (run after loading into SQLite/Postgres).
-- Expect: InvoiceNo, StockCode, Description, Quantity, InvoiceDate, UnitPrice, CustomerID, Country

-- Row count
SELECT COUNT(*) AS row_count FROM online_retail;

-- Missing CustomerID
SELECT COUNT(*) AS null_customer_id FROM online_retail WHERE CustomerID IS NULL;

-- Cancellations (InvoiceNo starting with 'C')
SELECT COUNT(*) AS cancellation_count FROM online_retail WHERE CAST(InvoiceNo AS TEXT) LIKE 'C%';

-- Quantity and UnitPrice ranges
SELECT MIN(Quantity) AS min_qty, MAX(Quantity) AS max_qty,
       MIN(UnitPrice) AS min_price, MAX(UnitPrice) AS max_price
FROM online_retail;

-- Revenue (Quantity * UnitPrice) summary
SELECT COUNT(*) AS lines, SUM(Quantity * UnitPrice) AS total_revenue
FROM online_retail
WHERE CAST(InvoiceNo AS TEXT) NOT LIKE 'C%' AND Quantity > 0 AND UnitPrice > 0 AND CustomerID IS NOT NULL;

-- Unique customers and invoices (after logical filters)
SELECT COUNT(DISTINCT CustomerID) AS unique_customers,
       COUNT(DISTINCT InvoiceNo) AS unique_invoices
FROM online_retail
WHERE CAST(InvoiceNo AS TEXT) NOT LIKE 'C%' AND Quantity > 0 AND UnitPrice > 0 AND CustomerID IS NOT NULL;

-- Revenue by country (top 10)
SELECT Country, SUM(Quantity * UnitPrice) AS revenue
FROM online_retail
WHERE CAST(InvoiceNo AS TEXT) NOT LIKE 'C%' AND Quantity > 0 AND UnitPrice > 0
GROUP BY Country
ORDER BY revenue DESC
LIMIT 10;
