"""
System Logger for Container Lifecycle Management

Provides comprehensive technical logging for debugging and monitoring
container operations, Socket.IO events, and system state changes.
"""

import logging
import json
import traceback
from datetime import datetime, timezone
from typing import Dict, Any
from enum import Enum


class LogLevel(Enum):
    """Log levels for structured logging"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SystemLogger:
    """
    System logger for detailed technical logging of container operations,
    Socket.IO events, and system state changes.

    Provides structured logging with appropriate levels, error handling with
    full context and stack traces, and debug logging for troubleshooting.
    """

    def __init__(self, logger_name: str = "flow_manager_system"):
        """
        Initialize the SystemLogger with structured logging configuration.

        Args:
            logger_name: Name for the logger instance
        """
        self.logger = logging.getLogger(logger_name)
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up structured logging with appropriate levels and formatting"""
        # Set logger level to DEBUG to capture all messages
        self.logger.setLevel(logging.DEBUG)

        # Prevent duplicate logs if handler already exists
        if self.logger.handlers:
            return

        # Create console handler with structured formatting
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # Create detailed formatter for structured logging
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)

    def _format_log_data(self, **kwargs) -> str:
        """
        Format log data as structured JSON for consistent logging.

        Args:
            **kwargs: Key-value pairs to include in log data

        Returns:
            JSON formatted string of log data
        """
        log_data = {"timestamp": datetime.now(timezone.utc).isoformat(), **kwargs}

        try:
            return json.dumps(log_data, default=str, separators=(",", ":"))
        except (TypeError, ValueError) as e:
            # Fallback to string representation if JSON serialization fails
            return f"LOG_SERIALIZATION_ERROR: {str(e)} | DATA: {str(log_data)}"

    def log_container_operation(
        self, operation: str, container_id: str, details: Dict[str, Any]
    ) -> None:
        """
        Log container operations with timestamp, container ID, and operation details.

        Args:
            operation: The container operation being performed (create, start, stop, etc.)
            container_id: ID of the container being operated on
            details: Additional operation details and context
        """
        try:
            log_message = self._format_log_data(
                event_type="container_operation",
                operation=operation,
                container_id=container_id,
                details=details,
            )

            self.logger.info(f"CONTAINER_OP | {log_message}")

        except Exception as e:
            # Ensure logging failures don't break the system
            self._log_logging_error(
                "log_container_operation",
                e,
                {
                    "operation": operation,
                    "container_id": container_id,
                    "details": str(details),
                },
            )

    def log_socket_event(self, event: str, sid: str, data: Dict[str, Any]) -> None:
        """
        Log Socket.IO events and responses with full context.

        Args:
            event: Socket.IO event name
            sid: Socket session ID
            data: Event data payload
        """
        try:
            log_message = self._format_log_data(
                event_type="socket_event", event=event, session_id=sid, data=data
            )

            self.logger.info(f"SOCKET_EVENT | {log_message}")

        except Exception as e:
            self._log_logging_error(
                "log_socket_event", e, {"event": event, "sid": sid, "data": str(data)}
            )

    def log_communication(
        self, container_id: str, direction: str, message: Dict[str, Any]
    ) -> None:
        """
        Log Unix socket communication for debugging.

        Args:
            container_id: ID of the container being communicated with
            direction: Communication direction ("send" or "receive")
            message: Message content being sent or received
        """
        try:
            log_message = self._format_log_data(
                event_type="socket_communication",
                container_id=container_id,
                direction=direction,
                message=message,
            )

            self.logger.debug(f"SOCKET_COMM | {log_message}")

        except Exception as e:
            self._log_logging_error(
                "log_communication",
                e,
                {
                    "container_id": container_id,
                    "direction": direction,
                    "message": str(message),
                },
            )

    def log_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """
        Log detailed error information including stack traces and context.

        Args:
            error: The exception that occurred
            context: Additional context about when/where the error occurred
        """
        try:
            # Get full stack trace
            stack_trace = traceback.format_exc()

            log_message = self._format_log_data(
                event_type="error",
                error_type=type(error).__name__,
                error_message=str(error),
                stack_trace=stack_trace,
                context=context,
            )

            self.logger.error(f"ERROR | {log_message}")

        except Exception as e:
            # Critical fallback - use basic logging if structured logging fails
            self.logger.error(
                f"LOGGING_ERROR in log_error: {str(e)} | Original error: {str(error)}"
            )

    def log_state_change(
        self, container_id: str, old_state: str, new_state: str
    ) -> None:
        """
        Log container state transitions with relevant metadata.

        Args:
            container_id: ID of the container whose state changed
            old_state: Previous container state
            new_state: New container state
        """
        try:
            log_message = self._format_log_data(
                event_type="state_change",
                container_id=container_id,
                old_state=old_state,
                new_state=new_state,
                transition=f"{old_state} -> {new_state}",
            )

            self.logger.info(f"STATE_CHANGE | {log_message}")

        except Exception as e:
            self._log_logging_error(
                "log_state_change",
                e,
                {
                    "container_id": container_id,
                    "old_state": old_state,
                    "new_state": new_state,
                },
            )

    def log_debug(self, message: str, context: Dict[str, Any]) -> None:
        """
        Create debug logging for troubleshooting.

        Args:
            message: Debug message
            context: Additional context for debugging
        """
        try:
            log_message = self._format_log_data(
                event_type="debug", message=message, context=context
            )

            self.logger.debug(f"DEBUG | {log_message}")

        except Exception as e:
            self._log_logging_error(
                "log_debug", e, {"message": message, "context": str(context)}
            )

    def _log_logging_error(
        self, method_name: str, error: Exception, context: Dict[str, Any]
    ) -> None:
        """
        Internal method to log logging failures without causing recursion.

        Args:
            method_name: Name of the logging method that failed
            error: The exception that occurred during logging
            context: Context that was being logged when the error occurred
        """
        try:
            # Use basic string formatting to avoid JSON serialization issues
            error_msg = (
                f"LOGGING_FAILURE | method={method_name} | "
                f"error={type(error).__name__}: {str(error)} | "
                f"context={str(context)} | "
                f"timestamp={datetime.now(timezone.utc).isoformat()}"
            )

            self.logger.error(error_msg)

        except Exception:
            # Ultimate fallback - print to stderr if all logging fails
            import sys

            print(
                f"CRITICAL_LOGGING_FAILURE: {method_name} failed with {str(error)}",
                file=sys.stderr,
            )
