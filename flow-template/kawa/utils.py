import json
import re
from datetime import timedelta
from sys import modules
from typing import Protocol
from uuid import NAMESPACE_DNS, UUID, uuid5

actors_namespace = uuid5(NAMESPACE_DNS, "actors")
events_namespace = uuid5(NAMESPACE_DNS, "events")


def untab_string(s: str) -> str:
    return re.sub(r"^(?: {2}| {4}|\t)+", "", s, flags=re.MULTILINE)


class HasName(Protocol):
    __name__: str


def get_object_key(obj: HasName) -> str:
    module_name = obj.__module__
    module = modules[module_name]
    file_path = getattr(module, "__file__", module_name)
    return f"{file_path}::{obj.__name__}"


def get_actor_uuid(obj: HasName) -> UUID:
    return uuid5(actors_namespace, get_object_key(obj))


def get_event_uuid(obj: HasName) -> UUID:
    return uuid5(events_namespace, get_object_key(obj))


class TimedeltaEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, timedelta):
            return int(obj.total_seconds())
        elif isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


def json_encode(obj):
    return json.dumps(obj, indent=4, cls=TimedeltaEncoder)
