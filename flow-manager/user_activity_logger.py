"""
User Activity Logger for Container Lifecycle Management

This module provides user-friendly activity logging that emits events to Socket.IO clients.
It filters sensitive information and provides clear, actionable messages for users.
"""

import socketio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Set


class UserActivityLogger:
    """
    User-friendly activity logger that emits to Socket.IO clients.

    This logger focuses on user-visible events and activities, providing
    clear messages about container operations and system status changes.
    """

    def __init__(self, sio: socketio.AsyncServer):
        """
        Initialize the UserActivityLogger.

        Args:
            sio: Socket.IO server instance for emitting events
        """
        self.sio = sio

    async def log_container_created(
        self, container_id: str, name: str, image: Optional[str] = None
    ) -> None:
        """
        Log container creation activity.

        Args:
            container_id: Container identifier
            name: Container name
            image: Docker image name (optional)
        """
        message = f"Container '{name}' created successfully"
        details = {"container_id": container_id, "name": name, "status": "created"}
        if image:
            details["image"] = image

        await self._emit_activity_log(
            "container_created", container_id, message, details
        )

    async def log_container_started(self, container_id: str, name: str) -> None:
        """
        Log container start activity.

        Args:
            container_id: Container identifier
            name: Container name
        """
        message = f"Container '{name}' started and is now running"
        details = {"container_id": container_id, "name": name, "status": "running"}
        await self._emit_activity_log(
            "container_started", container_id, message, details
        )

    async def log_container_stopped(self, container_id: str, name: str) -> None:
        """
        Log container stop activity.

        Args:
            container_id: Container identifier
            name: Container name
        """
        message = f"Container '{name}' stopped successfully"
        details = {"container_id": container_id, "name": name, "status": "stopped"}
        await self._emit_activity_log(
            "container_stopped", container_id, message, details
        )

    async def log_container_restarted(self, container_id: str, name: str) -> None:
        """
        Log container restart activity.

        Args:
            container_id: Container identifier
            name: Container name
        """
        message = f"Container '{name}' restarted successfully"
        details = {"container_id": container_id, "name": name, "status": "running"}
        await self._emit_activity_log(
            "container_restarted", container_id, message, details
        )

    async def log_container_updated(self, container_id: str, name: str) -> None:
        """
        Log container update activity.

        Args:
            container_id: Container identifier
            name: Container name
        """
        message = f"Container '{name}' updated with new code"
        details = {"container_id": container_id, "name": name, "status": "updated"}
        await self._emit_activity_log(
            "container_updated", container_id, message, details
        )

    async def log_container_deleted(self, container_id: str, name: str) -> None:
        """
        Log container deletion activity.

        Args:
            container_id: Container identifier
            name: Container name
        """
        message = f"Container '{name}' deleted and resources cleaned up"
        details = {"container_id": container_id, "name": name, "status": "deleted"}
        await self._emit_activity_log(
            "container_deleted", container_id, message, details
        )

    async def log_container_message(
        self,
        container_id: str,
        message_data: Dict[str, Any],
        direction: str = "received",
    ) -> None:
        """
        Log container message activity.

        Args:
            container_id: Container identifier
            message_data: Message content (will be filtered for sensitive data)
            direction: Message direction ("sent" or "received")
        """
        # Filter sensitive information from message
        filtered_message = self._filter_sensitive_data(message_data)

        action = "sent to" if direction == "sent" else "received from"
        message = f"Message {action} container"

        # Extract message type from original data before filtering
        message_type = "unknown"
        if isinstance(message_data, dict):
            message_type = message_data.get(
                "type", message_data.get("command", "unknown")
            )

        details = {
            "container_id": container_id,
            "direction": direction,
            "message_type": message_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Only include message content if it's not sensitive
        if not self._contains_sensitive_data(message_data):
            details["message_preview"] = (
                str(filtered_message)[:100] + "..."
                if len(str(filtered_message)) > 100
                else str(filtered_message)
            )

        await self._emit_activity_log(
            "container_message", container_id, message, details
        )

    async def log_actor_event(
        self,
        container_id: str,
        actor: str,
        event: str,
        event_data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log actor system events from containers.

        Args:
            container_id: Container identifier
            actor: Actor name or identifier
            event: Event type
            event_data: Event data (optional, will be filtered)
        """
        message = f"Actor '{actor}' triggered event '{event}'"
        details = {
            "container_id": container_id,
            "actor": actor,
            "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if event_data:
            filtered_data = self._filter_sensitive_data(event_data)
            details["event_data"] = filtered_data

        await self._emit_activity_log("actor_event", container_id, message, details)

    async def log_container_error(
        self, container_id: str, error_message: str, operation: Optional[str] = None
    ) -> None:
        """
        Log container error activity.

        Args:
            container_id: Container identifier
            error_message: User-friendly error message
            operation: Operation that failed (optional)
        """
        if operation:
            message = f"Error during {operation}: {error_message}"
        else:
            message = f"Container error: {error_message}"

        details = {
            "container_id": container_id,
            "error": True,
            "operation": operation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        await self._emit_activity_log("container_error", container_id, message, details)

    async def log_user_activity(
        self,
        activity_type: str,
        container_id: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log general user activity.

        Args:
            activity_type: Type of activity
            container_id: Container identifier
            message: User-friendly message
            details: Additional details (optional, will be filtered)
        """
        filtered_details = self._filter_sensitive_data(details) if details else {}
        await self._emit_activity_log(
            activity_type, container_id, message, filtered_details
        )

    async def _emit_activity_log(
        self,
        activity_type: str,
        container_id: str,
        message: str,
        details: Dict[str, Any],
    ) -> None:
        """
        Emit activity log event to all connected Socket.IO clients.

        Args:
            activity_type: Type of activity
            container_id: Container identifier
            message: User-friendly message
            details: Activity details
        """
        activity_log = {
            "type": activity_type,
            "container_id": container_id,
            "message": message,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Emit to all connected clients
        await self.sio.emit("activity_log", activity_log)

    def _filter_sensitive_data(
        self, data: Any, _seen: Optional[Set[int]] = None
    ) -> Any:
        """
        Filter sensitive information from data before logging.

        Args:
            data: Data to filter
            _seen: Set of object IDs to prevent circular references (internal use)

        Returns:
            Filtered data with sensitive information removed or masked
        """
        if data is None:
            return None

        # Initialize seen set on first call
        if _seen is None:
            _seen = set()

        # Check for circular references
        data_id = id(data)
        if data_id in _seen:
            return "[CIRCULAR_REFERENCE]"

        try:
            if isinstance(data, dict):
                _seen.add(data_id)
                filtered = {}
                for key, value in data.items():
                    if self._is_sensitive_key(key) and not isinstance(
                        value, (dict, list)
                    ):
                        # Only filter leaf values, not nested structures
                        filtered[key] = "[FILTERED]"
                    else:
                        filtered[key] = self._filter_sensitive_data(value, _seen)
                _seen.remove(data_id)
                return filtered

            elif isinstance(data, list):
                _seen.add(data_id)
                result = [self._filter_sensitive_data(item, _seen) for item in data]
                _seen.remove(data_id)
                return result

            elif isinstance(data, str):
                # Check for potential sensitive patterns in strings
                if self._contains_sensitive_pattern(data):
                    return "[FILTERED]"
                return data

            else:
                return data

        except (RecursionError, RuntimeError):
            # Handle any recursion errors gracefully
            return "[RECURSION_ERROR]"

    def _is_sensitive_key(self, key: str) -> bool:
        """
        Check if a key contains sensitive information.

        Args:
            key: Key name to check

        Returns:
            True if key is considered sensitive
        """
        # Exact matches for sensitive keys
        exact_sensitive_keys = {
            "password",
            "passwd",
            "pwd",
            "secret",
            "token",
            "auth",
            "authorization",
            "credential",
            "private",
            "session",
            "cookie",
            "jwt",
            "bearer",
        }

        # Keys that contain these patterns
        sensitive_patterns = {
            "api_key",
            "access_token",
            "refresh_token",
            "private_key",
            "secret_key",
            "auth_token",
            "session_token",
            "bearer_token",
            "jwt_token",
        }

        key_lower = key.lower()

        # Check exact matches
        if key_lower in exact_sensitive_keys:
            return True

        # Check patterns
        return any(pattern in key_lower for pattern in sensitive_patterns)

    def _contains_sensitive_pattern(self, text: str) -> bool:
        """
        Check if text contains sensitive patterns.

        Args:
            text: Text to check

        Returns:
            True if text contains sensitive patterns
        """
        # Simple patterns for common sensitive data
        sensitive_patterns = [
            "password=",
            "token=",
            "key=",
            "secret=",
            "auth=",
            "Bearer ",
            "Basic ",
            "jwt:",
            "api_key:",
        ]

        text_lower = text.lower()
        return any(pattern.lower() in text_lower for pattern in sensitive_patterns)

    def _contains_sensitive_data(self, data: Any) -> bool:
        """
        Check if data structure contains sensitive information.

        Args:
            data: Data to check

        Returns:
            True if data contains sensitive information
        """
        if isinstance(data, dict):
            return any(
                self._is_sensitive_key(key) or self._contains_sensitive_data(value)
                for key, value in data.items()
            )
        elif isinstance(data, list):
            return any(self._contains_sensitive_data(item) for item in data)
        elif isinstance(data, str):
            return self._contains_sensitive_pattern(data)
        else:
            return False
