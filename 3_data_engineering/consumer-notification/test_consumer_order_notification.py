import pytest
import json
from unittest.mock import MagicMock
from consumer_order_notification import process_order

## -----------------------------------------------------------------------------
## UNIT TEST: Notification Logic
## -----------------------------------------------------------------------------

def test_process_order_logic():
    """
    Tests that process_order correctly parses the JSON value and
    formats the notification string as expected.
    """
    # 1. Arrange: Create a mock Kafka message
    # We create a fake object and define what its methods should return.
    mock_msg = MagicMock()

    sample_payload = {
        "order_id": "123",
        "client_fname": "Osman",
        "item": "Jollof Rice",
        "order_quantity": 2
    }

    # Simulate the .value() method returning JSON bytes
    mock_msg.value.return_value = json.dumps(sample_payload).encode("utf-8")

    # Simulate the .partition() method returning a specific partition number
    mock_msg.partition.return_value = 1

    # 2. Act: Call the function with our fake message
    result = process_order(mock_msg)

    # 3. Assert: Verify the output contains the correct details
    assert "To        : Osman" in result
    assert "2 x Jollof Rice" in result
    assert "Order ID  : 123" in result
    assert "Partition : 1" in result


def test_process_order_missing_key():
    """
    Tests how the function behaves if a required key is missing.
    This shows the importance of data validation.
    """
    mock_msg = MagicMock()
    incomplete_payload = {"item": "Spinach"}  # Missing client_fname and others
    mock_msg.value.return_value = json.dumps(incomplete_payload).encode("utf-8")

    # We expect a KeyError because the function tries to access order['client_fname']
    with pytest.raises(KeyError):
        process_order(mock_msg)
