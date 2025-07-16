import json
from datetime import datetime, timedelta
from uuid import UUID

import pytest

from kawa.core import (
    Actor,
    ActorDefinition,
    ActorReceiveEventDefinition,
    ActorSendEventDefinition,
    Context,
    Event,
    EventDefinition,
    EventFilter,
    NotSupportedEvent,
    get_event_from_event_filter,
)
from kawa.cron import CronEvent, CronEventFilter
from kawa.email import SendEmailEvent
from kawa.utils import (
    TimedeltaEncoder,
    get_actor_uuid,
    get_event_uuid,
    get_object_key,
    json_encode,
    untab_string,
)

# Test kawa.core


class MockEvent(Event):
    """Mock Event Docstring"""

    pass


class AnotherMockEvent(Event):
    pass


class MockContext(Context):
    def __init__(self):
        self.dispatched_events = []

    def dispatch(self, event: Event):
        self.dispatched_events.append(event)


class MockEventFilter(EventFilter[MockEvent]):
    def __call__(self, event: MockEvent) -> bool:
        return True

    def get_context(self) -> dict:
        return {"filter_key": "filter_value"}


def test_event_base_class():
    event = Event()
    assert isinstance(event, Event)


def test_not_supported_event():
    original_event = MockEvent()
    not_supported = NotSupportedEvent(original_event)
    assert isinstance(not_supported, NotSupportedEvent)
    assert not_supported.event == original_event


def test_context_dispatch():
    ctx = MockContext()
    event = MockEvent()
    ctx.dispatch(event)
    assert len(ctx.dispatched_events) == 1
    assert ctx.dispatched_events[0] == event


def test_event_filter_abstract_methods():
    class ConcreteEventFilter(EventFilter[MockEvent]):
        def __call__(self, event: MockEvent) -> bool:
            return True

        def get_context(self) -> dict:
            return {}

    # This should not raise an error now
    ConcreteEventFilter()


def test_get_event_from_event_filter():
    event_filter = MockEventFilter()
    event_class = get_event_from_event_filter(event_filter)
    assert event_class == MockEvent


def test_actor_receive_event_definition_from_event_class():
    definition = ActorReceiveEventDefinition.fromEventClassOrFilter(MockEvent)
    assert isinstance(definition, ActorReceiveEventDefinition)
    assert definition.id == get_event_uuid(MockEvent)
    assert definition.name == "MockEvent"
    assert definition.doc == "Mock Event Docstring"
    assert definition.ctx == {}
    assert definition.eventClass == MockEvent
    assert definition.eventClassOrFilter == MockEvent


def test_actor_receive_event_definition_from_event_filter():
    event_filter = MockEventFilter()
    definition = ActorReceiveEventDefinition.fromEventClassOrFilter(event_filter)
    assert isinstance(definition, ActorReceiveEventDefinition)
    assert definition.id == get_event_uuid(MockEvent)
    assert definition.name == "MockEvent"
    assert definition.doc == "Mock Event Docstring"
    assert definition.ctx == {"filter_key": "filter_value"}
    assert definition.eventClass == MockEvent
    assert definition.eventClassOrFilter == event_filter


def test_actor_send_event_definition_from_event_class():
    definition = ActorSendEventDefinition.fromEventClass(MockEvent)
    assert isinstance(definition, ActorSendEventDefinition)
    assert definition.id == get_event_uuid(MockEvent)
    assert definition.name == "MockEvent"
    assert definition.doc == "Mock Event Docstring"
    assert definition.eventClass == MockEvent


def test_actor_decorator():
    @Actor(receivs=(MockEvent,), sends=(AnotherMockEvent,))
    class MyActor:
        def __call__(self, ctx: Context, event: Event):
            pass

    assert isinstance(MyActor, ActorDefinition)
    assert MyActor.name == "MyActor"
    assert len(MyActor.receivs) == 1
    assert MyActor.receivs[0].eventClass == MockEvent
    assert len(MyActor.sends) == 1
    assert MyActor.sends[0].eventClass == AnotherMockEvent


def test_actor_decorator_with_min_max_keep_instances():
    class MyActor:
        def __call__(self, ctx: Context, event: Event):
            pass

    MyActorDefinition = Actor(
        min_instances=1, max_instances=5, keep_instance=timedelta(minutes=10)
    )(MyActor)

    assert MyActorDefinition.min_instances == 1
    assert MyActorDefinition.max_instances == 5
    assert MyActorDefinition.keep_instance == timedelta(minutes=10)


def test_event_definition_from_event_class():
    definition = EventDefinition.fromEventClass(MockEvent)
    assert isinstance(definition, EventDefinition)
    assert definition.id == get_event_uuid(MockEvent)
    assert definition.name == "MockEvent"
    assert definition.doc == "Mock Event Docstring"
    assert definition.eventClass == MockEvent


# Test kawa.cron


def test_cron_event_filter_call():
    event_filter = CronEventFilter(template="* * * * *")
    event = CronEvent(template="* * * * *", datetime=datetime.now())
    assert event_filter(event)

    event_false = CronEvent(template="0 0 * * *", datetime=datetime.now())
    assert not event_filter(event_false)


def test_cron_event_filter_get_context():
    event_filter = CronEventFilter(template="* * * * *")
    assert event_filter.get_context() == {"template": "* * * * *"}


def test_cron_event_by_static_method():
    event_filter = CronEvent.by("0 0 * * *")
    assert isinstance(event_filter, CronEventFilter)
    assert event_filter.template == "0 0 * * *"


def test_cron_event_init():
    now = datetime.now()
    event = CronEvent(template="* * * * *", datetime=now)
    assert event.template == "* * * * *"
    assert event.datetime == now


# Test kawa.email


def test_send_email_event_init():
    event = SendEmailEvent(message="Hello, world!")
    assert event.message == "Hello, world!"


# Test kawa.utils


def test_untab_string():
    assert untab_string("  hello") == "hello"
    assert untab_string("\tworld") == "world"
    assert untab_string("    indented\n  text") == "indented\ntext"
    assert untab_string("no indent") == "no indent"


def test_get_object_key():
    class TempClass:
        pass

    assert get_object_key(TempClass).startswith(__file__)
    assert get_object_key(TempClass).endswith("::TempClass")


def test_get_actor_uuid():
    class TempActor:
        pass

    uuid = get_actor_uuid(TempActor)
    assert isinstance(uuid, UUID)


def test_get_event_uuid():
    class TempEvent:
        pass

    uuid = get_event_uuid(TempEvent)
    assert isinstance(uuid, UUID)


def test_timedelta_encoder():
    encoder = TimedeltaEncoder()
    assert encoder.default(timedelta(seconds=60)) == 60
    assert encoder.default(timedelta(minutes=2)) == 120
    assert (
        encoder.default(UUID("12345678-1234-5678-1234-567812345678"))
        == "12345678-1234-5678-1234-567812345678"
    )
    with pytest.raises(TypeError):
        encoder.default("not a timedelta")


def test_json_encode():
    data = {
        "duration": timedelta(seconds=30),
        "id": UUID("12345678-1234-5678-1234-567812345678"),
    }
    encoded = json_encode(data)
    expected = json.dumps(
        {"duration": 30, "id": "12345678-1234-5678-1234-567812345678"}, indent=4
    )
    assert encoded == expected
