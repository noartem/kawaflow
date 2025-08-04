"""
Comprehensive tests for Socket.IO event handlers.

This module tests all Socket.IO event handlers for container lifecycle management,
including error handling, edge cases, and proper event emission and response formatting.
"""

import pytest
from unittest.mock import Mock, AsyncMock, ANY
from datetime import datetime
import socketio

from socket_event_handler import SocketIOEventHandler
from container_manager import ContainerManager
from socket_communication_handler import SocketCommunicationHandler
from system_logger import SystemLogger
from user_activity_logger import UserActivityLogger
from models import ContainerInfo


def test_socket_event_handler_initialization():
    """Test that SocketIOEventHandler initializes correctly."""
    # Create mocks
    mock_sio = Mock(spec=socketio.AsyncServer)
    mock_sio.emit = AsyncMock()
    mock_sio.on = Mock()
    mock_sio.handlers = {"/": {}}

    mock_container_manager = Mock(spec=ContainerManager)
    mock_container_manager.register_status_change_callback = Mock()
    mock_container_manager.register_health_check_callback = Mock()
    mock_container_manager.register_crash_callback = Mock()

    mock_socket_handler = Mock(spec=SocketCommunicationHandler)
    mock_system_logger = Mock(spec=SystemLogger)
    mock_user_logger = Mock(spec=UserActivityLogger)

    # Create event handler
    event_handler = SocketIOEventHandler(
        sio=mock_sio,
        container_manager=mock_container_manager,
        socket_handler=mock_socket_handler,
        system_logger=mock_system_logger,
        user_logger=mock_user_logger,
    )

    # Verify event handlers are registered
    expected_events = [
        "create_container",
        "start_container",
        "stop_container",
        "restart_container",
        "update_container",
        "delete_container",
        "send_message",
        "get_container_status",
        "list_containers",
        "connect",
        "disconnect",
    ]

    for event in expected_events:
        mock_sio.on.assert_any_call(event, ANY)

    # Verify container manager callbacks are registered
    mock_container_manager.register_status_change_callback.assert_called_once()
    mock_container_manager.register_health_check_callback.assert_called_once()
    mock_container_manager.register_crash_callback.assert_called_once()


@pytest.mark.asyncio
async def test_handle_connect():
    """Test successful client connection."""
    # Create mocks
    mock_sio = Mock(spec=socketio.AsyncServer)
    mock_sio.emit = AsyncMock()
    mock_sio.on = Mock()

    mock_container_manager = Mock(spec=ContainerManager)
    mock_container_manager.register_status_change_callback = Mock()
    mock_container_manager.register_health_check_callback = Mock()
    mock_container_manager.register_crash_callback = Mock()

    mock_socket_handler = Mock(spec=SocketCommunicationHandler)
    mock_system_logger = Mock(spec=SystemLogger)
    mock_system_logger.log_socket_event = Mock()
    mock_user_logger = Mock(spec=UserActivityLogger)

    # Create event handler
    event_handler = SocketIOEventHandler(
        sio=mock_sio,
        container_manager=mock_container_manager,
        socket_handler=mock_socket_handler,
        system_logger=mock_system_logger,
        user_logger=mock_user_logger,
    )

    sid = "test-session-123"
    environ = {"HTTP_USER_AGENT": "test-client"}

    await event_handler.handle_connect(sid, environ)

    # Verify system logging
    mock_system_logger.log_socket_event.assert_called_once_with(
        "connect", sid, {"environ_keys": ["HTTP_USER_AGENT"]}
    )

    # Verify connection response
    mock_sio.emit.assert_called_once_with(
        "connected", {"message": "Connected to flow-manager"}, to=sid
    )


