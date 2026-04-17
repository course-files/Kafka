# ClickHouse + R (ODBC) Setup Guide

## Purpose

This guide helps you prepare your system so that R can connect to: - ClickHouse
(data warehouse) - PostgreSQL (operational database)

You must complete this setup **before running the lab scripts**.

--------------------------------------------------------------------------------

## Big Picture

In this lab, R does not connect to ClickHouse directly using an R package.
Instead, it uses:

-   DBI → standard database interface in R
-   odbc → bridge between R and system drivers
-   ClickHouse ODBC driver → actual communication layer

This is how real systems are built in industry.

--------------------------------------------------------------------------------

## Step 1: Install Required R Packages

Open R or RStudio and run:

``` r
install.packages(c("DBI", "RPostgres", "odbc", "tidyverse", "scales", "bench"))
```

--------------------------------------------------------------------------------

## Step 2: Install System Dependencies

### Linux (Ubuntu/Debian)

Install ODBC driver manager:

``` bash
sudo apt update
sudo apt install -y unixodbc unixodbc-dev
```

--------------------------------------------------------------------------------

### macOS (Homebrew)

``` bash
brew install unixodbc
```

--------------------------------------------------------------------------------

## Step 3: Install ClickHouse ODBC Driver

Download from official source:

<https://clickhouse.com/docs/en/interfaces/odbc>

### Linux (Example .deb installation)

``` bash
sudo dpkg -i clickhouse-odbc*.deb
```

If dependencies fail:

``` bash
sudo apt --fix-broken install
```

--------------------------------------------------------------------------------

### macOS

Install the `.pkg` file and follow the installer.

--------------------------------------------------------------------------------

## Step 4: Verify Driver Installation

Open R and run:

``` r
library(odbc)
odbcListDrivers()
```

You should see something like:

```         
ClickHouse ODBC Driver (Unicode)
```

If you do NOT see this: - The driver is not installed correctly - Stop and fix
this before proceeding

--------------------------------------------------------------------------------

## Step 5: Ensure Docker Services Are Running

From your project folder:

``` bash
docker compose up -d
```

Check containers:

``` bash
docker ps
```

You should see: - ClickHouse container - PostgreSQL container

--------------------------------------------------------------------------------

## Step 6: Generate Data

Run:

``` bash
python generate_data.py
```

This populates both databases.

--------------------------------------------------------------------------------

## Step 7: Run Connection Script

Open RStudio and run:

```         
connect_clickhouse.R
```

Run **line by line**.

Expected result:

-   Successful connection to ClickHouse
-   Successful connection to PostgreSQL
-   Row counts displayed

--------------------------------------------------------------------------------

## Common Problems and Fixes

### Problem: "No ClickHouse ODBC driver found"

Cause: - Driver not installed

Fix: - Reinstall driver - Restart R session

--------------------------------------------------------------------------------

### Problem: Connection fails

Check:

-   Docker is running
-   Port 8123 is open

Test in browser:

```         
http://localhost:8123
```

--------------------------------------------------------------------------------

### Problem: Driver name mismatch

Sometimes the driver name differs slightly.

Run:

``` r
odbcListDrivers()
```

Then copy the exact name into your script.

--------------------------------------------------------------------------------

## What You Are Learning (Important)

This lab is not just about R.

You are learning:

-   How real systems connect to databases
-   Why abstraction layers matter
-   How analytical systems differ from operational systems

--------------------------------------------------------------------------------

## Rules for This Lab

1.  Do NOT skip steps
2.  Do NOT install random R packages for ClickHouse
3.  Use ODBC exactly as instructed
4.  Ask for help early if setup fails

--------------------------------------------------------------------------------

## Final Check

Before proceeding to the notebook:

-   R packages installed
-   ODBC driver installed
-   Driver visible in R
-   Docker running
-   Data generated
-   Script runs without error

If all are true, proceed to:

```         
lab4_analytics.Rmd
```

--------------------------------------------------------------------------------

## Final Note

This setup may feel heavier than usual R work. That is intentional.

You are working with a real analytical database system, not a classroom toy.
