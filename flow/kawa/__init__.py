from .core import Actor
from .module import Module

__all__ = ["Actor", "Event", "Module"]

module = Module()

def Event(cls):
    module.register_event(cls)
    return cls
