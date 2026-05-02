import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
# Import the actual config and TZ object from your producer
from producer_order import create_order, TZ, TIMEZONE_NAME, ITEMS, CLIENTS


## -----------------------------------------------------------------------------
## UNIT TESTS: Order Generation Logic (Dynamic)
## -----------------------------------------------------------------------------

def test_create_order_timezone_dynamic():
    """
    Verifies that the 'produced_at' timestamp reflects the offset
    of the currently configured TIMEZONE_NAME.
    """
    order = create_order()
    timestamp_str = order['produced_at']

    # 1. Parse the produced timestamp
    dt = datetime.fromisoformat(timestamp_str)

    # 2. Get the expected offset for the current TZ at this specific time
    # This handles Daylight Savings Time automatically if the TZ supports it.
    expected_offset = datetime.now(TZ).strftime('%z')
    # Format the offset to match ISO 8601 (e.g., +0100 to +01:00)
    formatted_offset = f"{expected_offset[:3]}:{expected_offset[3:]}"

    # 3. Assert that the generated timestamp contains the correct offset
    assert formatted_offset in timestamp_str, \
        f"Expected offset {formatted_offset} for {TIMEZONE_NAME}, but got {timestamp_str}"


def test_create_order_structure():
    """
    Ensures all required keys are present for downstream consumers.
    """
    order = create_order()
    required_keys = ['order_id', 'client_fname', 'item', 'order_quantity', 'produced_at']
    assert all(key in order for key in required_keys)


def test_create_order_data_validity():
    """
    Validates that the generated data stays within expected bounds.
    """
    order = create_order()
    assert order['item'] in ITEMS
    assert order['client_fname'] in CLIENTS
    assert 1 <= order['order_quantity']