import pytest
import json
from unittest.mock import MagicMock
from consumer_order_notification import process_order, consumer_config

def test_process_order_success():
    """
    Success Path: Tests that a valid Kafka message is correctly 
    transformed into a notification string.
    """
    # 1. Arrange: Create a Mock Message object
    mock_msg = MagicMock()

    sample_data = {
        'client_fname': 'Jane',
        'order_quantity': 3,
        'item': 'Spinach',
        'order_id': '123'
    }

    # Configure the mock to behave like a real confluent_kafka Message
    mock_msg.value.return_value = json.dumps(sample_data).encode("utf-8")
    mock_msg.error.return_value = None
    mock_msg.partition.return_value = 0

    # 2. Act: Call the function with our mock
    result = process_order(mock_msg)

    # 3. Assert: Verify the output matches our expectations
    assert "To        : Jane" in result
    assert "3 x Spinach" in result
    assert "Order ID  : 123" in result


def test_process_order_with_error():
    """
    Error Path: Tests that the function handles Kafka errors gracefully.
    """
    mock_msg = MagicMock()
    mock_msg.error.return_value = "Broker: Not available"

    result = process_order(mock_msg)

    assert "Error" in result
    assert "Broker: Not available" in result


def test_consumer_settings():
    """
    Configuration Check: Verifies that crucial Kafka settings are present.
    """
    assert consumer_config["group.id"] == "order-notifiers"
    assert consumer_config["auto.offset.reset"] == "earliest"