from .main import event


@event
class SendEmailEvent:
    message: str
