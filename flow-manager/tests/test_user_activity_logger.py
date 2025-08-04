"""
Tests for UserActivityLogger

Tests the user activity logging functionality including Socket.IO integration,
sensitive data filtering, and various activity logging methods.
"""

import pytest
import socketio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from user_activity_logger import UserActivityLogger


@pytest.fixture
def mock_sio():
    """Create a mock Socket.IO server."""
    sio = MagicMock(spec=socketio.AsyncServer)
    sio.emit = AsyncMock()
    return sio


@pytest.fixture
def activity_logger(mock_sio):
    """Create a UserActivityLogger instance with mocked Socket.IO."""
    return UserActivityLogger(mock_sio)


class TestUserActivityLogger:
    """Test suite for UserActivityLogger class."""

    @pytest.mark.asyncio
    async def test_log_container_created(self, activity_logger, mock_sio):
        """Test logging container creation activity."""
        container_id = "test_container_123"
        name = "test-container"
        image = "nginx:latest"

        await activity_logger.log_container_created(container_id, name, image)

        # Verify Socket.IO emit was called
        mock_sio.emit.assert_called_once()
        call_args = mock_sio.emit.call_args

        assert call_args[0][0] == "activity_log"  # Event name
        activity_data = call_args[0][1]  # Event data

        assert activity_data["type"] == "container_created"
        assert activity_data["container_id"] == container_id
        assert (
            "Container 'test-container' created successfully"
            in activity_data["message"]
        )
        assert activity_data["details"]["name"] == name
        assert activity_data["details"]["image"] == image
        assert activity_data["details"]["status"] == "created"
        assert "timestamp" in activity_data

    @pytest.mark.asyncio
    async def test_log_container_started(self, activity_logger, mock_sio):
        """Test logging container start activity."""
        container_id = "test_container_123"
        name = "test-container"

        await activity_logger.log_container_started(container_id, name)

        mock_sio.emit.assert_called_once()
        call_args = mock_sio.emit.call_args
        activity_data = call_args[0][1]

        assert activity_data["type"] == "container_started"
        assert activity_data["container_id"] == container_id
        assert "started and is now running" in activity_data["message"]
        assert activity_data["details"]["status"] == "running"

    @pytest.mark.asyncio
    async def test_log_container_stopped(self, activity_logger, mock_sio):
        """Test logging container stop activity."""
        container_id = "test_container_123"
        name = "test-container"

        await activity_logger.log_container_stopped(container_id, name)

        mock_sio.emit.assert_called_once()
        call_args = mock_sio.emit.call_args
        activity_data = call_args[0][1]

        assert activity_data["type"] == "container_stopped"
        assert "stopped successfully" in activity_data["message"]
        assert activity_data["details"]["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_log_container_restarted(self, activity_logger, mock_sio):
        """Test logging container restart activity."""
        container_id = "test_container_123"
        name = "test-container"

        await activity_logger.log_container_restarted(container_id, name)

        mock_sio.emit.assert_called_once()
        call_args = mock_sio.emit.call_args
        activity_data = call_args[0][1]

        assert activity_data["type"] == "container_restarted"
        assert "restarted successfully" in activity_data["message"]
        assert activity_data["details"]["status"] == "running"

    @pytest.mark.asyncio
    async def test_log_container_updated(self, activity_logger, mock_sio):
        """Test logging container update activity."""
        container_id = "test_container_123"
        name = "test-container"

        await activity_logger.log_container_updated(container_id, name)

        mock_sio.emit.assert_called_once()
        call_args = mock_sio.emit.call_args
        activity_data = call_args[0][1]

        assert activity_data["type"] == "container_updated"
        assert "updated with new code" in activity_data["message"]
        assert activity_data["details"]["status"] == "updated"

    @pytest.mark.asyncio
    async def test_log_container_deleted(self, activity_logger, mock_sio):
        """Test logging container deletion activity."""
        container_id = "test_container_123"
        name = "test-container"

        await activity_logger.log_container_deleted(container_id, name)

        mock_sio.emit.assert_called_once()
        call_args = mock_sio.emit.call_args
        activity_data = call_args[0][1]

        assert activity_data["type"] == "container_deleted"
        assert "deleted and resources cleaned up" in activity_data["message"]
        assert activity_data["details"]["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_log_container_message_received(self, activity_logger, mock_sio):
        """Test logging received container messages."""
        container_id = "test_container_123"
        message_data = {"type": "status", "data": {"health": "ok"}}

        await activity_logger.log_container_message(
            container_id, message_data, "received"
        )

        mock_sio.emit.assert_called_once()
        call_args = mock_sio.emit.call_args
        activity_data = call_args[0][1]

        assert activity_data["type"] == "container_message"
        assert "received from container" in activity_data["message"]
        assert activity_data["details"]["direction"] == "received"
        assert activity_data["details"]["message_type"] == "status"

    @pytest.mark.asyncio
    async def test_log_container_message_sent(self, activity_logger, mock_sio):
        """Test logging sent container messages."""
        container_id = "test_container_123"
        message_data = {"command": "restart", "params": {}}

        await activity_logger.log_container_message(container_id, message_data, "sent")

        mock_sio.emit.assert_called_once()
        call_args = mock_sio.emit.call_args
        activity_data = call_args[0][1]

        assert activity_data["type"] == "container_message"
        assert "sent to container" in activity_data["message"]
        assert activity_data["details"]["direction"] == "sent"

    @pytest.mark.asyncio
    async def test_log_actor_event(self, activity_logger, mock_sio):
        """Test logging actor events."""
        container_id = "test_container_123"
        actor = "EmailActor"
        event = "email_sent"
        event_data = {"recipient": "user@example.com", "subject": "Test"}

        await activity_logger.log_actor_event(container_id, actor, event, event_data)

        mock_sio.emit.assert_called_once()
        call_args = mock_sio.emit.call_args
        activity_data = call_args[0][1]

        assert activity_data["type"] == "actor_event"
        assert (
            "Actor 'EmailActor' triggered event 'email_sent'"
            in activity_data["message"]
        )
        assert activity_data["details"]["actor"] == actor
        assert activity_data["details"]["event"] == event
        assert "event_data" in activity_data["details"]

    @pytest.mark.asyncio
    async def test_log_container_error(self, activity_logger, mock_sio):
        """Test logging container errors."""
        container_id = "test_container_123"
        error_message = "Connection timeout"
        operation = "start_container"

        await activity_logger.log_container_error(
            container_id, error_message, operation
        )

        mock_sio.emit.assert_called_once()
        call_args = mock_sio.emit.call_args
        activity_data = call_args[0][1]

        assert activity_data["type"] == "container_error"
        assert (
            "Error during start_container: Connection timeout"
            in activity_data["message"]
        )
        assert activity_data["details"]["error"] is True
        assert activity_data["details"]["operation"] == operation

    @pytest.mark.asyncio
    async def test_log_user_activity(self, activity_logger, mock_sio):
        """Test logging general user activity."""
        activity_type = "custom_activity"
        container_id = "test_container_123"
        message = "Custom activity performed"
        details = {"custom_field": "custom_value"}

        await activity_logger.log_user_activity(
            activity_type, container_id, message, details
        )

        mock_sio.emit.assert_called_once()
        call_args = mock_sio.emit.call_args
        activity_data = call_args[0][1]

        assert activity_data["type"] == activity_type
        assert activity_data["message"] == message
        assert activity_data["details"]["custom_field"] == "custom_value"


class TestSensitiveDataFiltering:
    """Test suite for sensitive data filtering functionality."""

    def test_filter_sensitive_keys(self, activity_logger):
        """Test filtering of sensitive keys in dictionaries."""
        data = {
            "username": "testuser",
            "password": "secret123",
            "api_key": "abc123",
            "normal_field": "normal_value",
        }

        filtered = activity_logger._filter_sensitive_data(data)

        assert filtered["username"] == "testuser"
        assert filtered["password"] == "[FILTERED]"
        assert filtered["api_key"] == "[FILTERED]"
        assert filtered["normal_field"] == "normal_value"

    def test_filter_nested_sensitive_data(self, activity_logger):
        """Test filtering of nested sensitive data structures."""
        data = {
            "config": {
                "database": {"host": "localhost", "password": "dbpass123"},
                "auth": {"secret": "jwt_secret", "public_key": "public_data"},
            },
            "users": [
                {"name": "user1", "token": "token123"},
                {"name": "user2", "role": "admin"},
            ],
        }

        filtered = activity_logger._filter_sensitive_data(data)

        assert filtered["config"]["database"]["host"] == "localhost"
        assert filtered["config"]["database"]["password"] == "[FILTERED]"
        assert filtered["config"]["auth"]["secret"] == "[FILTERED]"
        assert filtered["config"]["auth"]["public_key"] == "public_data"
        assert filtered["users"][0]["name"] == "user1"
        assert filtered["users"][0]["token"] == "[FILTERED]"
        assert filtered["users"][1]["name"] == "user2"
        assert filtered["users"][1]["role"] == "admin"

    def test_filter_sensitive_strings(self, activity_logger):
        """Test filtering of sensitive patterns in strings."""
        sensitive_string = "Authorization: Bearer token123"
        normal_string = "This is a normal message"

        filtered_sensitive = activity_logger._filter_sensitive_data(sensitive_string)
        filtered_normal = activity_logger._filter_sensitive_data(normal_string)

        assert filtered_sensitive == "[FILTERED]"
        assert filtered_normal == "This is a normal message"

    def test_is_sensitive_key(self, activity_logger):
        """Test identification of sensitive keys."""
        sensitive_keys = [
            "password",
            "PASSWORD",
            "api_key",
            "API_KEY",
            "secret",
            "token",
            "auth",
        ]
        normal_keys = ["username", "email", "name", "status", "data"]

        for key in sensitive_keys:
            assert activity_logger._is_sensitive_key(key) is True

        for key in normal_keys:
            assert activity_logger._is_sensitive_key(key) is False

    def test_contains_sensitive_pattern(self, activity_logger):
        """Test detection of sensitive patterns in text."""
        sensitive_texts = [
            "password=secret123",
            "Bearer token123",
            "api_key:abc123",
            "Authorization: Basic dXNlcjpwYXNz",
        ]
        normal_texts = [
            "This is a normal message",
            "Container started successfully",
            "Status: running",
        ]

        for text in sensitive_texts:
            assert activity_logger._contains_sensitive_pattern(text) is True

        for text in normal_texts:
            assert activity_logger._contains_sensitive_pattern(text) is False

    def test_contains_sensitive_data(self, activity_logger):
        """Test detection of sensitive data in complex structures."""
        sensitive_data = {
            "config": {"password": "secret"},
            "message": "Bearer token123",
        }
        normal_data = {"status": "running", "message": "Container started"}

        assert activity_logger._contains_sensitive_data(sensitive_data) is True
        assert activity_logger._contains_sensitive_data(normal_data) is False

    @pytest.mark.asyncio
    async def test_message_filtering_with_sensitive_data(
        self, activity_logger, mock_sio
    ):
        """Test that messages with sensitive data are properly filtered."""
        container_id = "test_container_123"
        sensitive_message = {
            "type": "auth",
            "credentials": {"username": "user", "password": "secret123"},
        }

        await activity_logger.log_container_message(container_id, sensitive_message)

        mock_sio.emit.assert_called_once()
        call_args = mock_sio.emit.call_args
        activity_data = call_args[0][1]

        # Should not include message preview for sensitive data
        assert "message_preview" not in activity_data["details"]
        assert activity_data["details"]["message_type"] == "auth"


class TestActivityLogStructure:
    """Test suite for activity log structure and format."""

    @pytest.mark.asyncio
    async def test_activity_log_structure(self, activity_logger, mock_sio):
        """Test that all activity logs have consistent structure."""
        await activity_logger.log_container_created("test_id", "test_name")

        mock_sio.emit.assert_called_once()
        call_args = mock_sio.emit.call_args

        assert call_args[0][0] == "activity_log"  # Event name
        activity_data = call_args[0][1]  # Event data

        # Check required fields
        required_fields = ["type", "container_id", "message", "details", "timestamp"]
        for field in required_fields:
            assert field in activity_data

        # Check timestamp format
        timestamp = activity_data["timestamp"]
        datetime.fromisoformat(
            timestamp.replace("Z", "+00:00")
        )  # Should not raise exception

    @pytest.mark.asyncio
    async def test_emit_to_all_clients(self, activity_logger, mock_sio):
        """Test that activity logs are emitted to all clients (no 'to' parameter)."""
        await activity_logger.log_container_started("test_id", "test_name")

        mock_sio.emit.assert_called_once()
        call_args = mock_sio.emit.call_args

        # Should not have 'to' parameter (broadcasts to all clients)
        assert len(call_args[1]) == 0 or "to" not in call_args[1]
