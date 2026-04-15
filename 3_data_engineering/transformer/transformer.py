# -----------------------------------------------------------------------------
# TRANSFORMER SERVICE — CDC CONSUMER AND DATA WAREHOUSE WRITER
# -----------------------------------------------------------------------------
# This service sits at the centre of the Lab 3 data pipeline.
#
# DATA FLOW:
#
#   PostgreSQL (orders table)
#       ↓ Debezium reads the WAL stream
#   Kafka Topic: dbserver1.public.orders
#       ↓ This service consumes events from that topic
#   TRANSFORMATION (see transform_order() below)
#       ↓ Cleaned and enriched records
#   ClickHouse (orders table)
#
# DEBEZIUM EVENT FORMAT:
#   Debezium does not publish raw rows to Kafka. It publishes change
#   events — structured messages that describe WHAT changed and HOW.
#   Each event has this structure:
#
#   {
#     "payload": {
#       "before": { ...old row... } or null,
#       "after":  { ...new row... } or null,
#       "op":     "c" (insert), "u" (update), "d" (delete), "r" (snapshot read)
#     }
#   }
#
#   "op" values explained:
#     "r" — Snapshot read. Debezium first reads all existing rows in the
#            table before switching to live CDC mode. These "r" events
#            represent the initial state of the table.
#     "c" — Create (INSERT). A new row was inserted into PostgreSQL.
#     "u" — Update. An existing row was modified.
#     "d" — Delete. A row was deleted. "after" will be null.
#
# TRANSFORMATIONS APPLIED (see transform_order()):
#   1. Field rename   : client_fname  → customer_name
#   2. Computed field : is_bulk_order (True if order_quantity > 5)
#   3. Timestamp      : received_at converted from microseconds to datetime
#   4. Audit field    : processed_at added (time this service ran the transform)
#   5. Audit field    : operation added (INSERT, UPDATE, SNAPSHOT)
#   6. Filter         : DELETE events are skipped — the warehouse is append-only
# -----------------------------------------------------------------------------

import os
import json
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from confluent_kafka import Consumer, KafkaError
import clickhouse_connect

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------

BOOTSTRAP_SERVERS  = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')
CLICKHOUSE_HOST    = os.environ.get('CLICKHOUSE_HOST', 'localhost')
CLICKHOUSE_PORT    = int(os.environ.get('CLICKHOUSE_PORT', 8123))
CLICKHOUSE_PASSWORD = os.environ.get('CLICKHOUSE_PASSWORD', 'lab_password')

# Read the timezone from the environment variable set in docker-compose.yaml.
# ZoneInfo looks up the IANA timezone database (e.g., "Africa/Nairobi").
# This is the same timezone database that operating systems use.
# Changing the timezone only requires updating the .env file and restarting
# the container — no code changes or rebuilds are needed.
TIMEZONE_NAME = os.environ.get('TIMEZONE', 'Africa/Nairobi')
TZ = ZoneInfo(TIMEZONE_NAME)

# The Debezium connector publishes to a topic named using the pattern:
#   {topic.prefix}.{schema}.{table}
# Our connector-config.json sets topic.prefix=dbserver1,
# and we monitor the public.orders table.
DEBEZIUM_TOPIC = 'dbserver1.public.orders'

# Map Debezium operation codes to human-readable labels.
OPERATION_MAP = {
    'r': 'SNAPSHOT',
    'c': 'INSERT',
    'u': 'UPDATE',
    'd': 'DELETE'
}

# -----------------------------------------------------------------------------
# TRANSFORMATION LOGIC
# -----------------------------------------------------------------------------

def transform_order(payload: dict) -> dict | None:
    """
    Receives a Debezium change event payload and returns a transformed
    dictionary ready to be written to ClickHouse, or None if the event
    should be skipped.

    Parameters:
        payload (dict): The Debezium event payload containing
                        "before", "after", and "op" fields.

    Returns:
        dict | None: Transformed record, or None for events to skip.
    """

    operation_code = payload.get('op')
    operation      = OPERATION_MAP.get(operation_code, 'UNKNOWN')

    # -------------------------------------------------------------------------
    # FILTER: Skip DELETE events.
    # -------------------------------------------------------------------------
    # In this warehouse, we treat the orders table as append-only.
    # A deleted order in PostgreSQL should not disappear from the
    # warehouse — the warehouse is a historical record.
    # In a production system, you might instead set a "deleted" flag.
    if operation_code == 'd':
        print(f"⏭️  Skipping DELETE event for order. "
              f"The warehouse retains historical records.")
        return None

    # For INSERT, UPDATE, and SNAPSHOT events, the row data is in "after".
    row = payload.get('after')
    if row is None:
        print("⚠️  Received event with no 'after' payload. Skipping.")
        return None

    # -------------------------------------------------------------------------
    # TRANSFORMATION 1: Timestamp conversion.
    # -------------------------------------------------------------------------
    # Debezium captures PostgreSQL TIMESTAMP columns as microseconds since
    # the Unix epoch (1970-01-01 00:00:00 UTC). We first reconstruct the
    # UTC moment, then convert it to Africa/Nairobi time so that all
    # timestamps stored in ClickHouse reflect the local business timezone.
    received_at_us = row.get('received_at', 0)
    # received_at = datetime.datetime.fromtimestamp(
    received_at = datetime.fromtimestamp(
        received_at_us / 1_000_000,
        tz=timezone.utc  # start from the correct UTC moment
    ).astimezone(TZ)  # then convert to Africa/Nairobi

    # -------------------------------------------------------------------------
    # TRANSFORMATION 2: Field rename.
    # -------------------------------------------------------------------------
    # In PostgreSQL the column is named client_fname (a legacy name).
    # In the warehouse we use customer_name (a cleaner, more descriptive name).
    # Renaming during the transformation step means the warehouse schema
    # can evolve independently of the source schema.
    customer_name = row.get('client_fname', '')

    # -------------------------------------------------------------------------
    # TRANSFORMATION 3: Computed field — is_bulk_order.
    # -------------------------------------------------------------------------
    # A business rule: any order for more than 5 units is classified as a
    # bulk order. This classification is not stored in PostgreSQL — it is
    # derived during the transformation and stored in the warehouse.
    # Storing derived fields in the warehouse avoids recalculating them
    # at query time, which improves dashboard performance.
    order_quantity = row.get('order_quantity', 0)
    is_bulk_order  = 1 if order_quantity > 5 else 0

    # -------------------------------------------------------------------------
    # TRANSFORMATION 4: Audit fields.
    # -------------------------------------------------------------------------
    # processed_at records the exact moment this transformer processed
    # the event. This is different from received_at (when the order entered
    # PostgreSQL). The gap between the two is the pipeline latency —
    # a useful metric in a production system.
    processed_at = datetime.now(tz=timezone.utc)

    return {
        'order_id':      row.get('order_id', ''),
        'customer_name': customer_name,
        'item':          row.get('item', ''),
        'order_quantity': order_quantity,
        'is_bulk_order': is_bulk_order,
        'received_at':   received_at,
        'processed_at':  processed_at,
        'operation':     operation
    }

