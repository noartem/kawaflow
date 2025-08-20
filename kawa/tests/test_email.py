from kawa.email import SendEmailEvent


def test_send_email_event_creation():
    event = SendEmailEvent(message="Test message")
    assert event.message == "Test message"


def test_send_email_event_empty_message():
    event = SendEmailEvent(message="")
    assert event.message == ""
