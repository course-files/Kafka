# -----------------------------------------------------------------------------
# SQLALCHEMY ORM MODEL — LAGOS, NIGERIA (WAT = UTC+1)
# -----------------------------------------------------------------------------
# This model maps to the "orders" table in PostgreSQL.
#
# TIMEZONE CHANGE FROM PREVIOUS VERSION:
#   received_at previously used datetime.datetime.utcnow — a deprecated
#   method that produces a timezone-NAIVE timestamp. A naive timestamp
#   has no timezone information attached and cannot be correctly compared
#   across systems in different timezones.
#
#   It now uses datetime.now(tz=TZ) with the Lagos timezone, producing a
#   timezone-AWARE timestamp. This means the value stored in PostgreSQL
#   carries its UTC offset (+01:00), making it unambiguous regardless of
#   which system reads it.
#
#   DateTime(timezone=True) maps to TIMESTAMPTZ in PostgreSQL — a column
#   type that stores the UTC offset alongside the timestamp value.
#
# TEACHING POINT:
#   Query the received_at column in both PostgreSQL and ClickHouse.
#   PostgreSQL will show the time in Lagos WAT (UTC+1).
#   ClickHouse will show the same moment in Nairobi EAT (UTC+3).
#   The underlying UTC value is identical. Only the display timezone differs.
# -----------------------------------------------------------------------------
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase

# Lagos, Nigeria — WAT (UTC+1)
# The TIMEZONE variable is injected by docker-compose from the .env file.
TIMEZONE_NAME = os.environ.get('TIMEZONE', 'Africa/Lagos')
TZ = ZoneInfo(TIMEZONE_NAME)


class Base(DeclarativeBase):
    pass


class Order(Base):
    """
    Maps to the "orders" table in PostgreSQL.

    received_at is set automatically at insert time to the current
    Lagos local time (WAT = UTC+1). Using timezone=True on the
    DateTime column stores the UTC offset in PostgreSQL, preventing
    any ambiguity when the Nairobi Transformer reads this value.
    """
    __tablename__ = "orders"

    order_id       = Column(String(36),  primary_key=True)
    client_fname   = Column(String(100), nullable=False)
    item           = Column(String(100), nullable=False)
    order_quantity = Column(Integer,     nullable=False)

    # DateTime(timezone=True) → TIMESTAMPTZ in PostgreSQL.
    # Stores the UTC offset (+01:00 for Lagos) alongside the timestamp.
    # This is the correct column type for any timestamp that will be
    # read by services in different timezones.
    received_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=TZ)
    )

    def __repr__(self):
        return (
            f"<Order(order_id='{self.order_id}', "
            f"item='{self.item}', "
            f"quantity={self.order_quantity}, "
            f"received_at='{self.received_at}')>"
        )