# -----------------------------------------------------------------------------
# ORDER INVENTORY SERVICE
# -----------------------------------------------------------------------------
# This service listens for new orders and persists each one to PostgreSQL.
# It represents the Inventory Service in a microservices architecture —
# responsible for deducting stock and maintaining a record of all orders.
#
# This service introduces two concepts not present in Part 1:
#   1. Reading configuration from environment variables (DATABASE_URL)
#   2. Persisting Kafka messages to a relational database using SQLAlchemy
#
# NOTE: This file intentionally shares the same consumer setup structure as
# consumer_order_notification.py. In a production codebase, the shared setup
# would be extracted into a shared library. The files are kept separate here
# so that each service is self-contained and easy to follow independently.
# -----------------------------------------------------------------------------
# TIMEZONE CONTEXT:
#   This service runs on West Africa Time (WAT = UTC+1).
#   The received_at timestamp recorded in PostgreSQL reflects the moment
#   this service consumed the Kafka message — expressed in Lagos local time.
#
#   TEACHING POINT — This received_at value (Lagos WAT) is what Debezium
#   captures and forwards to the Transformer. The Transformer then converts
#   it to Nairobi time (EAT = UTC+3), producing a timestamp that appears
#   2 hours later. Students should verify this by querying both databases.
# -----------------------------------------------------------------------------
import os
import time
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from confluent_kafka import Consumer
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import Order, Base

# -----------------------------------------------------------------------------
# DATABASE SETUP
# -----------------------------------------------------------------------------

DATABASE_URL     = os.environ.get('DATABASE_URL')
BOOTSTRAP_SERVERS = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

# Lagos, Nigeria — WAT (UTC+1)
TIMEZONE_NAME = os.environ.get('TIMEZONE', 'Africa/Lagos')
TZ = ZoneInfo(TIMEZONE_NAME)

# create_engine() establishes the connection configuration to PostgreSQL.
# No actual connection is made yet — SQLAlchemy connects lazily when needed.
engine = create_engine(DATABASE_URL)

# create_all() inspects the database and creates any tables defined in our
# models that do not already exist. Since init.sql already created the
# "orders" table, this call is a no-op. It acts as a safety net in case
# the database was started without the init.sql script.
Base.metadata.create_all(engine)

# -----------------------------------------------------------------------------
# KAFKA CONSUMER SETUP
# -----------------------------------------------------------------------------

consumer_config = {
    "bootstrap.servers": BOOTSTRAP_SERVERS,

    # A separate consumer group from the Notification Service.
    # Both groups receive every message from the broker independently.
    "group.id": "order-inventory",

    "auto.offset.reset": "earliest",

    # Offsets are committed automatically every 5 seconds (the default).
    # This means at-least-once delivery: if this service crashes between
    # consuming a message and the next auto-commit, that message will be
    # re-consumed on restart. For an inventory system, this means you must
    # guard against duplicate inserts (the primary key on order_id handles
    # this here — a duplicate insert will raise an IntegrityError).
    "enable.auto.commit": True
}

consumer = Consumer(consumer_config)
consumer.subscribe(["orders"])

print("Waiting for the Kafka cluster and database to stabilize...")
time.sleep(10)

print("-" * 75)
print(f"Order Inventory Service is running  [Timezone: {TIMEZONE_NAME}]")
print(f"Connected to brokers  : {BOOTSTRAP_SERVERS}")
print(f"Connected to database : {DATABASE_URL}")
print("-" * 75)

try:
    while True:
        msg = consumer.poll(1.0)

        if msg is None:
            continue
        if msg.error():
            print(f"❌ Error: {msg.error()}")
            continue

        order_data = json.loads(msg.value().decode("utf-8"))

        # ---------------------------------------------------------------------
        # PERSIST TO POSTGRESQL
        # ---------------------------------------------------------------------
        # We open a new database session for each message.
        # The "with" statement (context manager) ensures the session is
        # automatically closed after the block — whether the insert succeeds
        # or raises an exception. This prevents connection leaks.
        #
        # session.commit() writes the record to the database permanently.
        # The insert exists only in memory until commit() is called.
        # ---------------------------------------------------------------------
        try:
            with Session(engine) as session:
                order_record = Order(
                    order_id       = order_data['order_id'],
                    client_fname   = order_data['client_fname'],
                    item           = order_data['item'],
                    order_quantity = order_data['order_quantity']
                )
                session.add(order_record)
                session.commit()

                print(
                    f"📦 Inventory updated\n"
                    f"    Order ID  : {order_data['order_id']}\n"
                    f"    Deducted    : {order_data['order_quantity']} x {order_data['item']}\n"
                    f"    Received at : {order_record.received_at}  ← Lagos time (WAT)\n"
                    f"    Saved to    : PostgreSQL (orders table)\n"
                    f"    Partition   : {msg.partition()}\n"
                )

        except Exception as db_error:
            # If the order_id already exists (duplicate message due to
            # at-least-once delivery), the primary key constraint prevents
            # a duplicate row. We log the error and move on rather than
            # crashing the entire service.
            print(f"⚠️  Could not save order {order_data['order_id']}: {db_error}")

except KeyboardInterrupt:
    print("\nStopping Order Inventory Service...")
finally:
    consumer.close()