from dataclasses import dataclass

from .core import Event


@dataclass
class SendEmailEvent(Event):
    message: str