@pytest.mark.asyncio
async def test_handle_create_container_success():
    """Test successful container creation."""
    # Create mocks
    mock_sio = Mock(spec=socketio.AsyncServer)
    mock_sio.emit = AsyncMock()
    mock_sio.on = Mock()

    mock_container_manager = Mock(spec=ContainerManager)
    mock_container_manager.register_status_change_callback = Mock()
    mock_container_manager.register_health_check_callback = Mock()
    mock_container_manager.register_crash_callback = Mock()
    mock_container_manager.create_container = AsyncMock()

    mock_socket_handler = Mock(spec=SocketCommunicationHandler)
    mock_socket_handler.setup_socket = AsyncMock()

    mock_system_logger = Mock(spec=SystemLogger)
    mock_system_logger.log_socket_event = Mock()

    mock_user_logger = Mock(spec=UserActivityLogger)
    mock_user_logger.log_container_created = AsyncMock()

    # Create sample container info
    sample_container_info = ContainerInfo(
        id="test-container-123",
        name="test-container",
        status="created",
        image="test-image:latest",
        created=datetime.now(),
        socket_path="/tmp/test-container-123.sock",
        ports={"8080": 8080},
        environment={"TEST_VAR": "test_value"},
    )

    # Create event handler
    event_handler = SocketIOEventHandler(
        sio=mock_sio,
        container_manager=mock_container_manager,
        socket_handler=mock_socket_handler,
        system_logger=mock_system_logger,
        user_logger=mock_user_logger,
    )

    sid = "test-session-123"
    data = {
        "image": "test-image:latest",
        "name": "test-container",
        "environment": {"TEST_VAR": "test_value"},
        "volumes": {"/host/path": "/container/path"},
        "ports": {"8080": 8080},
    }

    # Mock container manager response
    mock_container_manager.create_container.return_value = sample_container_info

    await event_handler.handle_create_container(sid, data)

    # Verify container creation was called
    mock_container_manager.create_container.assert_called_once()
    config = mock_container_manager.create_container.call_args[0][0]
    assert config.image == "test-image:latest"
    assert config.name == "test-container"

    # Verify socket setup
    mock_socket_handler.setup_socket.assert_called_once_with(sample_container_info.id)

    # Verify user activity logging
    mock_user_logger.log_container_created.assert_called_once_with(
        sample_container_info.id,
        sample_container_info.name,
        sample_container_info.image,
    )

    # Verify success response
    mock_sio.emit.assert_called_with(
        "container_created",
        {
            "container_id": sample_container_info.id,
            "name": sample_container_info.name,
            "image": sample_container_info.image,
            "status": sample_container_info.status,
            "socket_path": sample_container_info.socket_path,
            "ports": sample_container_info.ports,
        },
        to=sid,
    )


@pytest.mark.asyncio
async def test_handle_disconnect():
    """Test client disconnection."""
    # Create mocks
    mock_sio = Mock(spec=socketio.AsyncServer)
    mock_sio.emit = AsyncMock()
    mock_sio.on = Mock()

    mock_container_manager = Mock(spec=ContainerManager)
    mock_container_manager.register_status_change_callback = Mock()
    mock_container_manager.register_health_check_callback = Mock()
    mock_container_manager.register_crash_callback = Mock()

    mock_socket_handler = Mock(spec=SocketCommunicationHandler)
    mock_system_logger = Mock(spec=SystemLogger)
    mock_system_logger.log_socket_event = Mock()
    mock_user_logger = Mock(spec=UserActivityLogger)

    # Create event handler
    event_handler = SocketIOEventHandler(
        sio=mock_sio,
        container_manager=mock_container_manager,
        socket_handler=mock_socket_handler,
        system_logger=mock_system_logger,
        user_logger=mock_user_logger,
    )

    sid = "test-session-123"

    await event_handler.handle_disconnect(sid)

    # Verify system logging
    mock_system_logger.log_socket_event.assert_called_once_with("disconnect", sid, {})


@pytest.mark.asyncio
async def test_handle_create_container_invalid_data():
    """Test create_container with invalid data."""
    # Create mocks
    mock_sio = Mock(spec=socketio.AsyncServer)
    mock_sio.emit = AsyncMock()
    mock_sio.on = Mock()

    mock_container_manager = Mock(spec=ContainerManager)
    mock_container_manager.register_status_change_callback = Mock()
    mock_container_manager.register_health_check_callback = Mock()
    mock_container_manager.register_crash_callback = Mock()
    mock_container_manager.create_container = AsyncMock()

    mock_socket_handler = Mock(spec=SocketCommunicationHandler)
    mock_system_logger = Mock(spec=SystemLogger)
    mock_system_logger.log_socket_event = Mock()
    mock_system_logger.log_error = Mock()
    mock_user_logger = Mock(spec=UserActivityLogger)
    mock_user_logger.log_container_error = AsyncMock()

    # Create event handler
    event_handler = SocketIOEventHandler(
        sio=mock_sio,
        container_manager=mock_container_manager,
        socket_handler=mock_socket_handler,
        system_logger=mock_system_logger,
        user_logger=mock_user_logger,
    )

    sid = "test-session-123"
    data = {"image": ""}  # Invalid empty image

    await event_handler.handle_create_container(sid, data)

    # Verify error response
    mock_sio.emit.assert_called_with("error", ANY, to=sid)
    error_data = mock_sio.emit.call_args[0][1]
    assert error_data["error"] is True
    assert "system_error" in error_data["error_type"]


