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
# CORE LOGIC (TESTABLE)
# -----------------------------------------------------------------------------

def save_order_to_db(session, order_data):
    """
    Save an order to the database by creating a new order record and committing it.

    This function takes a database session and 'order' data, creates a new order
    record using the provided data, adds it to the session, and commits the
    transaction to persist the data in the database.

    :param session: SQLAlchemy session used for the transaction.
    :param order_data: Dictionary containing order_id, client_fname, item, etc.
    :return: Newly created and committed Order object.
    """
    order_record = Order(
        order_id=order_data['order_id'],
        client_fname=order_data['client_fname'],
        item=order_data['item'],
        order_quantity=order_data['order_quantity']
    )
    session.add(order_record)
    session.commit()
    return order_record


# -----------------------------------------------------------------------------
# MAIN EXECUTION LOOP
# -----------------------------------------------------------------------------

def main():
    # Fetch configuration from environment
    DATABASE_URL = os.environ.get('DATABASE_URL')
    BOOTSTRAP_SERVERS = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')
    TIMEZONE_NAME = os.environ.get('TIMEZONE', 'Africa/Lagos')

    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set.")

    # Initialize Database Engine
    engine = create_engine(DATABASE_URL)

    # Safety net: Ensure tables are created if they do not exist.
    Base.metadata.create_all(engine)

    # Kafka Consumer Configuration
    consumer_config = {
        "bootstrap.servers": BOOTSTRAP_SERVERS,
        "group.id": "order-inventories",
        "auto.offset.reset": "earliest",
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
                print(f"❌ Kafka Error: {msg.error()}")
                continue

            # Convert raw Kafka bytes to a Python dictionary
            try:
                order_data = json.loads(msg.value().decode("utf-8"))
            except json.JSONDecodeError as e:
                print(f"❌ JSON Decode Error: {e}")
                continue

            #  PERSIST TO POSTGRESQL
            try:
                with Session(engine) as session:
                    order_record = save_order_to_db(session, order_data)

                    print(
                        f"📦 Inventory updated\n"
                        f"    Order ID    : {order_data['order_id']}\n"
                        f"    Deducted    : {order_data['order_quantity']} x {order_data['item']}\n"
                        f"    Received at : {order_record.received_at}  ← Lagos time (WAT)\n"
                        f"    Saved to    : PostgreSQL (orders table)\n"
                        f"    Partition   : {msg.partition()}\n"
                    )

            except Exception as db_error:
                # Guard against duplicate inserts (IntegrityError) from at-least-once delivery
                print(f"⚠️  Could not save order {order_data.get('order_id', 'Unknown')}: {db_error}")

    except KeyboardInterrupt:
        print("\nStopping Order Inventory Service...")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()