# =============================================================================
# connect_clickhouse.R
# =============================================================================
# PURPOSE:
#   Verify that R can connect to both the ClickHouse data warehouse and the
#   PostgreSQL operational database before you open the analytics notebook.
#   Run this file line by line using Ctrl+Enter (Windows/Linux) or
#   Cmd+Enter (macOS) in RStudio.
#
# PREREQUISITES:
#   1. The stack of containers from Part 3 must be running (docker-compose up -d)
#   2. The benchmark data generator must have completed (python generate_data.py)
#   3. The following R packages must be installed:
#
     install.packages(c(
     "DBI",          # Standard R database interface
     "RPostgres",    # PostgreSQL driver
     # "clickhouse",   # ClickHouse driver (uses HTTP interface on port 8123)
     "odbc",          # ODBC interface for ClickHouse (uses HTTP interface on port 8123)
     "tidyverse",    # Data manipulation and ggplot2 visualisation
     "scales",       # Axis formatting helpers for ggplot2
     "knitr",        # R Notebook rendering
     "bench"         # Precise benchmarking with statistical summaries
     ))
#
# NOTE:
#   ClickHouse access is done through ODBC. The ClickHouse ODBC driver
#   must have already been installed.
# =============================================================================

# -----------------------------------------------------------------------------
# STEP 1: Load required libraries
# -----------------------------------------------------------------------------

library(DBI)
library(RPostgres)
library(odbc)
library(tidyverse)
library(scales)
library(bench)

cat("All libraries loaded successfully.\n")

# -----------------------------------------------------------------------------
# STEP 2: Check that a ClickHouse ODBC driver is available
# -----------------------------------------------------------------------------
# The exact driver name may vary slightly depending on the operating system
# and driver version, so this script checks for a ClickHouse driver first.
# -----------------------------------------------------------------------------

drivers <- odbc::odbcListDrivers()

if (!any(grepl("ClickHouse", drivers$name, ignore.case = TRUE))) {
  stop(
    "No ClickHouse ODBC driver was found. ",
    "Install the ClickHouse ODBC driver first, then rerun this script."
  )
}

# -----------------------------------------------------------------------------
# STEP 3: Connect to ClickHouse through ODBC
# -----------------------------------------------------------------------------
# ClickHouse listens on:
#   Port 8123 — HTTP interface
#   Port 9000 — Native TCP interface
#
# The ClickHouse ODBC driver uses the HTTP endpoint.
# -----------------------------------------------------------------------------

ch_conn <- DBI::dbConnect(
  odbc::odbc(),
  driver   = "ClickHouse ODBC Driver (Unicode)",
  Url      = "http://localhost:8123/",
  Username = "default",
  Password = "lab_password",
  Database = "default"
)

on.exit({
  try(DBI::dbDisconnect(ch_conn), silent = TRUE)
  try(DBI::dbDisconnect(pg_conn), silent = TRUE)
}, add = TRUE)

cat("Connected to ClickHouse.\n")

ch_test <- dbGetQuery(ch_conn, "SELECT COUNT(*) AS total_orders FROM orders")
cat(sprintf(
  "ClickHouse orders table contains %s rows.\n",
  format(ch_test$total_orders, big.mark = ",")
))

if (ch_test$total_orders < 100000) {
  warning(
    "ClickHouse contains fewer than 100,000 rows. ",
    "The performance benchmark will not produce a meaningful result. ",
    "Run generate_data.py first."
  )
}

# -----------------------------------------------------------------------------
# STEP 4: Connect to PostgreSQL
# -----------------------------------------------------------------------------

pg_conn <- DBI::dbConnect(
  RPostgres::Postgres(),
  host     = "localhost",
  port     = 5432L,
  dbname   = "lab_db",
  user     = "lab_user",
  password = "lab_password"
)

cat("Connected to PostgreSQL.\n")

pg_test <- dbGetQuery(pg_conn, "SELECT COUNT(*) AS total_orders FROM orders")
cat(sprintf(
  "PostgreSQL orders table contains %s rows.\n",
  format(pg_test$total_orders, big.mark = ",")
))

# -----------------------------------------------------------------------------
# STEP 5: Inspect the schemas of both tables
# -----------------------------------------------------------------------------

cat("\n--- PostgreSQL orders schema ---\n")
pg_cols <- dbGetQuery(pg_conn, "
  SELECT column_name, data_type
  FROM information_schema.columns
  WHERE table_name = 'orders'
  ORDER BY ordinal_position
")
print(pg_cols)

cat("\n--- ClickHouse orders schema ---\n")
ch_cols <- dbGetQuery(ch_conn, "DESCRIBE TABLE orders")
print(ch_cols[, c("name", "type")])

# -----------------------------------------------------------------------------
# STEP 6: Preview the data from both databases
# -----------------------------------------------------------------------------

cat("\n--- PostgreSQL: first 5 rows ---\n")
pg_preview <- dbGetQuery(pg_conn, "
  SELECT order_id, client_fname, item, order_quantity, received_at
  FROM orders
  ORDER BY received_at DESC
  LIMIT 5
")
print(pg_preview)

cat("\n--- ClickHouse: first 5 rows ---\n")
ch_preview <- dbGetQuery(ch_conn, "
  SELECT order_id, customer_name, item, order_quantity,
         is_bulk_order, received_at, processed_at, operation
  FROM orders
  ORDER BY processed_at DESC
  LIMIT 5
")
print(ch_preview)

# -----------------------------------------------------------------------------
# STEP 7: Confirm readiness
# -----------------------------------------------------------------------------

cat("\n")
cat(paste(rep("=", 70), collapse = ""), "\n", sep = "")
cat("Both connections are ready.\n")
cat("ch_conn -> ClickHouse (data warehouse)\n")
cat("pg_conn -> PostgreSQL (operational database)\n")
cat("Open lab4_analytics_with_odbc.Rmd to begin the analytics notebook.\n")
cat(paste(rep("=", 70), collapse = ""), "\n", sep = "")
