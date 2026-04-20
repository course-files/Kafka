# Part 4: Data Analytics using ClickHouse and R via ODBC

## Overview

In Parts 1 through 3 we built a complete data engineering pipeline:

```
Producer → Kafka → Consumers → PostgreSQL → Debezium → ClickHouse
```

In Part 4 we move from **data engineering** to **data analytics**. We will
use R to query the ClickHouse data warehouse and perform statistical analysis
on the orders data that the pipeline has been collecting.

We will also run the same analytical query on both PostgreSQL and ClickHouse
and measure the difference in performance. This is the practical justification
for the entire pipeline we have built — relational databases are optimised for
day-to-day operations, and columnar data warehouses are optimised for analytical
queries. The gap in performance we will observe is not incidental — it is
architectural.

In this lab, R does not connect to ClickHouse directly using an R package.
Instead, it uses:

-   **Database Interface (DBI)** → standard database interface in R
-   **Open Database Connectivity (ODBC)** → bridge between R and system drivers
-   **ClickHouse ODBC driver** → actual communication layer

This moves us closer to industry-standard production setups where data analysts use tools like R, Tableau, or Power BI to connect to enterprise data warehouses via ODBC/JDBC drivers.

--------------------------------------------------------------------------------

### Why R for Analytics?

R is the standard tool for statistical analysis in business and research. It
was built specifically for data manipulation, hypothesis testing, and
visualization — tasks that general-purpose languages like Python can perform
but for which R provides a more natural and expressive environment. For
Business IT students moving into data analyst or business intelligence roles,
R is an essential skill.

### OLTP vs OLAP — The Performance Argument

You have heard this distinction before in courses like BBT 3104: Advanced 
Database Systems. This lab makes it tangible.

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

## Step 1: Install Required R Packages

Open RStudio and run:

``` r
install.packages(c("DBI", "RPostgres", "odbc", "tidyverse", "scales", "bench"))
```

---

## Step 2: Install System Dependencies

### <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/linux/linux-original.svg" width="40" /> Linux (Ubuntu/Debian)

Install ODBC driver manager:

``` bash
sudo apt update
sudo apt install -y unixodbc unixodbc-dev
```

---

### <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/apple/apple-original.svg" width="40"/> macOS (Homebrew)

``` bash
brew install unixodbc
```

---

### <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/windows11/windows11-original.svg" width="40" /> Windows

Windows is shipped with ODBC already installed.

However, Windows only provides the ODBC framework, not the actual database
drivers.
You must install the **ClickHouse ODBC driver** as described in the next step for
all Operating Systems.

---

## Step 3: Install ClickHouse ODBC Driver

Download from official source:

<https://clickhouse.com/docs/en/interfaces/odbc>


