# =============================================================================
# BENCHMARK DATA GENERATOR
# =============================================================================
# This script inserts 500,000 synthetic orders into BOTH PostgreSQL and
# ClickHouse so that the performance benchmark in lab4_analytics.Rmd produces
# a meaningful and clearly visible difference.
#
# The data is inserted directly — it bypasses Kafka and Debezium intentionally.
# The purpose here is not to demonstrate the pipeline but to populate the
# databases with enough rows for the benchmark to be statistically meaningful.
#
# WHY 500,000 ROWS?
#   The performance difference between a row store (PostgreSQL) and a column
#   store (ClickHouse) is negligible on small tables because both can fit the
#   entire dataset in memory. At 500,000 rows, the difference becomes clearly
#   visible and demonstrates the architectural point without requiring a
#   production-scale dataset.
#
# USAGE:
#   pip install psycopg2-binary clickhouse-connect faker
#   python generate_data.py
# =============================================================================

import uuid
import random
import datetime
from zoneinfo import ZoneInfo
import psycopg2
import clickhouse_connect

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------

POSTGRES_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "lab_db",
    "user":     "lab_user",
    "password": "lab_password"
}

CLICKHOUSE_CONFIG = {
    "host":     "localhost",
    "port":     8123,
    "username": "default",
    "password": "lab_password",
    "database": "default"
}

# Total number of orders to generate.
# Increase this for a more dramatic benchmark result.
TOTAL_ROWS = 500_000

# Batch size for inserts. Larger batches are faster but use more memory.
BATCH_SIZE = 5_000

# Sample data — reflects the items and customers from the lab
ITEMS   = [
    'Managu', 'Sukuma Wiki', 'Spinach', 'Mahindi', 'Nyanya', 'Matoke',
    'Injera', 'Jollof Rice', 'Ugali', 'Fufu', 'Egusi Soup', 'Nyama Choma',
    'Kaimati', 'Mahamri', 'Omena', 'Mutura', 'Matumbo']

CUSTOMERS = [
    'Omondi', 'Kiplagat', 'Mutua', 'Wanyama', 'Odhiambo', 'Kariuki',
    'Njoroge', 'Ochieng', 'Muthoni', 'Mwangi','Mugisha', 'Ndayishimiye',
    'Nkurunziza', 'Kagame', 'Bizimana', 'Mukasa', 'Kabongo', 'Mutombo',
    'Kabila', 'Lumumba', 'Mugabe', 'Mandela', 'Zuma', 'Malema', 'Mbeki',
    'Koinange', 'Mandela', 'Zuma', 'Malema', 'Munee', 'Munyao', 'Munyoki',
    'Munyua', 'Munyui', 'Munyuli', 'Munywe', 'Munzala', 'Munzala',
    'Hassan', 'Mohammed', 'Ali', 'Abdi', 'Omar', 'Osman', 'Hussein',
    'Ahmed', 'Ibrahim', 'Adan', 'Yusuf', 'Abdullahi']

# Africa/Nairobi for ClickHouse, Africa/Lagos for PostgreSQL
# (matching the lab configuration)
NAIROBI_TZ = ZoneInfo("Africa/Nairobi")
LAGOS_TZ   = ZoneInfo("Africa/Lagos")

# Time window: orders placed over the last 90 days
NOW_NAIROBI = datetime.datetime.now(tz=NAIROBI_TZ)
NINETY_DAYS_AGO = NOW_NAIROBI - datetime.timedelta(days=90)


def random_order():
    """Generate a single synthetic order record."""
    order_id       = str(uuid.uuid4())
    client_fname   = random.choice(CUSTOMERS)
    item           = random.choice(ITEMS)
    order_quantity = random.randint(1, 20)
    is_bulk_order  = 1 if order_quantity > 5 else 0

    # Random timestamp within the last 90 days
    random_seconds = random.uniform(0, 90 * 24 * 3600)
    received_nairobi = NINETY_DAYS_AGO + datetime.timedelta(seconds=random_seconds)
    received_lagos   = received_nairobi.astimezone(LAGOS_TZ)

    return {
        "order_id":       order_id,
        "client_fname":   client_fname,
        "item":           item,
        "order_quantity": order_quantity,
        "is_bulk_order":  is_bulk_order,
        # PostgreSQL stores in Lagos time (as configured in Lab 3)
        "received_lagos":   received_lagos,
        # ClickHouse stores in Nairobi time (as converted by the transformer)
        "received_nairobi": received_nairobi,
    }


