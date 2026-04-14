-- -----------------------------------------------------------------------------
-- CLICKHOUSE SCHEMA — DATA WAREHOUSE DESTINATION
-- -----------------------------------------------------------------------------
-- This script runs automatically the first time the ClickHouse container
-- starts. It creates the orders table that the Transformer Service writes to.
--
-- COLUMNAR STORAGE:
-- Unlike PostgreSQL which stores data row by row, ClickHouse stores each
-- column separately on disk. This makes column-level operations (SUM,
-- AVG, GROUP BY item) extremely fast because ClickHouse only reads the
-- columns it needs, skipping all others.
--
-- ENGINE: ReplacingMergeTree
-- ClickHouse offers many table engines. We use ReplacingMergeTree because
-- it handles duplicate records gracefully — a common occurrence in CDC
-- pipelines due to at-least-once delivery guarantees.
--
-- ReplacingMergeTree keeps only the most recent row per ORDER BY key
-- during background merge operations. The column passed as its argument
-- (processed_at) determines which row is "most recent" — the row with
-- the largest processed_at value is kept, and older duplicates are removed.
--
-- NOTICE the schema differences from PostgreSQL:
--   - client_fname is renamed to customer_name (applied by the transformer)
--   - is_bulk_order is a new computed field (applied by the transformer)
--   - processed_at is the time the transformer wrote this record
--   - received_at is the original time the order entered PostgreSQL
--   - operation records what type of database change triggered this event
-- These differences illustrate what the transformation step is responsible for.
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS orders
(
    order_id        String,
    customer_name   String,
    item            String,
    order_quantity  Int32,
    is_bulk_order   UInt8,
    received_at     DateTime,
    processed_at    DateTime,
    operation       LowCardinality(String)
)
ENGINE = ReplacingMergeTree(processed_at)
ORDER BY order_id;