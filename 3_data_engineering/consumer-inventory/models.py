# -----------------------------------------------------------------------------
# SQLALCHEMY ORM MODEL
# -----------------------------------------------------------------------------
# An ORM (Object-Relational Mapper) allows you to interact with a relational
# database using Python objects and classes instead of writing raw SQL.
#
# Here, we define the "Order" class. SQLAlchemy maps this class to the
# "orders" table in PostgreSQL. Each instance of the Order class represents
# one row in that table.
#
# The table itself was created by database/init.sql when the PostgreSQL
# container started. The model here mirrors that schema exactly so that
# SQLAlchemy knows how to read from and write to it.
# -----------------------------------------------------------------------------

from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase
import datetime


class Base(DeclarativeBase):
    pass


class Order(Base):
    """
    Maps to the "orders" table in PostgreSQL.

    Each column defined here corresponds to a column in the database table.
    The types (String, Integer, DateTime) are SQLAlchemy types that map to
    the equivalent PostgreSQL types (VARCHAR, INTEGER, TIMESTAMP).
    """
    __tablename__ = "orders"

    order_id       = Column(String(36),  primary_key=True)
    client_fname   = Column(String(100), nullable=False)
    item           = Column(String(100), nullable=False)
    order_quantity = Column(Integer,     nullable=False)

    # received_at is set automatically to the current timestamp at the
    # moment the record is inserted. This is the database insertion time —
    # i.e., when the Inventory Service consumed the Kafka message —
    # not the time the order was originally placed.
    received_at    = Column(DateTime, default=datetime.datetime.utcnow)

    def __repr__(self):
        return (
            f"<Order(order_id='{self.order_id}', "
            f"item='{self.item}', "
            f"quantity={self.order_quantity})>"
        )