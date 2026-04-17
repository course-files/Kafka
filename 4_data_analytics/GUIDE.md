# Part 4 — Data Analytics with R and ClickHouse

## Overview

In Parts 1 through 3 you built a complete data engineering pipeline:

```
Producer → Kafka → Consumers → PostgreSQL → Debezium → ClickHouse
```

In Part 4 you move from **data engineering** to **data analytics**. You will
use R to query the ClickHouse data warehouse and perform statistical analysis
on the orders data your pipeline has been collecting.

You will also run the same analytical query on both PostgreSQL and ClickHouse
and measure the difference in performance. This is the practical justification
for the entire pipeline you have built — relational databases are optimised for
day-to-day operations, and columnar warehouses are optimised for analytical
queries. The gap in performance you will observe is not incidental — it is
architectural.

---

## New Concepts in This Lab

### Why R for Analytics?

R is the standard tool for statistical analysis in business and research. It
was built specifically for data manipulation, hypothesis testing, and
visualisation — tasks that general-purpose languages like Python can perform
but for which R provides a more natural and expressive environment. For
Business IT students moving into data analyst or business intelligence roles,
R is an essential skill.

### OLTP vs OLAP — The Performance Argument

You have heard this distinction before. This lab makes it tangible.

| Characteristic     | PostgreSQL (OLTP)           | ClickHouse (OLAP)              |
|--------------------|-----------------------------|--------------------------------|
| Storage layout     | Row-by-row                  | Column-by-column               |
| Best query type    | `SELECT * WHERE id = 123`   | `SELECT SUM(...) GROUP BY ...` |
| Optimised for      | Low-latency single records  | High-throughput aggregations   |
| Index strategy     | B-tree on primary key       | Column compression + skipping  |
| Concurrent writes  | Yes — designed for it       | Batch inserts preferred        |

When you run `SELECT SUM(order_quantity) FROM orders GROUP BY item`, PostgreSQL
must read every row, load all columns into memory, and then aggregate. ClickHouse
stores the `order_quantity` and `item` columns separately on disk — it reads
only those two columns, skipping every other column entirely. On a large table
this difference is dramatic.

---

## Directory Structure

```
lab4/
├── GUIDE.md
├── generate_data.py          ← Generates 500,000 orders for the benchmark
└── r/
    ├── connect_clickhouse.R  ← Connection setup and verification
    └── lab4_analytics.Rmd   ← R Notebook: analytics and benchmark
```

---

## Prerequisites

### Step 1 — Ensure the Part 3 Stack is Running

Part 4 connects to the ClickHouse and PostgreSQL containers from Part 3.
The stack must be running before you open R.

```bash
cd lab3
docker compose up -d
```

Verify both databases are accessible:

```bash
# PostgreSQL
docker exec -it postgres psql -U lab_user -d lab_db -c "SELECT COUNT(*) FROM orders;"

# ClickHouse
docker exec -it clickhouse clickhouse-client --password lab_password \
  --query "SELECT COUNT(*) FROM orders;"
```

### Step 2 — Install R and RStudio

Download R from https://cran.r-project.org and RStudio from https://posit.co/downloads.
Both are free and available for Windows, macOS, and Linux.

### Step 3 — Generate Benchmark Data

The performance difference between PostgreSQL and ClickHouse is only clearly
visible with a large dataset. The default lab data (a few hundred orders) will
not produce a meaningful gap. Run the following script to insert 500,000
synthetic orders into both databases before opening R.

```bash
pip install psycopg2-binary clickhouse-connect faker
python generate_data.py
```

This will take approximately 2 to 4 minutes. You will see a progress report
in the terminal. Do not proceed to R until this script completes.

### Step 4 — Install R Packages

Open RStudio and run the following in the Console panel once:

```r
install.packages(c(
  "DBI",          # Standard R database interface
  "RPostgres",    # PostgreSQL driver
  # "clickhouse",   # ClickHouse driver (uses HTTP interface on port 8123)
  "tidyverse",    # Data manipulation and ggplot2 visualisation
  "scales",       # Axis formatting helpers for ggplot2
  "knitr",        # R Notebook rendering
  "bench"         # Precise benchmarking with statistical summaries
))
```

---

## Step-by-Step Instructions

### Step 5 — Run `connect_clickhouse.R`

Open `r/connect_clickhouse.R` in RStudio and run it line by line. This file
verifies that both database connections work before you open the notebook.
If either connection fails, resolve it here before proceeding.

### Step 6 — Open and Run `lab4_analytics.Rmd`

Open `r/lab4_analytics.Rmd` in RStudio. This is an R Notebook — each code
chunk can be run independently by clicking the green arrow in the top right
corner of the chunk. Work through each chunk in order, reading the narrative
text between them carefully.

To render the full notebook as an HTML report, click **Knit** in the RStudio
toolbar.

### Step 7 — Observe and Record the Benchmark Results

Pay close attention to the benchmark section. Record:
- The median query execution time on PostgreSQL
- The median query execution time on ClickHouse
- The speedup ratio

These numbers will vary depending on your machine, but ClickHouse should be
substantially faster — typically 10× to 50× on a 500,000-row table. On a
production warehouse with billions of rows, this gap widens to several orders
of magnitude.

---

## Exercises

1. Modify the aggregation query to group by `customer_name` instead of `item`.
   Which customer has placed the highest total quantity of orders? Run this on
   both databases and record the times.

2. Add a filter to the ClickHouse query: `WHERE is_bulk_order = 1`. How does
   filtering on a computed column affect performance compared to the unfiltered
   query?

3. Write a ClickHouse query that computes the average `order_quantity` per item
   for each operation type (INSERT, UPDATE, SNAPSHOT). What does this tell you
   about the data distribution?

4. The `processed_at - received_at` gap represents pipeline latency. Write an R
   query that computes the average latency in seconds for each item. Which item
   has the highest average latency and why might that be?

5. Using the benchmark results, extrapolate: if the 500,000-row query takes X
   seconds on PostgreSQL, approximately how long would a 50,000,000-row query
   take? Is PostgreSQL a viable tool for that scale of analytics?