@pytest.mark.asyncio
async def test_handle_send_message_success():
    """Test successful message sending."""
    # Create mocks
    mock_sio = Mock(spec=socketio.AsyncServer)
    mock_sio.emit = AsyncMock()
    mock_sio.on = Mock()

    mock_container_manager = Mock(spec=ContainerManager)
    mock_container_manager.register_status_change_callback = Mock()
    mock_container_manager.register_health_check_callback = Mock()
    mock_container_manager.register_crash_callback = Mock()

    mock_socket_handler = Mock(spec=SocketCommunicationHandler)
    mock_socket_handler.send_message = AsyncMock()

    mock_system_logger = Mock(spec=SystemLogger)
    mock_system_logger.log_socket_event = Mock()

    mock_user_logger = Mock(spec=UserActivityLogger)
    mock_user_logger.log_container_message = AsyncMock()

    # Create event handler
    event_handler = SocketIOEventHandler(
        sio=mock_sio,
        container_manager=mock_container_manager,
        socket_handler=mock_socket_handler,
        system_logger=mock_system_logger,
        user_logger=mock_user_logger,
    )

    sid = "test-session-123"
    data = {
        "container_id": "test-container-123",
        "message": {"command": "test", "data": {"key": "value"}},
    }

    await event_handler.handle_send_message(sid, data)

    # Verify message was sent
    mock_socket_handler.send_message.assert_called_once_with(
        "test-container-123", {"command": "test", "data": {"key": "value"}}
    )

    # Verify user activity logging
    mock_user_logger.log_container_message.assert_called_once_with(
        "test-container-123",
        {"command": "test", "data": {"key": "value"}},
        "sent",
    )

    # Verify success response
    mock_sio.emit.assert_called_with(
        "message_sent",
        {
            "container_id": "test-container-123",
            "message": {"command": "test", "data": {"key": "value"}},
            "status": "sent",
        },
        to=sid,
    )


@pytest.mark.asyncio
async def test_handle_send_message_timeout_error():
    """Test send_message with timeout error."""
    from socket_communication_handler import SocketTimeoutError

    # Create mocks
    mock_sio = Mock(spec=socketio.AsyncServer)
    mock_sio.emit = AsyncMock()
    mock_sio.on = Mock()

    mock_container_manager = Mock(spec=ContainerManager)
    mock_container_manager.register_status_change_callback = Mock()
    mock_container_manager.register_health_check_callback = Mock()
    mock_container_manager.register_crash_callback = Mock()

    mock_socket_handler = Mock(spec=SocketCommunicationHandler)
    mock_socket_handler.send_message = AsyncMock()
    mock_socket_handler.send_message.side_effect = SocketTimeoutError("Message timeout")

    mock_system_logger = Mock(spec=SystemLogger)
    mock_system_logger.log_socket_event = Mock()
    mock_system_logger.log_error = Mock()

    mock_user_logger = Mock(spec=UserActivityLogger)
    mock_user_logger.log_container_error = AsyncMock()

    # Create event handler
    event_handler = SocketIOEventHandler(
        sio=mock_sio,
        container_manager=mock_container_manager,
        socket_handler=mock_socket_handler,
        system_logger=mock_system_logger,
        user_logger=mock_user_logger,
    )

    sid = "test-session-123"
    data = {
        "container_id": "test-container-123",
        "message": {"command": "test"},
    }

    await event_handler.handle_send_message(sid, data)

    # Verify error response
    mock_sio.emit.assert_called_with("error", ANY, to=sid)
    error_data = mock_sio.emit.call_args[0][1]
    assert error_data["error_type"] == "socket_timeout_error"


