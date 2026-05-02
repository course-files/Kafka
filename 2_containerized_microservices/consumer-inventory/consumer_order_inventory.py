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

import os
import time
import json
from confluent_kafka import Consumer
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import Order, Base

# -----------------------------------------------------------------------------
# CORE LOGIC (TESTABLE USING PYTEST)
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
        order_id       = order_data['order_id'],
        client_fname   = order_data['client_fname'],
        item           = order_data['item'],
        order_quantity = order_data['order_quantity']
    )
    session.add(order_record)
    session.commit()
    return order_record

# -----------------------------------------------------------------------------
# MAIN EXECUTION LOOP
# -----------------------------------------------------------------------------

def main():
    # Configuration is fetched only when the service actually runs
    # We read the connection string and broker locations from environment variables.
    DATABASE_URL = os.environ.get('DATABASE_URL')
    BOOTSTRAP_SERVERS = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set.")

    # Initialize Engine and Tables
    # create_engine() establishes the connection configuration to PostgreSQL.
    # No actual connection is made yet at this point — SQLAlchemy connects 'lazily'
    # when needed.
    engine = create_engine(DATABASE_URL)

    # Safety net: Ensure tables are created if they do not exist.
    # create_all() inspects the database and creates any tables defined in our
    # models that do not already exist. Since init.sql already created the
    # "orders" table, this call acts as a safety net in case
    # the database was started without the init.sql script.
    Base.metadata.create_all(engine)

    # -----------------------------------------------------------------------------
    # KAFKA CONSUMER SETUP
    # -----------------------------------------------------------------------------
    consumer_config = {
        "bootstrap.servers": BOOTSTRAP_SERVERS,

        # A separate consumer group from the Notification Service.
        # Both groups receive every message from the broker independently.
        "group.id": "order-inventories",

        "auto.offset.reset": "earliest",

        # Offsets are committed automatically every 5 seconds (the default).
        # This means at-least-once delivery: if this service crashes between
        # consuming a message and the next auto-commit, that message will be
        # re-consumed on restart. For an inventory system, this means you must
        # guard against duplicate inserts (the primary key on order_id handles
        # this here — a duplicate insert will raise an IntegrityError).
        "enable.auto.commit": True
    }

    # Initialize the Kafka Consumer
    consumer = Consumer(consumer_config)
    consumer.subscribe(["orders"])

    print("Waiting for the Kafka cluster and database to stabilize...")
    time.sleep(10)

    print("-" * 75)
    print("Order Inventory Service is running. Subscribed to 'orders' topic.")
    print(f"Connected to brokers: {BOOTSTRAP_SERVERS}")
    print(f"Connected to database: {DATABASE_URL}")
    print("-" * 75)

    try:
        while True:
            # poll() asks for new messages (waits up to 1.0 second)
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                print(f"❌ Error: {msg.error()}")
                continue

            # Convert raw Kafka bytes to a Python dictionary
            order_data = json.loads(msg.value().decode("utf-8"))

            # ---------------------------------------------------------------------
            # PERSIST TO POSTGRESQL
            # ---------------------------------------------------------------------
            # We open a new database session for each message.
            # The "with" statement (context manager) ensures the session is
            # automatically closed after the block — whether the insert succeeds
            # or raises an exception. This prevents connection leaks.
            try:
                with Session(engine) as session:
                    # We pass the dictionary directly to our logic function.
                    save_order_to_db(session, order_data)

                    print(
                        f"📦 Inventory updated\n"
                        f"    Order ID  : {order_data['order_id']}\n"
                        f"    Deducted  : {order_data['order_quantity']} x {order_data['item']}\n"
                        f"    Saved to  : PostgreSQL (orders table)\n"
                        f"    Partition : {msg.partition()}\n"
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
        # Crucial for releasing resources and committing offsets before exit.
        consumer.close()

if __name__ == "__main__":
    main()