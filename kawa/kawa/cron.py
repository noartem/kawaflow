from datetime import datetime
from dataclasses import dataclass

from .core import EventFilter
from .main import event


@event
@dataclass
class CronEvent:
    template: str
    datetime: datetime

    @staticmethod
    def by(template: str):
        return EventFilter(
            CronEvent, {"template": template}, lambda e: e.template == template
        )
