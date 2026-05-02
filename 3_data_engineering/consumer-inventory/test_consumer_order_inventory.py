import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Order
from consumer_order_inventory import save_order_to_db

## ----------------------------------------------------------------------------
## DATABASE TEST SETUP (In-Memory SQLite)
## ----------------------------------------------------------------------------

@pytest.fixture
def db_session():
    """
    Creates a fresh, in-memory SQLite database for each test.
    This ensures tests are isolated and do not interfere with each other.
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

## -----------------------------------------------------------------------------
## UNIT TESTS: Inventory Persistence Logic
## -----------------------------------------------------------------------------

def test_save_order_to_db_valid_data(db_session):
    """
    Verifies that valid order data is correctly saved to the database.
    """
    sample_data = {
        'order_id': '123',
        'client_fname': 'Osman',
        'item': 'Jollof Rice',
        'order_quantity': 5
    }

    # Act
    saved_record = save_order_to_db(db_session, sample_data)

    # Assert: Check the returned object
    assert saved_record.order_id == '123'
    assert saved_record.item == 'Jollof Rice'

    # Assert: Verify it exists in the database
    db_record = db_session.query(Order).filter_by(order_id='123').first()
    assert db_record is not None
    assert db_record.client_fname == 'Osman'
    # Ensure the default received_at timestamp was generated
    assert db_record.received_at is not None

def test_save_order_duplicate_id(db_session):
    """
    Verifies that the database enforces Primary Key constraints.
    In Kafka, at-least-once delivery often sends duplicates.
    """
    sample_data = {
        'order_id': 'duplicate-123',
        'client_fname': 'Victor',
        'item': 'Tilapia',
        'order_quantity': 1
    }

    # Save the first time
    save_order_to_db(db_session, sample_data)

    # Attempt to save the same ID again should raise an Integrity Error
    # (In SQLite/SQLAlchemy this raises an IntegrityError)
    from sqlalchemy.exc import IntegrityError
    with pytest.raises(IntegrityError):
        save_order_to_db(db_session, sample_data)
