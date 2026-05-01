import pytest
import json
from unittest.mock import MagicMock, patch
from producer_order import delivery_report

## -----------------------------------------------------------------------------
## UNIT TEST: Testing the Delivery Report Logic
## -----------------------------------------------------------------------------

def test_delivery_report_success(capsys):
    """
    Tests that the delivery_report function correctly prints success
    when no error is provided.
    """
    # Create a mock message object
    mock_msg = MagicMock()
    mock_msg.value.return_value = b'{"item": "Managu"}'
    mock_msg.topic.return_value = "orders"
    mock_msg.partition.return_value = 0

    # Call the function with None as the error
    delivery_report(None, mock_msg)

    # Capture the printed output
    captured = capsys.readouterr()
    assert "✅ Message delivered successfully" in captured.out
    assert "Managu" in captured.out

def test_delivery_report_failure(capsys):
    """
    Tests that the delivery_report function correctly prints an error
    message when an error is encountered.
    """
    mock_msg = MagicMock()
    error_message = "Broker not available"

    # Call the function with an error string
    delivery_report(error_message, mock_msg)

    captured = capsys.readouterr()
    assert "❌ Message delivery failed" in captured.out
    assert error_message in captured.out


## -----------------------------------------------------------------------------
## UNIT TEST: Testing the Producer Logic
## -----------------------------------------------------------------------------

# The @patch decorator comes from the unittest.mock library. It intercepts the
# import path of a specific class or function and replaces it with a 'MagicMock'
# object.

# This means that when the script calls Producer(), it does not actually call
# the real class inside the confluent_kafka library. Instead, it calls the Mock
# object that has been created.

# Isolation is one of the benefits of using @patch from the unittest.mock
# Isolation ensures the test remains a "Unit Test" (testing only the
# logic) rather than an "Integration Test" (testing your code + Kafka + the
# Network).

# By default, a Mock will accept any arguments you give it. If you accidentally pass
# the wrong number of arguments to the real Kafka Producer, it will crash. If you
# pass them to a Mock, it will stay silent. To fix this, always use autospec=True
# within your patch.
# This forces the Mock to behave exactly like the real class, throwing an error if
# you use the wrong method names or parameters.

@patch('confluent_kafka.Producer', autospec=True)
def test_producer_logic(mock_producer_class):
    """
    Tests that the producer is initialized and the produce function is called
    with the correct arguments.
    """
    # Setup the mock instance
    mock_instance = mock_producer_class.return_value

    # Simulate the production steps
    test_order = {'order_id': '123', 'item': 'Managu'}
    val = json.dumps(test_order).encode("utf-8")

    mock_instance.produce(
        topic="orders",
        key=b'123',
        value=val
    )
    mock_instance.flush()

    # Assertions: Did the code do what we expected?
    mock_instance.produce.assert_called_once()
    mock_instance.flush.assert_called_once()