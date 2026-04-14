# -----------------------------------------------------------------------------
# ORDER PRODUCER SERVICE
# -----------------------------------------------------------------------------
# In a microservices architecture, this service represents the Order Service.
# Its responsibility is to accept new orders and publish them as events to
# the Kafka "orders" topic so that downstream services can react to them.
#
# In Part 1, this script ran directly on your host machine and connected to
# a single Kafka broker via localhost:9092.
#
# In Part 2, this script runs inside a Docker container and connects to a
# cluster of three Kafka brokers using their Docker service names (not to
# localhost:9092).
#
# The key changes from Part 1 are (as we move towards a more production
# ready setup):
#   1. Bootstrap servers read from an environment variable (not hardcoded)
#   2. 'acks': 'all' ensures full replication acknowledgment per message
#   3. Orders are generated in a loop to demonstrate live message flow
# -----------------------------------------------------------------------------

import os
import time
import uuid
import json
import random
from confluent_kafka import Producer

# Read the bootstrap servers from the environment variable set in
# docker-compose.yaml. Using environment variables instead of hardcoding
# values makes the application portable — the same code works in a local
# lab, a staging environment, and a production cluster simply by changing
# the environment variable.
BOOTSTRAP_SERVERS = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

producer_config = {
    'bootstrap.servers': BOOTSTRAP_SERVERS,

    # 'acks' controls how many brokers must confirm receipt of a message
    # before the producer considers it successfully delivered.
    #
    # Options:
    #   0    : Fire and forget. No confirmation. Fastest, but messages can
    #          be lost if the broker fails.
    #   1    : The leader broker confirms receipt. Fast, but if the leader
    #          fails before replicating, the message is lost.
    #   'all': All in-sync replicas must confirm receipt. Slowest, but
    #          guarantees no message is lost as long as at least
    #          min.insync.replicas brokers are available.
    #
    # We use 'all' here because we have a 3-broker cluster and we want to
    # demonstrate true fault-tolerant, replicated delivery.
    'acks': 'all'
}

producer = Producer(producer_config)

# This provides sample data to generate realistic-looking orders.
ITEMS   = ["Managu", "Sukuma Wiki", "Spinach", "Mahindi", "Nyanya", "Matoke"]
CLIENTS = ["Peter", "Jane", "Koinange", "Wanjiru", "Otieno", "Aisha"]

def delivery_report(err, msg):
    """
    Called once per message to report the delivery outcome.
    Notice the partition number in the output.
    With 3 partitions, you will see messages landing on partitions 0, 1,
    and 2. Each partition is managed by a different broker, demonstrating
    that the load is distributed across the Kafka cluster.
    """
    if err is not None:
        print(f"❌ Message delivery failed: {err}")
    else:
        order = json.loads(msg.value().decode("utf-8"))
        print(
            f"✅ Order produced\n"
            f"    Order ID  : {order['order_id']}\n"
            f"    Item      : {order['order_quantity']} x {order['item']}\n"
            f"    Client    : {order['client_fname']}\n"
            f"    Topic     : {msg.topic()}\n"
            f"    Partition : {msg.partition()}\n"
            f"    Offset    : {msg.offset()}\n"
        )

# Give the Kafka cluster a moment to fully stabilize after the initial
# health checks pass. This is a safety buffer to ensure that the producer
# does not send messages to a broker that is still booting up.

print("Waiting for the Kafka cluster to stabilize...")
time.sleep(10)

print("-" * 75)
print("The 'order producer' is running. Sending one order every 5 seconds.")
print("Sending one order every 5 seconds for simulation purposes.")
print(f"Connected to brokers: {BOOTSTRAP_SERVERS}")
print("-" * 75)

while True:
    order = {
        'order_id':       str(uuid.uuid4()),
        'client_fname':   random.choice(CLIENTS),
        'item':           random.choice(ITEMS),
        'order_quantity': random.randint(1, 8)
    }

    value = json.dumps(order).encode("utf-8")

    # The message key ensures that all messages for the same order_id
    # always go to the same partition, preserving order per entity.
    key = order['order_id'].encode("utf-8")

    producer.produce(
        topic="orders",
        key=key,
        value=value,
        callback=delivery_report
    )

    # flush() blocks until the message is acknowledged by all in-sync
    # replicas (because acks='all'). This makes the delivery report print
    # immediately after each message, keeping the output easy to follow.
    producer.flush()

    time.sleep(5)