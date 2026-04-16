# Part 3 — Kafka Data Pipeline: PostgreSQL to ClickHouse via Debezium CDC

## Overview

In Part 2 we built a containerized microservices architecture where a
producer published orders to Kafka and two consumers processed them —
one sending notifications, and the other persisting to PostgreSQL.

In Part 3 we will build a **data pipeline** on top of that foundation.
Using **Debezium Change Data Capture (CDC)**, you will stream every change made
to the PostgreSQL `orders` table into Kafka, transform the data, and
load it into a ClickHouse data warehouse in real time.

The architecture is shown below.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Docker Network                              │
│                                                                     │
│  ┌──────────┐   orders    ┌───────────────────────────────────────┐ │
│  │ producer │────────────▶│         Kafka Cluster                 │ │
│  └──────────┘   topic     │   kafka1  │  kafka2  │  kafka3        │ │
│                           └───────────────────────────────────────┘ │
│                                   │                    │            │
│                    ┌──────────────┘                    │            │
│                    ▼                                   ▼            │
│           ┌────────────────┐              ┌────────────────────┐    │
│           │ consumer-      │              │ consumer-          │    │
│           │ notification   │              │ inventory          │    │
│           └────────────────┘              └─────────┬──────────┘    │
│                                                     │               │
│                                                     ▼               │
│                                            ┌─────────────────┐      │
│                                            │   PostgreSQL    │      │
│                                            │ (orders table)  │      │
│                                            └────────┬────────┘      │
│                                                     │               │
│                                            WAL logical stream       │
│                                                     │               │
│                                                     ▼               │
│                                            ┌─────────────────┐      │
│                                            │  Kafka Connect  │      │
│                                            │  + Debezium     │      │
│                                            │  (CDC engine)   │      │
│                                            └────────┬────────┘      │
│                                                     │               │
│                                   dbserver1.public.orders topic     │
│                                                     │               │
│                                                     ▼               │
│                                            ┌─────────────────┐      │
│                                            │  Transformer    │      │
│                                            │  Service        │      │
│                                            │  (Python)       │      │
│                                            └────────┬────────┘      │
│                                                     │               │
│                                                     ▼               │
│                                            ┌─────────────────┐      │
│                                            │   ClickHouse    │      │
│                                            │ (data warehouse)│      │
│                                            └─────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## New Concepts in This Lab

### Change Data Capture (CDC)

In Part 2, the Inventory Service wrote orders to PostgreSQL directly.
But what if you have an existing application that writes to a database
and you cannot modify its code? CDC solves this.

Instead of changing the application, CDC taps into the database's
internal change log — the **Write-Ahead Log (WAL)** — and streams
every INSERT, UPDATE, and DELETE as an event to Kafka. The application
never knows CDC is running.

This is how large-scale data pipelines are built in practice: you
capture change at the database level, not at the application level.

### Debezium

Debezium is a CDC platform that runs as a **Kafka Connect** plugin.
It connects to PostgreSQL as a replication client, reads the WAL, and
publishes every change as a structured JSON event to a Kafka topic.

Each Debezium event has this structure:

```json
{
  "payload": {
    "before": null,
    "after": {
      "order_id": "abc-123",
      "client_fname": "Jeff",
      "item": "Managu",
      "order_quantity": 3,
      "received_at": 1714000000000000
    },
    "op": "c"
  }
}
```

The `op` field tells you what kind of change occurred:

| `op` | Meaning                                              |
|------|------------------------------------------------------|
| `r`  | Snapshot read — existing row read at connector start |
| `c`  | Create — a new row was INSERTED                      |
| `u`  | Update — an existing row was UPDATED                 |
| `d`  | Delete — a row was DELETED                           |

### ClickHouse

ClickHouse is a **columnar** database built for analytical queries.

| Feature        | PostgreSQL (row store)       | ClickHouse (column store)          |
|----------------|------------------------------|------------------------------------|
| Storage layout | One row stored together      | One column stored together         |
| Best for       | INSERT / SELECT single rows  | Aggregations over millions of rows |
| Use case       | Transactional systems (OLTP) | Analytics and reporting (OLAP)     |
| Example query  | "Fetch order #1234"          | "Total revenue by item this month" |

In a production data platform, PostgreSQL holds the live operational
data and ClickHouse holds the historical analytical data for dashboards
and reports.

### The Transformation Step

Raw Debezium events reflect the source database schema exactly. A
transformation step exists to:

