# Part 2: Containerized Microservices

## Key Architectural Differences from Part 1

1. **Every service now runs inside a container.** Containers do not communicate
with each other via localhost — they use Docker service names instead. The
bootstrap servers are now **kafka1:9092, kafka2:9092, and kafka3:9092.**
2. The `orders` topic will have a replication factor of **3** and **3**
partitions. You will observe messages landing on different partitions. You can
stop one broker and watch the system continue working.
3. The producer now uses `acks=all`. This means the producer waits for all
in-sync replicas to confirm each message. Combined with `min.insync.replicas=2`,
the cluster tolerates one broker failure without losing a single message.
4. The Inventory Service now not only consumes messages but also proceeds to write every order to PostgreSQL via an **Object Relational Mapping (ORM)** layer created using **SQLAlchemy**.

Navigate into the Part 2 directory (`2_containerized_microservices`) first. All the 
commands below assume that you are inside the `2_containerized_microservices` directory.

```bash
cd 2_containerized_microservices
```
## Step 1: Run Unit Tests

Run the unit tests:

```bash
cd producer/
pytest -v -s test_producer_order.py
```

```bash
cd ../consumer-notification/
pytest -v -s test_consumer_order_notification.py
```

```bash
cd ../consumer-inventory/
pytest -v -s test_consumer_order_inventory.py
```

## Step 2: Execute the Project Setup Script

```bash
# This is executed to create the required volume directories
chmod u+x project_setup.sh
sed -i 's/\r$//' project_setup.sh
./project_setup.sh
```

## Step 3: Build the images (once only) and start all services

```bash
docker compose -f docker-compose.yaml up --build \
  --scale producer=1 \
  --scale consumer-notification=1 \
  --scale consumer-inventory=1
```

Give the containers in the stack a few minutes to be stable. Check
Docker Desktop for any container that did not start and start it manually
by running `docker start <container-name>` or clicking the "Start" button in
the Docker Desktop UI.

## Step 4: In a separate terminal, verify the `orders` table is being populated

Execute:

```bash
docker exec -it postgres psql -U lab_user -d lab_db -c "SELECT * FROM orders ORDER BY received_at DESC LIMIT 5;"
```

## Step 5: Verify the topic exists as well as its replication status

```bash
docker exec -it kafka1 kafka-topics \
  --bootstrap-server localhost:9092 \
  --describe --topic orders
```

## Step 6 (IMPORTANT): Demonstrate fault tolerance — stop one broker and watch the system continue

```bash
docker stop kafka3
```

Observe that the `producer` and `consumers` continue operating without 
interruption.
The cluster still has **2** in-sync replicas, which satisfies `min.insync.replicas=2`.

## Step 7: Bring the broker back and watch it rejoin the cluster

docker start kafka3

## Step 8: Simulate horizontal scaling for parallel processing

Both inventory consumer containers join the same consumer group (`order-inventories`).
Kafka detects the new member, triggers a rebalance, and redistributes the 3
partitions between the 2 instances. Each instance owns a subset of partitions and
processes only the messages from those partitions. No message is processed twice.

Example:

```text
Before scaling:
  consumer-inventory-1  →  partitions 0, 1, 2

After scaling to 2:
  consumer-inventory-1  →  partitions 0, 1
  consumer-inventory-2  →  partition  2
```

Observe the partition assignment before the scaling:

```bash
docker exec kafka1 kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --group order-inventories
```

### Scale the inventory consumer to 2 instances:

```bash
docker compose -f docker-compose.yaml up -d \
  --scale producer=1 \
  --scale consumer-notification=1 \
  --scale consumer-inventory=2
```

Observe the partition assignment after the scaling:

```bash
docker exec kafka1 kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --group order-inventories
```

### Scale the inventory consumer to 3 instances:

```bash
docker compose -f docker-compose.yaml up -d \
  --scale producer=1 \
  --scale consumer-notification=1 \
  --scale consumer-inventory=3
```

Observe the partition assignment after the scaling:

```bash
docker exec kafka1 kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --group order-inventories
```

Oberve that the `orders` table in the PostgreSQL container is still receiving
data:

```bash
docker exec -it postgres psql -U lab_user -d lab_db -c "SELECT * FROM orders ORDER BY received_at DESC LIMIT 5;"
```

## Step 9: Tear Down (Clean Up) Part 2 of the Lab

```bash
# Stop all services AND delete all stored data
docker-compose down -v
```

```bash
chmod u+x project_cleanup.sh
sed -i.bak 's/\r$//' project_cleanup.sh
./project_cleanup.sh
```