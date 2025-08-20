from .main import event
from dataclasses import dataclass


@event
@dataclass
class SendEmailEvent:
    message: str
