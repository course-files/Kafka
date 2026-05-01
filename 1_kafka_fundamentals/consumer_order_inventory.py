# -----------------------------------------------------------------------------
# ORDER INVENTORY SERVICE
# -----------------------------------------------------------------------------
# In a microservices architecture, this file represents the Inventory Service.
# Its responsibility is to listen for new orders and update stock levels
# accordingly, for example, by deducting the ordered quantity from a database.
# It operates completely independently of the Notification Service (a loosely
# coupled system).
#
# NOTE: This file is intentionally similar in structure to
# consumer_order_notification.py. Both files share the same consumer setup
# because they perform the same fundamental operation: subscribing to a topic
# and polling for messages. The only differences are the group.id and the
# business logic applied to each message. In a production codebase, the shared
# setup would be extracted into a reusable module to avoid duplication.
# The files are kept separate here so that each service is self-contained
# and easy to follow independently.
# -----------------------------------------------------------------------------

from confluent_kafka import Consumer
import json

consumer_config = {
    "bootstrap.servers": "localhost:9092",

    # A "group.id" identifies a group of consumers that are instances of the
    # same application. This is useful when an application has been scaled out
    # to handle a high volume of messages. The work of consuming is distributed
    # across the group, so each instance processes a subset of the partitions.
    #
    # Analogy: A group of friends are eating dinner together.
    # Each person is a consumer, and the group is the consumer group.
    # The dinner is the topic. Each person eats a portion of the meal so that
    # the task of finishing it is shared. The whole meal is consumed in the end.
    #
    # IMPORTANT: This consumer group ("order-inventories") is different from the
    # one used in consumer_order_notification.py ("order-notifiers"). This means
    # that BOTH consumers will receive every message independently. This is the
    # publish-subscribe pattern: one event, many independent reactions.
    "group.id": "order-inventories",

    # "auto.offset.reset" specifies where the consumer should start reading
    # when there is no previously committed offset for the consumer group.
    # This typically happens the very first time a consumer group runs.
    #
    # Options:
    #   "earliest": Start from the very first message available in the topic.
    #   "latest": Start from the next new message (ignore existing messages).
    #   "none": Throw an exception if no previous offset is found.
    #
    # We use "earliest" so that you always receive messages even if you started
    # this consumer after the producer had already run. This is the safest
    # choice for a learning environment.
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

def process_order_message(msg_value):
    """
    Converts raw bytes to a notification string.
    """
    # The message value arrives as Bytes.
    # We decode it back into a UTF-8 string first.
    value = msg_value.value().decode("utf-8")

    # We then convert the JSON string into a Python dictionary so we can
    # access individual fields by their key names.
    order = json.loads(value)

    # In a real Inventory Service, this is where you would connect to a
    # database and deduct the ordered quantity from the current stock level.
    # For now, we simply print the action that would be taken.
    print(f"📦 Inventory updated: Deducted {order['order_quantity']} x "
          f"{order['item']} for \nOrder ID {order['order_id']}.")

def main():
    consumer = Consumer(consumer_config)

    consumer.subscribe(["orders"])

    print("-" * 75)
    print("Order Inventory Service is running. Subscribed to 'orders' topic.")
    print("-" * 75)

    try:
        while True:
            # poll() asks the broker for any new messages on the subscribed topics.
            # The argument (1.0) is the maximum number of seconds to wait for a
            # new message before returning. If no message arrives within that time,
            # poll() returns None and the loop continues.
            #
            # NOTE: The broker does not push messages to consumers automatically.
            # The consumer must poll to request them. This gives the consumer full
            # control over the rate at which it reads and processes messages.
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                print("❌ Error: {}".format(msg.error()))
                continue

            process_order_message(msg)

    except KeyboardInterrupt:
        print("\nStopping Order Inventory Service...")
    finally:
        # Closing the consumer is mandatory. It releases network connections and
        # file handles, commits any pending offsets, and revokes the consumer's
        # partition assignments so other consumers in the group can take over.
        consumer.close()

if __name__ == "__main__":
    main()
