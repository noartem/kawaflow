from .core import Actor
from .system import System

__all__ = ["Actor", "Event", "System"]

system = System()

def Event(cls):
    system.register_event(cls)
    return cls
