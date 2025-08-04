from kawa.core import ActorDefinition, Event, EventDefinition, NotSupportedEvent
from kawa.cron import CronEvent
from kawa.utils import get_event_uuid





class System:
    _PRIVATE_EVENTS = (
        get_event_uuid(NotSupportedEvent),
        get_event_uuid(CronEvent),
    )

    def __init__(self):
        self.actors = {}
        self.events = {}

    def register_event(self, event_class):
        event_def = EventDefinition.fromEventClass(event_class)
        if event_def.id in self.events:
            return
        self.events[event_def.id] = event_def

    def _dump_event(self, event: EventDefinition):
        return {
            "id": event.id,
            "name": event.name,
            "doc": event.doc,
            "private": event.id in self._PRIVATE_EVENTS,
        }

    def _dump_actor(self, actor: ActorDefinition):
        return {
            "id": actor.id,
            "name": actor.name,
            "doc": actor.doc,
            "receives": [
                {
                    "id": receive.id,
                    "ctx": receive.ctx,
                }
                for receive in actor.receivs
            ],
            "sends": [
                {
                    "id": send.id,
                }
                for send in actor.sends
            ],
            "min_instances": actor.min_instances,
            "max_instances": actor.max_instances,
            "keep_instance": actor.keep_instance,
        }

    def dump(self):
        return {
            "events": [self._dump_event(x) for x in self.events.values()],
            "actors": [self._dump_actor(x) for x in self.actors.values()],
        }
