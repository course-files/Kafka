# Key Architectural Differences from Part 1

1. **Every service now runs inside a container.** Containers do not communicate
with each other via localhost — they use Docker service names instead. The
bootstrap servers are now **kafka1:9092,kafka2:9092,kafka3:9092.**
2. The `orders` topic will have a replication factor of **3** and **3**
partitions. You will observe messages landing on different partitions. You can
stop one broker and watch the system continue working.
3. The producer now uses `acks=all`. This means the producer waits for all
in-sync replicas to confirm each message. Combined with `min.insync.replicas=2`,
the cluster tolerates one broker failure without losing a single message.
4. The Inventory Service now writes every order to PostgreSQL using SQLAlchemy.

# Step 1: Run `project_setup.sh` to create the volume directories (once only)
Make `project_setup.sh` executable:

```bash
chmod u+x project_setup.sh
./project_setup.sh
```

# Step 2: Build the images (once only) and start all services

```bash
docker compose -f docker-compose.yaml up -d --build \
  --scale producer=1 \
  --scale consumer-notification=1 \
  --scale consumer-inventory=1
```

# Step 3: In a separate terminal, verify the orders table is being populated
`docker exec -it postgres psql -U lab_user -d lab_db -c "SELECT * FROM orders;"`

# Step 4: Verify the topic and its replication

```bash
docker exec -it kafka1 kafka-topics \
  --bootstrap-server localhost:9092 \
  --describe --topic orders
```

# Step 5 (IMPORTANT): Demonstrate fault tolerance — stop one broker and watch the system continue

```bash
docker stop kafka3
```

Observe that the producer and consumers continue operating without interruption.
The cluster still has 2 in-sync replicas, which satisfies `min.insync.replicas=2`.

# Step 6: Bring the broker back and watch it rejoin the cluster

docker start kafka3

# Step 7: Simulate horizontal scaling for parallel processing
Both inventory consumer containers join the same consumer group (order-inventory).
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
  --describe --group order-inventory
```

## Scale the inventory consumer to 2 instances:

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
  --describe --group order-inventory
```

## Scale the inventory consumer to 3 instances:

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
  --describe --group order-inventory
```

# Step 8: Tear down the entire lab
docker-compose down

# To also delete all stored data (volumes):
docker-compose down -v