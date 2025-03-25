-- ============================================================
-- SQL ETL PIPELINE (SQLite) — INIT
-- Customer Segmentation & Retention Analytics (Online Retail)
--
-- Assumptions (raw load happens outside SQL):
-- - Table `online_retail` exists (raw transactional lines)
--   Expected columns:
--     InvoiceNo, StockCode, Description, Quantity, InvoiceDate,
--     UnitPrice, CustomerID, Country
-- ============================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

