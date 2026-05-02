# -----------------------------------------------------------------------------
# ORDER PRODUCER SERVICE
# -----------------------------------------------------------------------------
#
# TIMEZONE CONTEXT:
#   This service runs on West Africa Time (WAT = UTC+1), specifically Lagos,
#   Nigeria time. The produced_at timestamp appended to each order reflects
#   Lagos local time.
#
#   LESSON TO LEARN: When this timestamp eventually reaches the Nairobi
#   Transformer, it will be converted to East Africa Time (EAT = UTC+3).
#   The same moment in time will appear 2 hours later on the clock.
#   This is correct behavior — not a data error.
# -----------------------------------------------------------------------------

import os
import time
import uuid
import json
import random
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from confluent_kafka import Producer

# Read the bootstrap servers from the environment variable set in
# docker-compose.yaml. Using environment variables instead of hardcoding
# values makes the application portable — the same code works in a local
# lab, a staging environment, and a production cluster simply by changing
# the environment variable.
BOOTSTRAP_SERVERS = os.environ.get('BOOTSTRAP_SERVERS', 'localhost:9092')

# Lagos, Nigeria — WAT (UTC+1)
# Read from the TIMEZONE environment variable so the timezone is
# configurable without a code change or image rebuild.
TIMEZONE_NAME = os.environ.get('TIMEZONE', 'Africa/Lagos')
TZ = ZoneInfo(TIMEZONE_NAME)

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

# This provides sample data to generate realistic-looking orders.
ITEMS   = ["Managu", "Sukuma Wiki", "Spinach", "Mahindi", "Nyanya", "Matoke",
           'Injera', 'Jollof Rice', 'Ugali', 'Fufu', 'Egusi Soup', 'Nyama Choma',
           'Kaimati', 'Mahamri', 'Omena', 'Mutura', 'Matumbo']
CLIENTS = ['Omondi', 'Kiplagat', 'Mutua', 'Wanyama', 'Odhiambo', 'Kariuki',
           'Njoroge', 'Ochieng', 'Muthoni', 'Mwangi','Mugisha', 'Ndayishimiye',
           'Nkurunziza', 'Kagame', 'Bizimana', 'Mukasa', 'Kabongo', 'Mutombo',
           'Kabila', 'Lumumba', 'Mugabe', 'Mandela', 'Zuma', 'Malema', 'Mbeki',
           'Koinange', 'Mandela', 'Zuma', 'Malema', 'Munee', 'Munyao', 'Munyoki',
           'Munyua', 'Munyui', 'Munyuli', 'Munywe', 'Munzala', 'Munzala',
           'Hassan', 'Mohammed', 'Ali', 'Abdi', 'Omar', 'Osman', 'Hussein',
           'Ahmed', 'Ibrahim', 'Adan', 'Yusuf', 'Abdullahi']

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

def create_order():
    """
    Generates a random order dictionary.
    """
    # Capture the current Lagos time as a timezone-aware timestamp.
    # Including produced_at in the Kafka message gives the Transformer
    # a second reference timestamp to compare against received_at
    # (set by the Inventory Consumer when the record lands in PostgreSQL).
    now_lagos = datetime.now(tz=TZ)
    return {
        'order_id': str(uuid.uuid4()),
        'client_fname': random.choice(CLIENTS),
        'item': random.choice(ITEMS),
        'order_quantity': random.randint(1, 8),
        # ISO 8601 format preserves the UTC offset (+01:00) so any
        # downstream service can parse this unambiguously.
        'produced_at': now_lagos.isoformat()
    }

def main():
    producer = Producer(producer_config)

    # Give the Kafka cluster a moment to fully stabilize after the initial
    # health checks pass. This is a safety buffer to ensure that the producer
    # does not send messages to a broker that is still booting up.

    print("Waiting for the Kafka cluster to stabilize...")
    time.sleep(10)

    print("-" * 75)
    print(f"Order Producer is running  [Timezone: {TIMEZONE_NAME}]")
    print("Sending one order every 5 seconds.")
    print(f"Connected to brokers: {BOOTSTRAP_SERVERS}")
    print("-" * 75)

    try:
        while True:
            order = create_order()

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

            # In high-throughput production environments, one would call
            # flush() only before shutting down to allow Kafka to batch messages.

            # Otherwise, calling it as we have done below actually makes the
            # producer synchronous instead of asynchronous. We call it here for
            # educational purposes (to make it easier to learn).
            producer.flush()

            time.sleep(5)
    except KeyboardInterrupt:
        print("\nStopping Order Producer Service...")

if __name__ == "__main__":
    main()
