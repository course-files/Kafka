# We need to install and import a library called "confluent_kafka".
# "confluent_kafka" is a Python client for Apache Kafka developed and maintained
# by Confluent. It provides a high-performance API for producing and consuming
# Kafka messages.

# pip install confluent-kafka
from confluent_kafka import Producer
import uuid
import json

# We inform the producer of the location of the initial host that acts as the
# starting point for a producer to discover the full set of alive Kafka
# servers in the cluster.
producer_config = {
    'bootstrap.servers': 'localhost:9092'
}
producer = Producer(producer_config)


# The following helps us to track whether the message was sent or not.
# If delivery fails, the error is logged so we can investigate further.
def delivery_report(err, msg):
    """ Called once for each message produced to indicate the delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print('❌ Message delivery failed: {}'.format(err))
    else:
        print(
            '✅ Message delivered successfully: "{}" \n'
            'Topic: "{}", \n'
            'Partition: "{}"'
            .format(msg.value().decode("utf-8"), msg.topic(), msg.partition()))


# We create an event that we want to send to Kafka.
# NOTE: In a real system, this data would arrive dynamically, for example,
# from a web form, a mobile app, or another service. It is hardcoded here
# purely for demonstration purposes.
order = {
    'order_id': str(uuid.uuid4()),
    'client_fname': "Jeff",
    'item': "Managu",
    'order_quantity': 1
}

# The order above is a Python dictionary. We need to convert it to a JSON
# string first, and then encode it into Bytes, which is the format
# that Kafka expects for message values.
value = json.dumps(order).encode("utf-8")

# The key determines which partition the message is sent to.
# Kafka guarantees that all messages with the same key will always be sent
# to the same partition. This is important for preserving the order of
# messages that belong to the same entity. For example, all events for
# the same 'order_id' will always arrive in the correct sequence.
# Without a key, Kafka distributes messages across partitions randomly,
# and ordering is no longer guaranteed.
key = order['order_id'].encode("utf-8")

# This sends the event to Kafka.
# NOTE: Kafka will automatically create the "orders" topic if it does not
# already exist. This is a convenience feature controlled by the broker
# setting "auto.create.topics.enable", which is set to True by default.
# In production environments, this setting is typically disabled and topics
# are created manually with explicitly defined configurations (e.g., number
# of partitions, replication factor). We rely on it here for simplicity.
producer.produce(
    topic="orders",
    key=key,
    value=value,
    # "callback" allows us to specify a function that will be called when
    # the message is either delivered successfully or has failed.
    callback=delivery_report
)

# Kafka producers are asynchronous, which means that the produce() method
# does not wait for the message to be sent before moving on. We call flush()
# to force the producer to send all buffered messages before the program exits.
# Without flush(), buffered messages could be lost when the program terminates.
# TRY IT: Comment out flush() and run the script. Observe that the delivery
# report is never printed, because the program exits before the message is sent.
producer.flush()


# -----------------------------------------------------------------------------
# TROUBLESHOOTING
# -----------------------------------------------------------------------------
# Documentation for Kafka CLI:
# https://docs.confluent.io/kafka/operations-tools/kafka-tools.html

# List all topics
# docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092

# Describe a topic (partitions, replication factor, configuration)
# docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --describe --topic orders

# Consume all records from a topic from the beginning
# docker exec -it kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic orders --from-beginning