@pytest.mark.asyncio
async def test_handle_start_container_success():
    """Test successful container start."""
    # Create mocks
    mock_sio = Mock(spec=socketio.AsyncServer)
    mock_sio.emit = AsyncMock()
    mock_sio.on = Mock()

    mock_container_manager = Mock(spec=ContainerManager)
    mock_container_manager.register_status_change_callback = Mock()
    mock_container_manager.register_health_check_callback = Mock()
    mock_container_manager.register_crash_callback = Mock()
    mock_container_manager.start_container = AsyncMock()
    mock_container_manager.list_containers = AsyncMock()

    mock_socket_handler = Mock(spec=SocketCommunicationHandler)

    mock_system_logger = Mock(spec=SystemLogger)
    mock_system_logger.log_socket_event = Mock()

    mock_user_logger = Mock(spec=UserActivityLogger)
    mock_user_logger.log_container_started = AsyncMock()

    # Create event handler
    event_handler = SocketIOEventHandler(
        sio=mock_sio,
        container_manager=mock_container_manager,
        socket_handler=mock_socket_handler,
        system_logger=mock_system_logger,
        user_logger=mock_user_logger,
    )

    sid = "test-session-123"
    data = {"container_id": "test-container-123"}

    # Mock container list for name lookup
    container_info = Mock()
    container_info.id = "test-container-123"
    container_info.name = "test-container"
    mock_container_manager.list_containers.return_value = [container_info]

    await event_handler.handle_start_container(sid, data)

    # Verify container start was called
    mock_container_manager.start_container.assert_called_once_with("test-container-123")

    # Verify user activity logging
    mock_user_logger.log_container_started.assert_called_once_with(
        "test-container-123", "test-container"
    )

    # Verify success response
    mock_sio.emit.assert_called_with(
        "container_started",
        {"container_id": "test-container-123", "status": "running"},
        to=sid,
    )


@pytest.mark.asyncio
async def test_handle_stop_container_success():
    """Test successful container stop."""
    # Create mocks
    mock_sio = Mock(spec=socketio.AsyncServer)
    mock_sio.emit = AsyncMock()
    mock_sio.on = Mock()

    mock_container_manager = Mock(spec=ContainerManager)
    mock_container_manager.register_status_change_callback = Mock()
    mock_container_manager.register_health_check_callback = Mock()
    mock_container_manager.register_crash_callback = Mock()
    mock_container_manager.stop_container = AsyncMock()
    mock_container_manager.list_containers = AsyncMock()

    mock_socket_handler = Mock(spec=SocketCommunicationHandler)

    mock_system_logger = Mock(spec=SystemLogger)
    mock_system_logger.log_socket_event = Mock()

    mock_user_logger = Mock(spec=UserActivityLogger)
    mock_user_logger.log_container_stopped = AsyncMock()

    # Create event handler
    event_handler = SocketIOEventHandler(
        sio=mock_sio,
        container_manager=mock_container_manager,
        socket_handler=mock_socket_handler,
        system_logger=mock_system_logger,
        user_logger=mock_user_logger,
    )

    sid = "test-session-123"
    data = {"container_id": "test-container-123"}

    # Mock container list for name lookup
    container_info = Mock()
    container_info.id = "test-container-123"
    container_info.name = "test-container"
    mock_container_manager.list_containers.return_value = [container_info]

    await event_handler.handle_stop_container(sid, data)

    # Verify container stop was called
    mock_container_manager.stop_container.assert_called_once_with("test-container-123")

    # Verify user activity logging
    mock_user_logger.log_container_stopped.assert_called_once_with(
        "test-container-123", "test-container"
    )

    # Verify success response
    mock_sio.emit.assert_called_with(
        "container_stopped",
        {"container_id": "test-container-123", "status": "stopped"},
        to=sid,
    )


@pytest.mark.asyncio
async def test_handle_delete_container_success():
    """Test successful container deletion."""
    # Create mocks
    mock_sio = Mock(spec=socketio.AsyncServer)
    mock_sio.emit = AsyncMock()
    mock_sio.on = Mock()

    mock_container_manager = Mock(spec=ContainerManager)
    mock_container_manager.register_status_change_callback = Mock()
    mock_container_manager.register_health_check_callback = Mock()
    mock_container_manager.register_crash_callback = Mock()
    mock_container_manager.delete_container = AsyncMock()
    mock_container_manager.list_containers = AsyncMock()

    mock_socket_handler = Mock(spec=SocketCommunicationHandler)
    mock_socket_handler.cleanup_socket = AsyncMock()

    mock_system_logger = Mock(spec=SystemLogger)
    mock_system_logger.log_socket_event = Mock()

    mock_user_logger = Mock(spec=UserActivityLogger)
    mock_user_logger.log_container_deleted = AsyncMock()

    # Create event handler
    event_handler = SocketIOEventHandler(
        sio=mock_sio,
        container_manager=mock_container_manager,
        socket_handler=mock_socket_handler,
        system_logger=mock_system_logger,
        user_logger=mock_user_logger,
    )

    sid = "test-session-123"
    data = {"container_id": "test-container-123"}

    # Mock container list for name lookup
    container_info = Mock()
    container_info.id = "test-container-123"
    container_info.name = "test-container"
    mock_container_manager.list_containers.return_value = [container_info]

    await event_handler.handle_delete_container(sid, data)

    # Verify socket cleanup was called first
    mock_socket_handler.cleanup_socket.assert_called_once_with("test-container-123")

    # Verify container deletion was called
    mock_container_manager.delete_container.assert_called_once_with(
        "test-container-123"
    )

    # Verify user activity logging
    mock_user_logger.log_container_deleted.assert_called_once_with(
        "test-container-123", "test-container"
    )

    # Verify success response
    mock_sio.emit.assert_called_with(
        "container_deleted",
        {"container_id": "test-container-123", "status": "deleted"},
        to=sid,
    )