# -----------------------------------------------------------------------------
# CLICKHOUSE CONNECTION
# -----------------------------------------------------------------------------

def connect_to_clickhouse():
    """
    Establishes a connection to ClickHouse and returns the client.
    Retries with a delay to handle cases where ClickHouse is still
    starting up when this service initialises.
    """
    while True:
        try:
            client = clickhouse_connect.get_client(
                host=CLICKHOUSE_HOST,
                port=CLICKHOUSE_PORT,
                username='default',
                password=CLICKHOUSE_PASSWORD,
                database='default'
            )
            # Run a trivial query to verify the connection is alive.
            client.query('SELECT 1')
            print(f"✅ Connected to ClickHouse at {CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}")
            return client
        except Exception as e:
            print(f"⏳ ClickHouse not ready yet: {e}. Retrying in 5 seconds...")
            time.sleep(5)


def write_to_clickhouse(client, record: dict):
    """
    Writes a single transformed order record to the ClickHouse orders table.

    Parameters:
        client: An active clickhouse_connect client.
        record (dict): The transformed record from transform_order().
    """
    client.insert(
        table='orders',
        data=[[
            record['order_id'],
            record['customer_name'],
            record['item'],
            record['order_quantity'],
            record['is_bulk_order'],
            record['received_at'],
            record['processed_at'],
            record['operation']
        ]],
        column_names=[
            'order_id',
            'customer_name',
            'item',
            'order_quantity',
            'is_bulk_order',
            'received_at',
            'processed_at',
            'operation'
        ]
    )

# -----------------------------------------------------------------------------
# KAFKA CONSUMER SETUP
# -----------------------------------------------------------------------------

consumer_config = {
    'bootstrap.servers': BOOTSTRAP_SERVERS,

    # A unique consumer group for this service.
    # Debezium publishes to dbserver1.public.orders as a normal Kafka topic.
    # This consumer group reads those events independently of any other
    # consumer groups that might also subscribe to the same topic.
    'group.id': 'warehouse-transformer',

    # "earliest" ensures the transformer reads all events from the beginning
    # of the topic, including the initial snapshot events that Debezium
    # publishes when the connector first starts.
    'auto.offset.reset': 'earliest',

    'enable.auto.commit': True
}

# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------

print("Waiting for the Kafka cluster and ClickHouse to stabilize...")
time.sleep(15)

clickhouse_client = connect_to_clickhouse()

consumer = Consumer(consumer_config)
consumer.subscribe([DEBEZIUM_TOPIC])

print("-" * 75)
print("Transformer Service is running.")
print(f"Consuming from Kafka topic : {DEBEZIUM_TOPIC}")
print(f"Writing to ClickHouse      : {CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}")
print("-" * 75)

try:
    while True:
        msg = consumer.poll(1.0)

        if msg is None:
            continue
        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                # End of partition — not an error. The consumer has
                # caught up with the current end of the topic.
                continue
            print(f"❌ Kafka error: {msg.error()}")
            continue

        # Parse the raw JSON message from Debezium.
        event = json.loads(msg.value().decode('utf-8'))

        # The actual change data is inside the "payload" key.
        payload = event.get('payload', {})

        # Apply all transformations. Returns None for events to skip.
        record = transform_order(payload)

        if record is None:
            continue

        try:
            write_to_clickhouse(clickhouse_client, record)
            print(
                f"🏭 Transformed and written to ClickHouse\n"
                f"   Order ID      : {record['order_id']}\n"
                f"   Customer      : {record['customer_name']}\n"
                f"   Item          : {record['order_quantity']} x {record['item']}\n"
                f"   Bulk order    : {'Yes' if record['is_bulk_order'] else 'No'}\n"
                f"   Operation     : {record['operation']}\n"
                f"   Received at   : {record['received_at']}\n"
                f"   Processed at  : {record['processed_at']}\n"
            )
        except Exception as e:
            print(f"⚠️  Failed to write to ClickHouse: {e}")

except KeyboardInterrupt:
    print("\nStopping Transformer Service...")
finally:
    consumer.close()