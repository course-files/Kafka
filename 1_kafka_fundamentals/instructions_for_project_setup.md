# Part 1: Kafka Fundamentals

Part 1 of the lab is used to learn about Kafka. It simulates part of an order 
system for a restaurant. There is a producer service that sends orders to Kafka, 
and two consumers that consume the orders. One consumer is responsible for 
sending notifications to the customers, while the other consumer is responsible 
for updating the inventory.

Navigate into the Part 1 directory (`1_kafka_fundamentals`) first. All the 
commands below assume that you are inside the `1_kafka_fundamentals` directory.

```bash
cd 1_kafka_fundamentals_old/
```

## Step 1: Install the Dependencies
Then install the dependencies.

```bash
pip install -r requirements.txt
```

## Step 2: Run Unit Tests

Refer to the following instructions to run the unit tests:
[instructions_for_running_unit_tests.md](instructions_for_running_unit_tests.md)

## Step 3: Execute the Project Setup Script

```bash
# This is executed to create the required volume directories
chmod u+x project_setup.sh
sed -i 's/\r$//' project_setup.sh
./project_setup.sh
```

## Step 4: Start the Kafka Service

Use the `confluentinc/cp-kafka` image to create a Kafka container. 
The Kafka container uses **KRaft** as the consensus mechanism instead of using **Zookeeper**.

```bash
docker compose -f docker-compose.yaml up --build
```

## Step 5: Start the Consumers

```bash
python consumer_order_notification.py
python consumer_order_inventory.py
```

## Step 6: Start the Producer

```bash
python producer_order.py
```

## Step 7: Project Cleanup

```bash
# Stop all services AND delete all stored data
docker-compose down -v
```

```bash
chmod u+x project_cleanup.sh
sed -i 's/\r$//' project_cleanup.sh
./project_cleanup.sh
```