# -----------------------------------------------------------------------------
# POSTGRESQL INSERT
# -----------------------------------------------------------------------------

def insert_postgres(conn, batch):
    """Insert a batch of orders into PostgreSQL."""
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO orders (order_id, client_fname, item, order_quantity, received_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (order_id) DO NOTHING
            """,
            [
                (
                    row["order_id"],
                    row["client_fname"],
                    row["item"],
                    row["order_quantity"],
                    row["received_lagos"].replace(tzinfo=None)  # store as naive Lagos time
                )
                for row in batch
            ]
        )
    conn.commit()


# -----------------------------------------------------------------------------
# CLICKHOUSE INSERT
# -----------------------------------------------------------------------------

def insert_clickhouse(client, batch):
    """Insert a batch of orders into ClickHouse."""
    now_nairobi = datetime.datetime.now(tz=NAIROBI_TZ)

    client.insert(
        table="orders",
        data=[
            [
                row["order_id"],
                row["client_fname"],   # customer_name in ClickHouse schema
                row["item"],
                row["order_quantity"],
                row["is_bulk_order"],
                row["received_nairobi"],
                now_nairobi,           # processed_at
                "INSERT"               # operation
            ]
            for row in batch
        ],
        column_names=[
            "order_id",
            "customer_name",
            "item",
            "order_quantity",
            "is_bulk_order",
            "received_at",
            "processed_at",
            "operation"
        ]
    )


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("PART 4 — BENCHMARK DATA GENERATOR")
    print(f"Generating {TOTAL_ROWS:,} synthetic orders...")
    print("=" * 70)

    # Connect to PostgreSQL
    print("\nConnecting to PostgreSQL...")
    try:
        pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
        print("✅ PostgreSQL connection successful.")
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("   Is the Lab 3 stack running? Run: docker compose up -d")
        return

    # Connect to ClickHouse
    print("Connecting to ClickHouse...")
    try:
        ch_client = clickhouse_connect.get_client(**CLICKHOUSE_CONFIG)
        ch_client.query("SELECT 1")
        print("✅ ClickHouse connection successful.")
    except Exception as e:
        print(f"❌ ClickHouse connection failed: {e}")
        print("   Is the Lab 3 stack running? Run: docker compose up -d")
        pg_conn.close()
        return

    # Insert in batches
    print(f"\nInserting {TOTAL_ROWS:,} rows in batches of {BATCH_SIZE:,}...")
    print("-" * 70)

    batches_total    = TOTAL_ROWS // BATCH_SIZE
    rows_inserted_pg = 0
    rows_inserted_ch = 0

    for batch_num in range(batches_total):
        batch = [random_order() for _ in range(BATCH_SIZE)]

        # Insert into PostgreSQL
        try:
            insert_postgres(pg_conn, batch)
            rows_inserted_pg += len(batch)
        except Exception as e:
            print(f"⚠️  PostgreSQL batch {batch_num + 1} failed: {e}")

        # Insert into ClickHouse
        try:
            insert_clickhouse(ch_client, batch)
            rows_inserted_ch += len(batch)
        except Exception as e:
            print(f"⚠️  ClickHouse batch {batch_num + 1} failed: {e}")

        # Progress report every 10 batches
        if (batch_num + 1) % 10 == 0:
            pct = ((batch_num + 1) / batches_total) * 100
            print(
                f"   Batch {batch_num + 1:>4} / {batches_total} "
                f"({pct:>5.1f}%) — "
                f"PG: {rows_inserted_pg:>7,} rows | "
                f"CH: {rows_inserted_ch:>7,} rows"
            )

    # Final summary
    print("-" * 70)
    print(f"\n✅ Done.")
    print(f"   PostgreSQL : {rows_inserted_pg:,} rows inserted")
    print(f"   ClickHouse : {rows_inserted_ch:,} rows inserted")
    print()

    # Verify final counts
    with pg_conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM orders;")
        pg_count = cur.fetchone()[0]
    ch_count = ch_client.query("SELECT COUNT(*) FROM orders;").result_rows[0][0]

    print(f"   Total rows in PostgreSQL  : {pg_count:,}")
    print(f"   Total rows in ClickHouse  : {ch_count:,}")
    print()
    print("You may now open lab4_analytics.Rmd in RStudio.")

    pg_conn.close()


if __name__ == "__main__":
    main()
