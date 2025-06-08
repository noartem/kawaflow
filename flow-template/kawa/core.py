import sys
from abc import abstractmethod
from dataclasses import dataclass
from datetime import timedelta
from types import get_original_bases
from typing import (
    Callable,
    Generic,
    Optional,
    Protocol,
    TypeVar,
    Union,
    final,
    get_args,
)
from uuid import UUID

from .utils import (
    get_actor_uuid,
    get_event_uuid,
    untab_string,
)


class Event:
    pass


@final
class NotSupportedEvent(Event):
    def __init__(self, event: Event):
        self.event = event


class Context:
    def dispatch(self, event: Event):
        pass


EventFilterT = TypeVar("EventFilterT", bound=Event)
EventFilterContext = dict[str, str]


class EventFilter(Generic[EventFilterT]):
    @abstractmethod
    def __call__(event: EventFilterT) -> bool:
        pass

    @abstractmethod
    def get_context() -> EventFilterContext:
        return {}


class ActorClassProtocol(Protocol):
    def __call__(self, ctx: Context, event: Event) -> None:
        pass


EventClassOrFilter = Union[type[Event], type[EventFilter]]


def get_event_from_event_filter(eventFilter: EventFilter):
    forward_ref = get_args(get_original_bases(eventFilter.__class__)[0])[0]

    globalns = sys.modules[eventFilter.__class__.__module__].__dict__
    localns = {}

    return forward_ref._evaluate(
        globalns, localns, recursive_guard=set(), type_params=None
    )


@dataclass
class ActorReceiveEventDefinition:
    id: UUID
    name: str
    doc: str

    ctx: EventFilterContext

    eventClass: type[Event]
    eventClassOrFilter: EventClassOrFilter

    @staticmethod
    def fromEventClassOrFilter(eventClassOrFilter: EventClassOrFilter):
        if isinstance(eventClassOrFilter, EventFilter):
            eventClass = get_event_from_event_filter(eventClassOrFilter)
            ctx = eventClassOrFilter.get_context()
        else:
            eventClass = eventClassOrFilter
            ctx = {}

        doc = eventClass.__doc__
        if doc is None:
            doc = ""

        return ActorReceiveEventDefinition(
            id=get_event_uuid(eventClass),
            name=eventClass.__name__,
            doc=untab_string(doc).strip(),
            ctx=ctx,
            eventClass=eventClass,
            eventClassOrFilter=eventClassOrFilter,
        )


@dataclass
class ActorSendEventDefinition:
    id: UUID
    name: str
    doc: str

    eventClass: type[Event]

    @staticmethod
    def fromEventClass(eventClass: type[Event]):
        doc = eventClass.__doc__
        if doc is None:
            doc = ""

        return ActorSendEventDefinition(
            id=get_event_uuid(eventClass),
            name=eventClass.__name__,
            doc=untab_string(doc).strip(),
            eventClass=eventClass,
        )


ActorProtocol = Union[Callable[[Context, Event], None], ActorClassProtocol]


@dataclass
class ActorDefinition:
    id: UUID
    name: str
    doc: str

    funcOrClass: ActorProtocol

    receivs: list[ActorReceiveEventDefinition]
    sends: list[ActorSendEventDefinition]
    min_instances: int
    max_instances: int
    keep_instance: timedelta


@dataclass
class Actor:
    receivs: Optional[tuple[EventClassOrFilter, ...]] = None
    sends: Optional[tuple[type[Event], ...]] = None
    min_instances: Optional[int] = None
    max_instances: Optional[int] = None
    keep_instance: Optional[timedelta] = None

    funcOrClass: Optional[ActorProtocol] = None

    def __call__(self, funcOrClass):
        definition = ActorDefinition(
            id=get_actor_uuid(funcOrClass),
            name=funcOrClass.__name__,
            doc=untab_string(funcOrClass.__doc__).strip(),
            funcOrClass=funcOrClass,
            receivs=[
                ActorReceiveEventDefinition.fromEventClassOrFilter(receive)
                for receive in getattr(self, "receivs", tuple())
            ],
            sends=[
                ActorSendEventDefinition.fromEventClass(send)
                for send in getattr(self, "sends", tuple())
            ],
            min_instances=self.min_instances,
            max_instances=self.max_instances,
            keep_instance=self.keep_instance,
        )

        return definition


@dataclass
class EventDefinition:
    id: UUID
    name: str
    doc: str

    eventClass: type[Event]

    @staticmethod
    def fromEventClass(eventClass: type[Event]):
        doc = eventClass.__doc__
        if doc is None:
            doc = ""

        return EventDefinition(
            id=get_event_uuid(eventClass),
            name=eventClass.__name__,
            doc=untab_string(doc).strip(),
            eventClass=eventClass,
        )
