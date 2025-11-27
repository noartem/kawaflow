from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Dict, List, Optional

from system_logger import SystemLogger

CommandHandler = Callable[[Dict[str, Any], Any], Awaitable[None]]


class Messaging(ABC):
    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def close(self) -> None: ...

    @abstractmethod
    async def publish_event(
        self,
        event_name: str,
        payload: Dict[str, Any],
        routing_key: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> None: ...

    @abstractmethod
    async def publish_response(
        self,
        action: str,
        payload: Dict[str, Any],
        reply_to: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> None: ...

    @abstractmethod
    async def consume_commands(self, handler: CommandHandler) -> None: ...

    @abstractmethod
    async def stop_consuming(self) -> None: ...


class InMemoryMessaging(Messaging):
    """
    Simple in-memory messaging backend for tests and local dev without a broker.
    """

    def __init__(self, logger: SystemLogger):
        self.logger = logger
        self.published_events: List[Dict[str, Any]] = []
        self.published_responses: List[Dict[str, Any]] = []
        self._handler: Optional[CommandHandler] = None
        self._closed = False

    async def connect(self) -> None:  # pragma: no cover - no-op
        self.logger.debug("InMemoryMessaging connect", {})

    async def close(self) -> None:  # pragma: no cover - no-op
        self._closed = True
        self.logger.debug("InMemoryMessaging close", {})

    async def publish_event(
        self,
        event_name: str,
        payload: Dict[str, Any],
        routing_key: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        self.published_events.append(
            {
                "event": event_name,
                "payload": payload,
                "routing_key": routing_key,
                "correlation_id": correlation_id,
            }
        )
        self.logger.debug(
            "InMemoryMessaging publish_event",
            {"event": event_name, "routing_key": routing_key},
        )

    async def publish_response(
        self,
        action: str,
        payload: Dict[str, Any],
        reply_to: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        self.published_responses.append(
            {
                "action": action,
                "payload": payload,
                "reply_to": reply_to,
                "correlation_id": correlation_id,
            }
        )
        self.logger.debug(
            "InMemoryMessaging publish_response",
            {"action": action, "reply_to": reply_to},
        )

    async def consume_commands(self, handler: CommandHandler) -> None:
        self._handler = handler
        self.logger.debug("InMemoryMessaging consume_commands", {})

    async def stop_consuming(self) -> None:  # pragma: no cover - no-op
        self._handler = None
        self.logger.debug("InMemoryMessaging stop_consuming", {})

    async def emit_command(self, payload: Dict[str, Any]) -> None:
        """Helper to push a command into the handler (test utility)."""
        if not self._handler:
            raise RuntimeError("No command handler registered")
        await self._handler(payload, message=None)


def create_messaging(
    kind: str, logger: Optional[SystemLogger] = None, **kwargs: Any
) -> Messaging:
    """
    Factory for messaging backends.

    Args:
        kind: Backend type (rabbitmq, inmemory)
        logger: Optional SystemLogger
        **kwargs: Transport-specific options
    """

    kind_normalized = (kind or "rabbitmq").lower()

    if kind_normalized == "rabbitmq":
        from rabbitmq_client import RabbitMQMessaging

        return RabbitMQMessaging(logger=logger, **kwargs)
    if kind_normalized == "inmemory":
        return InMemoryMessaging(logger=logger)

    raise ValueError(f"Unsupported messaging backend: {kind}")
