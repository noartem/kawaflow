import re

import importlib
from kawa.core import ActorDefinition, EventDefinition, Event, NotSupportedEvent
from kawa.cron import CronEvent
from kawa.utils import json_encode, get_event_uuid

import importlib.util
import sys


def import_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        raise Exception(f"Invalid module path: {file_path}. Failed to create spec")

    if not hasattr(spec.loader, "exec_module"):
        raise Exception(f"Invalid module path: {file_path}. Invalid loader")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)  # ty: ignore[possibly-unbound-attribute]

    return module


class Module:
    _PRIVATE_EVENTS = (
        get_event_uuid(NotSupportedEvent),
        get_event_uuid(CronEvent),
    )

    def __init__(self, path: str):
        self.path = path

        self.actors = {}
        self.events = {}
        self._load()

        self.commands: list[str] = []
        self._load_commands()

    def _load(self):
        module = import_from_path("", self.path)

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, ActorDefinition):
                if attr.id in self.actors:
                    continue

                self.actors[attr.id] = attr

                for event in attr.receivs:
                    eventDef = EventDefinition.fromEventClass(event.eventClass)
                    if eventDef.id in self.events:
                        continue
                    self.events[eventDef.id] = eventDef

                for event in attr.sends:
                    eventDef = EventDefinition.fromEventClass(event.eventClass)
                    if eventDef.id in self.events:
                        continue
                    self.events[eventDef.id] = eventDef

            elif isinstance(attr, type) and issubclass(attr, Event):
                eventDef = EventDefinition.fromEventClass(attr)
                if eventDef.id in self.events:
                    continue
                self.events[eventDef.id] = eventDef

    def _load_commands(self):
        HASHBANG_PATTERN = re.compile(r"^#!(.*)")

        with open(self.path, "r", encoding="utf-8") as file:
            for line in file:
                match = HASHBANG_PATTERN.match(line.strip())
                if not match:
                    continue

                command = match.group(1).strip()
                self.commands.append(command)

    def _event_to_dict(self, event: EventDefinition):
        return {
            "id": event.id,
            "name": event.name,
            "doc": event.doc,
            "private": event.id in self._PRIVATE_EVENTS,
        }

    def _actor_to_dict(self, actor: ActorDefinition):
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

    def to_dict(self):
        return {
            "events": [self._event_to_dict(x) for x in self.events.values()],
            "actors": [self._actor_to_dict(x) for x in self.actors.values()],
        }


if __name__ == "__main__":
    module = Module("main.py")
    print(json_encode(module.to_dict()))

    # print(json_encode(read_commands("./main.py")))

    # module = actors.load_module('./main.py')

    # module.add(CronActor, external=True)
    # module.add(EmailActor, external=True)

    # module.dispatch(CronEvent("0 8 * * *", datetime.now()), as=CronActor)

    # #module.definition() -> Actors, Events, connections
    # # filter not used
