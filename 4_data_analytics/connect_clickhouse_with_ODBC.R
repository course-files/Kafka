# Connect to Data Sources ----

## Purpose ----
#   Verify that R can connect to both the ClickHouse data warehouse and the
#   PostgreSQL operational database before you open the analytics notebook.
#   Run this file line by line using Ctrl+Enter (Windows/Linux) or
#   Cmd+Enter (macOS) in RStudio.
#

## Prerequisites ----

# 1. The stack of containers from Part 3 must be running (docker-compose up -d)

# 2. The benchmark data generator must have completed (python generate_data.py)

# 3. You should be in the "4_data_analytics" as your working directory
setwd("./4_data_analytics")
# Confirm the working directory you are in:
getwd()

## STEP 1: Install and Load required dependencies ----

### Install Dependencies ----
# Integrates R and C++. Other packages depend on this
install.packages("Rcpp", dependencies = TRUE)

# Standard R database interface
install.packages("DBI", dependencies = TRUE)

# ODBC interface for ClickHouse (uses HTTP interface on port 8123)
install.packages("odbc", dependencies = TRUE)

# PostgreSQL driver
install.packages("RPostgres", dependencies = TRUE)

# To avoid typing passwords in plaintext
install.packages("dotenv", dependencies = TRUE)

# Data manipulation and ggplot2 visualisation
install.packages("tidyverse", dependencies = TRUE)
# Axis formatting helpers for ggplot2
install.packages("scales", dependencies = TRUE)
# R Notebook rendering
install.packages("knitr", dependencies = TRUE)
# Precise benchmarking with statistical summaries
install.packages("bench", dependencies = TRUE)

### Load Dependencies ----
library(DBI)
library(odbc)

library(RPostgres)

library(dotenv)

library(tidyverse)
library(scales)
library(bench)

cat("All libraries loaded successfully.\n")

### Load Environment Variables from .env ----

# Create the .env file using the same .env.example file from Part 3 of the lab
# Place it in the same folder where this .R file is
dotenv::load_dot_env(file = ".env")

## STEP 2: Confirm Availability of ODBC Drivers ----

### Install ClickHouse ODBC Drivers ----

# Download from here: https://github.com/ClickHouse/clickhouse-odbc/releases/tag/v1.5.3.20260311.

#### Windows ----

# For Windows download the 'clickhouse-odbc-1.5.3.20260311-win64.msi' file and
# the 'clickhouse-odbc-1.5.3.20260311-powerbi-win64.msi' file as well.

#### Linux ----

# Install ODBC first:

# sudo apt update
# sudo apt install -y unixodbc unixodbc-dev

# Download the 'clickhouse-odbc-linux-Clang-UnixODBC-Release.zip' file.

#### MacOS ----

# Download the 'clickhouse-odbc-macos-AppleClang-UnixODBC-Release.zip' file.
# Install ODBC first
# brew install unixodbc

### Install PostgreSQL ODBC Drivers ----

#### Windows ----

# Download 'psqlodbc-setup.exe' from here:
# https://www.postgresql.org/ftp/odbc/releases/REL-18_00_0001-mimalloc/

#### Linux ----

# sudo apt-get install odbc-postgresql

#### MacOS ----

# brew install psqlodbc


# *****************************************************************************
# The exact driver name may vary slightly depending on the operating system
# and driver version, so this script checks for a ClickHouse driver
# and a PostgreSQL driver without specifying additional details.
# *****************************************************************************

drivers <- odbc::odbcListDrivers()

if (!any(grepl("ClickHouse", drivers$name, ignore.case = TRUE))) {
  stop(
    "No ClickHouse ODBC driver was found. ",
    "Install the ClickHouse ODBC driver first, then rerun this script."
  )
}

if (!any(grepl("PostgreSQL", drivers$name, ignore.case = TRUE))) {
  stop(
    "No PostgreSQL ODBC driver was found. ",
    "Install the PostgreSQL ODBC driver first, then rerun this script."
  )
}

## STEP 3: Connect to ClickHouse through ODBC ----

