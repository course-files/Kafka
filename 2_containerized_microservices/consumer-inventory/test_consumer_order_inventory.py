import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Order
from consumer_order_inventory import save_order_to_db

## -----------------------------------------------------------------------------
## FIXTURE: SET UP AN IN-MEMORY DATABASE
## -----------------------------------------------------------------------------
# A fixture is a way to provide a fixed baseline or a "known state" upon which
# tests can reliably run. Instead of manually setting up and tearing down
# resources (like database connections, API clients, or temporary files) inside
# every single test function, you define them once in a fixture and "inject"
# them where needed.

# ANALOGY: In a professional kitchen, before the chef (the test) starts
# cooking, a prep cook (the fixture) ensures the stove is on, the pans are
# clean, and the ingredients are chopped. Once the dish is finished, the prep
# cook cleans the station for the next order.

# USAGE:
# 1. The Setup: Everything before the yield statement. This is where we create
# the resource (e.g., creating the in-memory SQLite database).
#
# 2. The Injection: The yield keyword "hands over" the resource to the test
# function. The test runs while the fixture waits.
#
# 3. The Teardown: Everything after the yield. Once the test finishes (even if
# it fails), Python returns to the fixture to clean up (e.g., closing the
# database session).
@pytest.fixture
def db_session():
    """
    Creates a fresh, in-memory SQLite database for every single test.
    """
    # Use sqlite :memory: for ultra-fast, isolated testing without side effects.
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    session = Session()
    yield session  # Provide the session to the test (the injection stage)
    session.close()

## -----------------------------------------------------------------------------
## UNIT TESTS
## -----------------------------------------------------------------------------

def test_save_order_to_db_valid_data(db_session):
    """
    Tests that save_order_to_db correctly persists a record.
    """
    sample_data = {
        'order_id': '123',
        'client_fname': 'Aisha',
        'item': 'Spinach',
        'order_quantity': 5
    }

    # Act
    save_order_to_db(db_session, sample_data)

    # Assert
    queried_record = db_session.query(Order).filter_by(order_id='123').first()
    assert queried_record is not None
    assert queried_record.client_fname == "Aisha"
    assert queried_record.order_quantity == 5

def test_save_order_duplicate_id_fails(db_session):
    """
    Ensures primary key constraints prevent duplicate Order IDs.
    """
    sample_data = {
        'order_id': 'duplicate-1',
        'client_fname': 'Test',
        'item': 'Spinach',
        'order_quantity': 1
    }

    # First save
    save_order_to_db(db_session, sample_data)

    # Second save should raise IntegrityError
    from sqlalchemy.exc import IntegrityError
    with pytest.raises(IntegrityError):
        save_order_to_db(db_session, sample_data)
        db_session.commit() # SQLite requires a flush/commit to trigger the PK error
