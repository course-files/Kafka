from confluent_kafka import Consumer
import json

consumer_config = {
    "bootstrap.servers": "localhost:9092",
    # A 'group.id' identifies groups of consumers that are instances of the
    # same application. This is useful in cases where an application has been
    # scaled out to form a cluster. However, the work of consuming is
    # distributed across the cluster, so each instance will consume a subset of
    # the partitions in the topic.

    # Analogy: A group of friends are eating dinner together.
    # Each person is a consumer, and the group of friends is a consumer group.
    # The dinner is the topic. Each person eats a subset of the dinner
    # so that the task of finishing the meal is distributed across the group.
    # The whole meal is consumed in the end.
    "group.id": "order-inventory",

    # "auto.offset.reset" is used to specify what should be done when there is
    # no initial offset in Kafka or if the current offset does not exist any more
    # on the server (e.g., because that data has been deleted).
    # "auto.offset.reset" options include:
    ## 1. earliest: The consumer will start from the earliest offset in the partition.
    ## 2. latest: The consumer will start from the latest offset in the partition.
    ## 3. by_duration: Reset the offset to a configured <duration> from the current timestamp.
    ## 4. none: Throw an exception to the consumer if no previous offset is found for the consumer's group.
    "auto.offset.reset": "earliest"
}

consumer = Consumer(consumer_config)

consumer.subscribe(["orders"])

print("-" * 75)
print("The Kafka Consumer is running and it is subscribed to the 'orders' topic")
print("-" * 75)

try:
    while True:
        # .poll() asks the broker for any new messages on the subscribed topics
        # and returns them to the consumer for processing.
        # 1.0 is the maximum time in seconds to block waiting for new messages.

        # Polling allows consumers to control the frequency of reading messages.
        # The Kafka broker does not push messages to the consumers if the consumer
        # has not polled.
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print("❌ Error: {}".format(msg.error()))
            continue

        # The message value is in Bytes.
        # We decode it to get the original JSON string.
        value = msg.value().decode("utf-8")

        # We then take the JSON string and convert it to a Python dictionary
        # A Python dictionary is a collection of key-value pairs where each
        # unique key maps to a specific value.

        order = json.loads(value)

        print(f"Remove from inventory: {order['order_quantity']} x {order['item']} for order ID {order['order_id']}")

except KeyboardInterrupt:
    print ("\nStopping consumer...")
finally:
    # You MUST be able to gracefully shut down your application.
    # This involves closing the consumer connection to prevent resource leaks.
    # The close() function closes network connections and file handles. It also
    # commits any outstanding offsets, and the consumer's partition
    # assignments are revoked.
    consumer.close()