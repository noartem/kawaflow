"""
Tests for SystemLogger class

Verifies structured logging, error handling, and debug functionality
according to requirements 7.1, 7.2, 7.3, 7.4.
"""

import logging
from unittest.mock import patch
from io import StringIO
from system_logger import SystemLogger


class TestSystemLogger:
    """Test suite for SystemLogger functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.logger = SystemLogger("test_logger")

        # Capture log output for testing
        self.log_capture = StringIO()
        handler = logging.StreamHandler(self.log_capture)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(levelname)s | %(message)s")
        handler.setFormatter(formatter)

        # Clear existing handlers and add test handler
        self.logger.logger.handlers.clear()
        self.logger.logger.addHandler(handler)

    def get_log_output(self) -> str:
        """Get captured log output"""
        return self.log_capture.getvalue()

    def test_logger_initialization(self):
        """Test SystemLogger initialization and setup"""
        logger = SystemLogger("test_init")

        assert logger.logger.name == "test_init"
        assert logger.logger.level == logging.DEBUG
        assert len(logger.logger.handlers) >= 1

    def test_log_container_operation(self):
        """Test container operation logging with structured data"""
        # Test data
        operation = "create_container"
        container_id = "test_container_123"
        details = {"image": "nginx:latest", "ports": {"80": 8080}, "status": "created"}

        # Execute
        self.logger.log_container_operation(operation, container_id, details)

        # Verify
        log_output = self.get_log_output()
        assert "CONTAINER_OP" in log_output
        assert "INFO" in log_output

        # Verify structured data is present
        assert operation in log_output
        assert container_id in log_output
        assert "container_operation" in log_output

    def test_log_socket_event(self):
        """Test Socket.IO event logging"""
        # Test data
        event = "start_container"
        sid = "session_123"
        data = {"container_id": "test_123", "image": "nginx"}

        # Execute
        self.logger.log_socket_event(event, sid, data)

        # Verify
        log_output = self.get_log_output()
        assert "SOCKET_EVENT" in log_output
        assert "INFO" in log_output
        assert event in log_output
        assert sid in log_output
        assert "socket_event" in log_output

    def test_log_communication(self):
        """Test Unix socket communication logging"""
        # Test data
        container_id = "comm_test_123"
        direction = "send"
        message = {"command": "status", "data": {}}

        # Execute
        self.logger.log_communication(container_id, direction, message)

        # Verify
        log_output = self.get_log_output()
        assert "SOCKET_COMM" in log_output
        assert "DEBUG" in log_output
        assert container_id in log_output
        assert direction in log_output
        assert "socket_communication" in log_output

    def test_log_error_with_stack_trace(self):
        """Test error logging with full context and stack traces"""
        # Create a test exception with stack trace
        try:
            raise ValueError("Test error for logging")
        except ValueError as e:
            context = {
                "operation": "test_operation",
                "container_id": "error_test_123",
                "additional_info": "test context",
            }

            # Execute
            self.logger.log_error(e, context)

        # Verify
        log_output = self.get_log_output()
        assert "ERROR" in log_output
        assert "ValueError" in log_output
        assert "Test error for logging" in log_output
        assert "test_operation" in log_output
        assert "error_test_123" in log_output
        assert "Traceback" in log_output or "stack_trace" in log_output

    def test_log_state_change(self):
        """Test container state change logging"""
        # Test data
        container_id = "state_test_123"
        old_state = "stopped"
        new_state = "running"

        # Execute
        self.logger.log_state_change(container_id, old_state, new_state)

        # Verify
        log_output = self.get_log_output()
        assert "STATE_CHANGE" in log_output
        assert "INFO" in log_output
        assert container_id in log_output
        assert old_state in log_output
        assert new_state in log_output
        assert "stopped -> running" in log_output

    def test_log_debug(self):
        """Test debug logging for troubleshooting"""
        # Test data
        message = "Debug message for troubleshooting"
        context = {
            "function": "test_function",
            "variables": {"var1": "value1", "var2": 42},
            "state": "debugging",
        }

        # Execute
        self.logger.log_debug(message, context)

        # Verify
        log_output = self.get_log_output()
        assert "DEBUG" in log_output
        assert message in log_output
        assert "test_function" in log_output
        assert "debugging" in log_output

    def test_structured_logging_format(self):
        """Test that logs are properly structured with JSON data"""
        # Execute a log operation
        self.logger.log_container_operation("test_op", "test_id", {"key": "value"})

        # Verify structured format
        log_output = self.get_log_output()

        # Should contain structured JSON data
        assert "timestamp" in log_output
        assert "event_type" in log_output
        assert "container_operation" in log_output

    def test_logging_error_handling(self):
        """Test that logging failures don't break the system"""
        # Mock JSON dumps to raise an exception
        with patch("json.dumps", side_effect=TypeError("Mock JSON error")):
            # This should not raise an exception
            self.logger.log_container_operation(
                "test_op",
                "test_id",
                {"problematic": object()},  # Non-serializable object
            )

            # Verify fallback logging occurred
            log_output = self.get_log_output()
            assert (
                "LOG_SERIALIZATION_ERROR" in log_output
                or "LOGGING_FAILURE" in log_output
            )

    def test_logging_method_failure_handling(self):
        """Test handling of failures in logging methods themselves"""
        # Mock the logger to raise an exception
        with patch.object(
            self.logger.logger, "info", side_effect=Exception("Mock logging error")
        ):
            # This should not raise an exception
            self.logger.log_container_operation("test", "test", {})

            # Verify error was handled
            log_output = self.get_log_output()
            assert "LOGGING_FAILURE" in log_output or "ERROR" in log_output

    def test_multiple_log_levels(self):
        """Test that different log levels are used appropriately"""
        # Test different log levels
        self.logger.log_debug("Debug message", {})
        self.logger.log_container_operation("info_op", "info_id", {})

        try:
            raise RuntimeError("Test error")
        except RuntimeError as e:
            self.logger.log_error(e, {})

        log_output = self.get_log_output()

        # Verify different log levels are present
        assert "DEBUG" in log_output
        assert "INFO" in log_output
        assert "ERROR" in log_output

    def test_timestamp_inclusion(self):
        """Test that timestamps are included in all log entries"""
        self.logger.log_container_operation("test", "test", {})

        log_output = self.get_log_output()
        assert "timestamp" in log_output

        # Verify timestamp format (ISO format)
        import re

        timestamp_pattern = r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
        assert re.search(timestamp_pattern, log_output)

    def test_context_preservation(self):
        """Test that context is preserved in all logging operations"""
        context = {
            "user_id": "user123",
            "session": "session456",
            "operation_id": "op789",
        }

        self.logger.log_debug("Test with context", context)

        log_output = self.get_log_output()
        assert "user123" in log_output
        assert "session456" in log_output
        assert "op789" in log_output
