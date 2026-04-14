# -----------------------------------------------------------------------------
# ORDER NOTIFICATION SERVICE
# -----------------------------------------------------------------------------
# This service listens for new orders and simulates sending a confirmation
# notification to the customer (e.g., an email or SMS).
#
# Changes from Part 1:
#   1. Bootstrap servers read from an environment variable
#   2. A short startup delay is added to allow the cluster to stabilize
#   3. The bootstrap.servers value now lists all 3 brokers by service name
# -----------------------------------------------------------------------------

import os
import time
import json
from confluent_kafka import Consumer

BOOTSTRAP_SERVERS = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

consumer_config = {
    "bootstrap.servers": BOOTSTRAP_SERVERS,

    # This consumer belongs to its own consumer group, separate from the
    # Inventory Service. Kafka delivers every message to every consumer
    # group independently. Both services receive every order — this is
    # the publish-subscribe pattern at work.
    "group.id": "order-notifiers",

    # "earliest" ensures this consumer reads all messages from the
    # beginning of the topic if it has no previously committed offset.
    # This prevents missed messages when the consumer starts after
    # the producer has already sent some orders.
    "auto.offset.reset": "earliest",

    # Kafka consumers automatically commit (save) their current offset to the
    # broker periodically. The offset records which messages the consumer has
    # already read, so that if the consumer restarts, it continues from where
    # it left off rather than re-reading all messages from the beginning.
    #
    # "enable.auto.commit" is True by default. We set it explicitly here so
    # that it is visible and not a hidden behavior.
    #
    # IMPORTANT: Auto-commit saves the offset on a time interval (every 5
    # seconds by default), NOT immediately after a message is processed.
    # This means if the consumer crashes between processing a message and
    # the next scheduled commit, that message will be processed again on
    # restart. This is known as "at-least-once delivery": every message is
    # guaranteed to be processed, but it may be processed more than once.
    "enable.auto.commit": True
}

consumer = Consumer(consumer_config)

consumer.subscribe(["orders"])

print("Waiting for the Kafka cluster to stabilize...")
time.sleep(10)

print("-" * 75)
print("Order Notification Service is running. Subscribed to 'orders' topic.")
print(f"Connected to brokers: {BOOTSTRAP_SERVERS}")
print("-" * 75)

try:
    while True:
        msg = consumer.poll(1.0)

        if msg is None:
            continue
        if msg.error():
            print(f"❌ Error: {msg.error()}")
            continue

        order = json.loads(msg.value().decode("utf-8"))

        # In a real Notification Service, this is where you would call an
        # email API (e.g., SendGrid) or an SMS gateway (e.g., Africa's Talking).
        print(
            f"📧 Notification sent\n"
            f"    To        : {order['client_fname']}\n"
            f"    Message   : Your order of {order['order_quantity']} x "
            f"{order['item']} has been received.\n"
            f"    Order ID  : {order['order_id']}\n"
            f"    Partition : {msg.partition()}\n"
        )

except KeyboardInterrupt:
    print("\nStopping Order Notification Service...")
finally:
    consumer.close()