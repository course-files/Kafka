import pytest
import json
from unittest.mock import MagicMock
from consumer_order_notification import process_order_message

## -----------------------------------------------------------------------------
## UNIT TEST: Testing the Process Order Message Logic
## -----------------------------------------------------------------------------

def test_process_order_message_valid_data(capsys):
    """
    Tests the 'success path' where the message object returns valid JSON bytes.
    """
    # 1. Arrange: Create a Mock for the Kafka Message object
    mock_msg = MagicMock()

    # We define what mock_msg.value() should return when called
    raw_data = {
        'order_id': '123',
        'client_fname': 'Jeff',
        'item': 'Managu',
        'order_quantity': 2
    }
    mock_msg.value.return_value = json.dumps(raw_data).encode("utf-8")

    # 2. Act: Pass the Mock object into the function
    process_order_message(mock_msg)

    # 3. Assert: Verify the output was printed to the console correctly
    captured = capsys.readouterr()
    assert "Notification sent" in captured.out
    assert "2 x Managu" in captured.out
    assert "Jeff" in captured.out

def test_process_order_message_missing_field():
    """
    Tests that a KeyError is raised when the JSON is missing required fields.
    """
    # 1. Arrange: Mock a message with incomplete data
    mock_msg = MagicMock()
    incomplete_data = {'order_id': '123'}  # Missing 'item', 'client_fname', etc.
    mock_msg.value.return_value = json.dumps(incomplete_data).encode("utf-8")

    # 2. Act & Assert: Verify the function raises a KeyError
    with pytest.raises(KeyError):
        process_order_message(mock_msg)