- **Rename fields** to match the warehouse naming convention
- **Compute derived fields** that would be expensive to recalculate at query time
- **Convert data types** (e.g., microsecond timestamps to datetime objects)
- **Filter events** that should not enter the warehouse, e.g.,
removing Personally Identifiable Information (PII) to comply with privacy 
regulations in the **Kenya Data Protection Act**.
- **Enrich records** with metadata that the source system does not store

etc.

In `transformer.py`, the following transformations are applied:

| Transformation    | Source value                       | Warehouse value                |
|-------------------|------------------------------------|--------------------------------|
| Field rename      | `client_fname`                     | `customer_name`                |
| Computed field    | `order_quantity`                   | `is_bulk_order` (qty > 5)      |
| Timestamp         | Microseconds since epoch (integer) | Python `datetime` object       |
| Added audit field | —                                  | `processed_at` (pipeline time) |
| Added audit field | `op` code                          | `operation` (readable label)   |
| Filter            | `op = "d"` (DELETE)                | Skipped entirely               |

---

## Step-by-Step Instructions

### Prerequisites

Ensure you have completed Part 2 and understand the producer, consumer,
and broker concepts first because Part 3 of the lab builds directly on top of
the concepts in Part 2.

---

### Step 1 — Set Up Directories and Start the Stack

```bash
# Create the required volume directories
chmod u+x project_setup.sh
sed -i.bak 's/\r$//' project_setup.sh
./project_setup.sh

# Build all images and start all services
# docker-compose up --build
docker compose -f docker-compose.yaml up --build \
  --scale producer=1 \
  --scale consumer-notification=1 \
  --scale consumer-inventory=1
```

This will start:
- 3 Kafka brokers (`kafka1`, `kafka2`, `kafka3`)
- 1 PostgreSQL container
- 1 Kafka Connect container with Debezium
- 1 ClickHouse container
- 1 producer service
- 1 notification consumer service
- 1 inventory consumer service
- 1 transformer service

Wait until all containers are running and healthy before proceeding.
You can check their status with:

```bash
docker-compose ps
```

All services should show `healthy` or `running`. The Kafka Connect
container (`kafka-connect`) takes approximately 60 seconds to fully
initialize. Wait until it shows `healthy` before moving to Step 2.

---

### Step 2 — Verify the Stack is Healthy

**Check that Kafka brokers are up:**
```bash
docker exec kafka1 kafka-topics \
  --bootstrap-server localhost:9092 \
  --list
```

**Check that PostgreSQL is receiving orders:**
```bash
docker exec -it postgres psql -U lab_user -d lab_db \
  -c "SELECT * FROM orders ORDER BY received_at DESC LIMIT 5;"
```

**Check that Kafka Connect is ready:**
```bash
curl http://localhost:8083/
```

You should see a JSON response showing the Kafka Connect version.
If you receive a connection error, wait 30 more seconds and try again.

---

### Step 3 — Register the Debezium Connector

This is the step that activates CDC. You are telling Debezium which
database and table to monitor.

```bash
cd 3_data_engineering/
chmod u+x kafka-connect/register-connector.sh
sed -i.bak 's/\r$//' register-connector.sh
./kafka-connect/register-connector.sh
```

Expected output:
```
Waiting for Kafka Connect to be ready...
Kafka Connect is ready.

Registering Debezium PostgreSQL connector...
✅ Connector registered successfully (HTTP 201).

You can verify the connector status with:
  curl http://localhost:8083/connectors/orders-postgres-connector/status
```

**What the connector configuration does (connector-config.json):**

| Field                                       | Value             | Purpose                                                                              |
|---------------------------------------------|-------------------|--------------------------------------------------------------------------------------|
| `connector.class`                           | PostgresConnector | Uses the Debezium PostgreSQL connector                                               |
| `database.hostname`                         | postgres          | Docker service name of the PostgreSQL container                                      |
| `topic.prefix`                              | dbserver1         | Prefix for all Kafka topics this connector creates                                   |
| `table.include.list`                        | public.orders     | Only monitor this table (schema.table format)                                        |
| `plugin.name`                               | pgoutput          | Uses PostgreSQL's built-in logical decoding plugin (no extra installation needed)    |
| `slot.name`                                 | debezium_slot     | The replication slot Debezium creates in PostgreSQL to track its position in the WAL |
| `publication.autocleanup.on.connector.stop` | true              | Cleans up the PostgreSQL replication slot when the connector is stopped              |
| `snapshot.mode`                             | initial           | Read all existing rows first, then switch to live CDC                                |

**Verify the connector is running:**
```bash
curl http://localhost:8083/connectors/orders-postgres-connector/status
```