This leads to [https://github.com/ClickHouse/clickhouse-odbc/releases/tag/v1.5.3.20260311](https://github.com/ClickHouse/clickhouse-odbc/releases/tag/v1.5.3.20260311).

The exact version used in this lab is **clickhouse-odbc version 1.5.3.20260311 for use with PowerBI**.

* For Windows download the `clickhouse-odbc-1.5.3.20260311-powerbi-win64.msi` file.
* For Linux download the `clickhouse-odbc-linux-Clang-UnixODBC-Release.zip` file.
* For macOS download the `clickhouse-odbc-macos-AppleClang-UnixODBC-Release.zip ` file.

---

## Step 4: Verify Driver Installation

Run the following in R:

``` r
library(odbc)
odbcListDrivers()
```

You should see an item like:

```         
ClickHouse ODBC Driver (Unicode)
```

If you do NOT see this, then:
* The driver is not installed correctly
* Stop and fix this before proceeding

---

## Step 5: Ensure Docker Services Are Running

Navigate into the Part 3 directory (`3_data_engineering`) first. All the 
commands below assume that you are inside the `3_data_engineering` directory.

Then:

```bash
# This is executed to create the required volume directories
chmod u+x project_setup.sh
sed -i 's/\r$//' project_setup.sh
./project_setup.sh
```

### Build the images and start all services

```bash
docker compose -f docker-compose.yaml up --build \
  --scale producer=1 \
  --scale consumer-notification=1 \
  --scale consumer-inventory=1
```

Give the containers in the stack a few minutes to be stable. Check
Docker Desktop for any container that did not start and start it manually
by running `docker start <container-name>` or clicking the "Start" button in
the Docker Desktop UI.

#### Register the Debezium Connector

This is the step that **activates CDC**. You are basically telling Debezium 
which database and table to monitor.

The documentation of the connector configuration is available [here](kafka-connect/connector-config.json_documented_version.md).

```bash
cd 3_data_engineering/
chmod u+x kafka-connect/register-connector.sh
sed -i 's/\r$//' register-connector.sh
./kafka-connect/register-connector.sh
```

Confirm that data is flowing through the pipeline:

**For PostgreSQL:**

```bash
docker exec -it postgres psql -U lab_user -d lab_db \
-c "SELECT COUNT(*) FROM orders;"
```

**For ClickHouse:**

```bash
docker exec -it clickhouse clickhouse-client --password lab_password \
  --query "SELECT COUNT(*) FROM orders;"
```
## Step 6: Generate Data

The performance difference between PostgreSQL and ClickHouse is only clearly
visible with a large dataset. The default lab data (a few hundred orders) will
not produce a meaningful gap.

Pause the producer container using Docker Desktop.

Then run the following script to insert 500,000 synthetic orders into both the
PostgreSQL (the operational data store) and ClickHouse (the analytical data 
store).

Run:

``` bash
pip install psycopg2-binary clickhouse-connect faker
cd ../4_data_analytics/
python generate_data.py
```

This will take approximately 2 to 4 minutes. You will see a progress report in 
the terminal. Do not proceed to R until this script completes.

---

## Step 7: Run Connection Script

Open RStudio and run the following script line by line.

```
connect_clickhouse.R
```

Part of the expected result:

* ✅ Successful connection to ClickHouse
* ✅ Successful connection to PostgreSQL
* ✅ Row counts displayed

---

### Common Problems and Fixes

#### Problem: "No ClickHouse ODBC driver found"

Cause: Driver not installed

Fix: Reinstall ClickHouse ODBC driver and then restart the R session

---

#### Problem: Connection fails

Check:

-   The PostgreSQL and ClickHouse Docker containers must be running
-   Port 8123 should be open and accessible via HTTP (ClickHouse's HTTP interface)

Test in browser:

[http://localhost:8123](http://localhost:8123)

---

#### Problem: Driver name mismatch

Sometimes the driver name differs slightly.

Run:

``` r
odbcListDrivers()
```

Then copy the exact driver name into your R script.

---

### Final Check

Before proceeding to the notebook:

-   R packages installed
-   ODBC driver installed
-   Driver visible in R
-   Docker running
-   Data generated
-   Script runs without error

If all are true, then proceed to: `lab4_analytics_with_odbc.Rmd`

## Step 8: Run the R Notebook
`lab4_analytics_with_odbc.Rmd` is an R Notebook — each code chunk can be run
independently by clicking the green arrow in the top right corner of the
chunk. Work through each chunk in order, reading the narrative text between
them carefully.

To render the full notebook as a PDF or HTML report, click Knit in the RStudio
toolbar.

---

## Step 9: Observe and Record the Benchmark Results

Pay close attention to the benchmark section. Record:

* The median query execution time on PostgreSQL
* The median query execution time on ClickHouse
* The speedup ratio

These numbers will vary depending on your machine, but ClickHouse should be 
substantially faster — typically 10× to 50× on a 500,000-row table. On a
production warehouse with billions of rows, this gap widens to several orders
of magnitude.
