# We need to install and import a library called "confluent_kafka"
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
# If not, then we can log the error.
def delivery_report(err, msg):
    """ Called once for each message produced to indicate the delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print('❌ Message delivery failed: {}'.format(err))
    else:
        print(
            '✅ Message delivered: "{}" \n'
            'Topic: "{}", \n'
            'Partition: "{}"'
            .format(msg.value().decode("utf-8"), msg.topic(), msg.partition()))

# We create an event that we want to send to Kafka.
order = {
    'order_id': str(uuid.uuid4()),
    'client_fname': "Janet",
    'item': "Sweet Potatoes",
    'order_quantity': 1
}

# The order above is a JSON object. But we need to convert it into a Kafka
# compatible format, i.e., Bytes.
value = json.dumps(order).encode("utf-8")

# This sends the event to Kafka and asks Kafka to create a new topic called
# "orders", if the topic does not exist.
# "value" is the event that we then send into the "orders" topic.
producer.produce(
    topic="orders",
    value=value,
    # "callback" enables to specify a function that will be called when the
    # message is delivered or if there is an error.
    callback=delivery_report
)

# Kafka producers are asynchronous, which means that the produce() method
# does not wait for the event to be sent to Kafka. We need to call flush() to
# make sure that all the events that we have produced are sent to Kafka before
# we exit the program otherwise, the events will be lost.
producer.flush()

# TROUBLESHOOTING

# Documentation for Kafka CLI: https://docs.confluent.io/kafka/operations-tools/kafka-tools.html
# or docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --help

# List all the topics using Kafka CLI
# docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092

# List the configuration properties and values for a topic
# docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --describe --topic orders

# Consume records from a topic
# docker exec -it kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic orders --from-beginning