The `state` field should show `RUNNING`.

---

### Step 4 — Verify the Debezium Topic Exists

Once the connector is registered, Debezium creates a new Kafka topic
named `dbserver1.public.orders` and immediately begins publishing
snapshot events for all existing rows in the PostgreSQL orders table.

```bash
# List all topics — you should now see dbserver1.public.orders
docker exec kafka1 kafka-topics \
  --bootstrap-server localhost:9092 \
  --list

# Inspect the CDC topic — notice that it has 3 partitions and 3 replicas
docker exec kafka1 kafka-topics \
  --bootstrap-server localhost:9092 \
  --describe --topic dbserver1.public.orders

# Consume raw events from the CDC topic to see the Debezium format
docker exec kafka1 kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic dbserver1.public.orders \
  --from-beginning \
  --max-messages 3
```

Read the raw JSON output carefully. Identify the `payload.op`,
`payload.before`, and `payload.after` fields. This is the exact input
that `transformer.py` receives and processes.

---

### Step 5 — Verify Data is Arriving in ClickHouse

The transformer service is already running as a Docker container. Check
its logs to see it consuming CDC events and writing to ClickHouse:

```bash
docker-compose logs transformer
```

Then query ClickHouse directly to see the transformed data:

```bash
# Connect to ClickHouse using the CLI
docker exec -it clickhouse clickhouse-client

# Once inside the CLI, run these queries:

-- Count total orders in the warehouse
SELECT count() FROM orders;

-- View all orders
SELECT * FROM orders ORDER BY processed_at DESC LIMIT 10;

-- See the effect of the is_bulk_order field
SELECT
    is_bulk_order,
    count()        AS order_count,
    sum(order_quantity) AS total_units
FROM orders
GROUP BY is_bulk_order;

-- Compare received_at and processed_at to measure pipeline latency
SELECT
    order_id,
    received_at,
    processed_at,
    dateDiff('second', received_at, processed_at) AS latency_seconds
FROM orders
ORDER BY processed_at DESC
LIMIT 10;

-- Exit the CLI
exit;
```

---

### Step 6 — Observe the Live Pipeline

At this point the full pipeline is running continuously. Open three
terminal windows and run the following simultaneously to observe the
end-to-end flow in real time.

**Terminal 1 — Watch new orders arrive in PostgreSQL:**
```bash
watch -n 2 "docker exec postgres psql -U lab_user -d lab_db \
  -c 'SELECT order_id, item, order_quantity, received_at FROM orders \
  ORDER BY received_at DESC LIMIT 5;'"
```

**Terminal 2 — Watch the transformer processing CDC events:**
```bash
docker-compose logs -f transformer
```

**Terminal 3 — Watch ClickHouse receiving transformed records:**
```bash
watch -n 2 "docker exec clickhouse clickhouse-client \
  --query 'SELECT order_id, customer_name, item, is_bulk_order, operation \
  FROM orders ORDER BY processed_at DESC LIMIT 5'"
```

You will see rows appearing in PostgreSQL and then — within seconds —
appearing in ClickHouse with the applied transformations. The
`customer_name` column will contain the renamed value and `is_bulk_order`
will be set automatically based on the quantity.

---

### Step 7 — Observe CDC Operations (INSERT, UPDATE, DELETE)

The producer only ever inserts new orders. To observe UPDATE and DELETE
events flowing through the pipeline, run these commands manually.

**Trigger an UPDATE:**
```bash
docker exec -it postgres psql -U lab_user -d lab_db -c "
UPDATE orders
SET order_quantity = 99
WHERE order_id = (SELECT order_id FROM orders LIMIT 1);
"
```

Watch the transformer logs — you will see an event with
`operation: UPDATE`. Then query ClickHouse to see the updated record.

**Trigger a DELETE:**
```bash
docker exec -it postgres psql -U lab_user -d lab_db -c "
DELETE FROM orders
WHERE order_id = (SELECT order_id FROM orders LIMIT 1);
"
```

Watch the transformer logs — you will see `Skipping DELETE event`.
The record will remain in ClickHouse because the transformer filters
out DELETE operations by design. This demonstrates an intentional
architectural decision: the warehouse retains historical data even
when the source database removes it.

---

### Step 8 — Tear Down

```bash
# Stop all services but retain volume data
docker-compose down

# Stop all services AND delete all stored data
docker-compose down -v
```

```bash
chmod u+x project_cleanup.sh
sed -i.bak 's/\r$//' project_cleanup.sh
./project_cleanup.sh
```
---
