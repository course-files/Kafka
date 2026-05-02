import pytest
import json
from unittest.mock import MagicMock, patch
from producer_order import create_order, delivery_report


def test_create_order_structure():
    """
    Tests that the order generator creates a valid dictionary
    with all required Kafka keys.
    """
    order = create_order()

    # Assertions verify the 'Contract' of the order object
    assert isinstance(order, dict)
    assert "order_id" in order
    assert "item" in order
    assert 1 <= order['order_quantity'] <= 8
    # Ensure order_id is a valid UUID string
    assert len(order['order_id']) == 36


def test_delivery_report_success(capsys):
    """
    Tests the delivery_report function by mocking a Kafka Message object.
    """
    # Create a mock message
    mock_msg = MagicMock()
    sample_order = {
        'order_id': '123',
        'item': 'Matoke',
        'order_quantity': 5,
        'client_fname': 'Wanjiru'
    }
    mock_msg.value.return_value = json.dumps(sample_order).encode("utf-8")
    mock_msg.topic.return_value = "orders"
    mock_msg.partition.return_value = 1
    mock_msg.offset.return_value = 100

    # Call with err=None (Success case)
    delivery_report(None, mock_msg)

    captured = capsys.readouterr()
    assert "Order produced" in captured.out
    assert "Order ID  : 123" in captured.out
    assert "Topic     : orders" in captured.out
    assert "Partition : 1" in captured.out

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
def test_producer_configuration(mock_producer_class):
    """
    Tests that the Producer is initialized with the 'acks': 'all' setting.
    """
    import producer_order
    # We simulate calling the main logic (conceptually)
    # This verifies the config dictionary matches our requirements
    assert producer_order.producer_config['acks'] == 'all'
    assert 'bootstrap.servers' in producer_order.producer_config