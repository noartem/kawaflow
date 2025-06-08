from dataclasses import dataclass
from datetime import datetime
from typing import final

from .core import Event, EventFilter


@final
@dataclass
class CronEventFilter(EventFilter["CronEvent"]):
    template: str

    def __call__(self, event: "CronEvent") -> bool:
        return event.template == self.template

    def get_context(self):
        return {"template": self.template}


@final
@dataclass
class CronEvent(Event):
    """
    Just CRON
    """

    template: str
    datetime: datetime

    @staticmethod
    def by(template: str) -> CronEventFilter:
        return CronEventFilter(template)