@pytest.mark.asyncio
async def test_error_handling():
    """Test that errors are emitted in standardized format."""
    # Create mocks
    mock_sio = Mock(spec=socketio.AsyncServer)
    mock_sio.emit = AsyncMock()
    mock_sio.on = Mock()

    mock_container_manager = Mock(spec=ContainerManager)
    mock_container_manager.register_status_change_callback = Mock()
    mock_container_manager.register_health_check_callback = Mock()
    mock_container_manager.register_crash_callback = Mock()

    mock_socket_handler = Mock(spec=SocketCommunicationHandler)

    mock_system_logger = Mock(spec=SystemLogger)
    mock_system_logger.log_error = Mock()

    mock_user_logger = Mock(spec=UserActivityLogger)
    mock_user_logger.log_container_error = AsyncMock()

    # Create event handler
    event_handler = SocketIOEventHandler(
        sio=mock_sio,
        container_manager=mock_container_manager,
        socket_handler=mock_socket_handler,
        system_logger=mock_system_logger,
        user_logger=mock_user_logger,
    )

    sid = "test-session-123"
    operation = "test_operation"
    error = Exception("Test error")
    data = {"test": "data"}

    await event_handler._emit_error(sid, operation, error, data)

    # Verify error was logged
    mock_system_logger.log_error.assert_called_once_with(
        error, {"operation": operation, "sid": sid, "data": data}
    )

    # Verify error response was emitted
    mock_sio.emit.assert_called_with("error", ANY, to=sid)
    error_data = mock_sio.emit.call_args[0][1]

    # Verify error response structure
    assert error_data["error"] is True
    assert error_data["error_type"] == "system_error"
    assert error_data["message"] == "Test error"
    assert error_data["details"]["operation"] == operation
    assert error_data["details"]["data"] == data

    # Verify user activity logging
    mock_user_logger.log_container_error.assert_called_once()


@pytest.mark.asyncio
async def test_status_change_callback():
    """Test status change callback."""
    # Create mocks
    mock_sio = Mock(spec=socketio.AsyncServer)
    mock_sio.emit = AsyncMock()
    mock_sio.on = Mock()

    mock_container_manager = Mock(spec=ContainerManager)
    mock_container_manager.register_status_change_callback = Mock()
    mock_container_manager.register_health_check_callback = Mock()
    mock_container_manager.register_crash_callback = Mock()

    mock_socket_handler = Mock(spec=SocketCommunicationHandler)
    mock_system_logger = Mock(spec=SystemLogger)

    mock_user_logger = Mock(spec=UserActivityLogger)
    mock_user_logger.log_user_activity = AsyncMock()

    # Create event handler
    event_handler = SocketIOEventHandler(
        sio=mock_sio,
        container_manager=mock_container_manager,
        socket_handler=mock_socket_handler,
        system_logger=mock_system_logger,
        user_logger=mock_user_logger,
    )

    container_id = "test-container-123"
    old_state = "stopped"
    new_state = "running"

    await event_handler._on_status_change(container_id, old_state, new_state)

    # Verify status change event was emitted
    mock_sio.emit.assert_called_with(
        "status_changed",
        {
            "container_id": container_id,
            "old_state": old_state,
            "new_state": new_state,
            "timestamp": ANY,
        },
    )

    # Verify user activity logging
    mock_user_logger.log_user_activity.assert_called_once_with(
        "status_change",
        container_id,
        f"Container status changed from {old_state} to {new_state}",
        {"old_state": old_state, "new_state": new_state},
    )
