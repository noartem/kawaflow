from datetime import timedelta
from typing import Optional
from dataclasses import dataclass

from .core import ActorDefinition, EventDefinition, EventClassOrFilter, ActorFuncOrClass
from .registry import Registry


registry = Registry()


def event(cls):
    registry.register_event(EventDefinition(cls))
    return dataclass(cls)


def actor(
    receivs: Optional[tuple[EventClassOrFilter, ...]] = None,
    sends: Optional[tuple[type[object], ...]] = None,
    min_instances: Optional[int] = None,
    max_instances: Optional[int] = None,
    keep_instance: Optional[timedelta] = None,
):
    def decorator(actorFuncOrClass: ActorFuncOrClass):
        registry.register_actor(
            ActorDefinition(
                actorFuncOrClass=actorFuncOrClass,
                receivs=receivs,
                sends=sends,
                min_instances=min_instances,
                max_instances=max_instances,
                keep_instance=keep_instance,
            )
        )

        return actorFuncOrClass

    return decorator
