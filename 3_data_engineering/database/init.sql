-- -----------------------------------------------------------------------------
-- POSTGRESQL SCHEMA — SOURCE DATABASE
-- -----------------------------------------------------------------------------
-- This script runs automatically the first time the PostgreSQL container
-- starts. It creates the orders table that the Inventory Service writes to.
--
-- IMPORTANT NOTE FOR LAB 3:
-- Debezium CDC requires PostgreSQL to be running with wal_level=logical.
-- This is set via the "command" entry in docker-compose.yaml.
-- No changes to this SQL file are needed for CDC to work — Debezium reads
-- the WAL stream at the server level, not at the schema level.
--
-- The POSTGRES_USER (lab_user) is created as a superuser by the PostgreSQL
-- Docker image, which grants it the REPLICATION privilege that Debezium
-- requires to connect as a logical replication client.
-- -----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS orders (
    order_id        VARCHAR(36)     PRIMARY KEY,
    client_fname    VARCHAR(100)    NOT NULL,
    item            VARCHAR(100)    NOT NULL,
    order_quantity  INTEGER         NOT NULL,
    received_at     TIMESTAMP       DEFAULT NOW()
);