# *****************************************************************************
# ClickHouse listens on:
#   Port 8123 — HTTP interface
#   Port 9000 — Native TCP interface
#
# The ClickHouse ODBC driver uses the HTTP endpoint.
# *****************************************************************************

ch_conn <- DBI::dbConnect(
  # tells DBI which backend to use and how to translate DBI calls into database
  # commands. `odbc::odbc()` returns that driver object for any ODBC-compliant
  # data source.
  odbc::odbc(),
  driver   = "ClickHouse ODBC Driver (Unicode)",
  server   = "localhost",
  port     = 8123L,
  database = "default",
  uid      = "default",
  pwd      = Sys.getenv("CLICKHOUSE_PASSWORD")
)

## STEP 4: Connect to PostgreSQL through ODBC ----

# pg_conn <- DBI::dbConnect(
#   RPostgres::Postgres(),
#   host     = "localhost",
#   port     = 5432L,
#   dbname   = Sys.getenv("POSTGRES_DB"),
#   user     = Sys.getenv("POSTGRES_USER"),
#   password = Sys.getenv("POSTGRES_PASSWORD")
# )

pg_conn <- DBI::dbConnect(
  odbc::odbc(),
  driver   = "PostgreSQL Unicode",
  server   = "localhost",
  port     = 5432L,
  database = Sys.getenv("POSTGRES_DB"),
  uid      = Sys.getenv("POSTGRES_USER"),
  pwd      = Sys.getenv("POSTGRES_PASSWORD")
)

## STEP 5: Confirm the connections are both valid ----

#' This function connects to the specified database and executes
#' 'SELECT 1' to confirm that the connection is valid.
#'
#' @param conn The connection to the source of data.
#' @param label The name of the connection that will be displayed in the return.
#' @return The connection status.

confirm_connection <- function(conn, label) {
  alive <- DBI::dbIsValid(conn) &&
    tryCatch({
      DBI::dbGetQuery(conn, "SELECT 1")
      TRUE
    }, error = function(e) FALSE)
  cat(sprintf("%s -> %s\n", label, if (alive) "connected and responsive" else "NOT responding"))
  invisible(alive)
}

confirm_connection(ch_conn, "ch_conn (ClickHouse)")
confirm_connection(pg_conn, "pg_conn (PostgreSQL)")


## STEP 6: Confirm the number of rows in ClickHouse and in PostgreSQL ----

ch_test <- dbGetQuery(ch_conn, "SELECT COUNT(*) AS total_orders FROM orders")
cat(sprintf(
  "ClickHouse orders table contains %s rows.\n",
  format(as.numeric(ch_test$total_orders), big.mark = ",")
))

if (ch_test$total_orders < 100000) {
  warning(
    "ClickHouse contains fewer than 100,000 rows. ",
    "The performance benchmark will not produce a meaningful result. ",
    "Run 'python generate_data.py' first."
  )
}

pg_test <- dbGetQuery(pg_conn, "SELECT COUNT(*) AS total_orders FROM orders")

cat(sprintf(
  "PostgreSQL orders table contains %s rows.\n",
  format(as.numeric(pg_test$total_orders), big.mark = ",")
))

## STEP 7: Inspect the schemas of both tables ----

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

# STEP 8: Preview the data from both databases ----

cat("\n--- PostgreSQL: last 5 rows ---\n")
pg_preview <- dbGetQuery(pg_conn, "
  SELECT order_id, client_fname, item, order_quantity, received_at
  FROM orders
  ORDER BY received_at DESC
  LIMIT 5
")
print(pg_preview)

cat("\n--- ClickHouse: last 5 rows ---\n")
ch_preview <- dbGetQuery(ch_conn, "
  SELECT order_id, customer_name, item, order_quantity,
         is_bulk_order, received_at, processed_at, operation
  FROM orders
  ORDER BY processed_at DESC
  LIMIT 5
")
print(ch_preview)

# STEP 7: Print the Go-Ahead ----

cat("\n")
cat(paste(rep("=", 70), collapse = ""), "\n", sep = "")
cat("If both connections have been established, then\n")
cat("open 'lab4_analytics_with_odbc.qmd' to review the analytics notebook.\n")
cat(paste(rep("=", 70), collapse = ""), "\n", sep = "")
