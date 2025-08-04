"""
Comprehensive integration test for Task 11: Integrate all components in main application

This test verifies that all components are properly wired together and the main
application correctly integrates ContainerManager, SocketCommunicationHandler,
loggers, Socket.IO server, and FastAPI.
"""

import asyncio
from unittest.mock import Mock, AsyncMock, patch

import pytest
import socketio


class TestMainApplicationIntegration:
    """Test suite for main application integration."""

    @pytest.fixture
    def app_instance(self):
        """Create a test application instance with mocked Docker."""
        with patch("docker.from_env") as mock_docker:
            mock_docker.return_value = Mock()
            # Import here to avoid Docker connection during module import
            from main import FlowManagerApp
            from container_manager import ContainerManager
            from socket_communication_handler import SocketCommunicationHandler
            from socket_event_handler import SocketIOEventHandler
            from system_logger import SystemLogger
            from user_activity_logger import UserActivityLogger

            # Store classes for later use
            self.FlowManagerApp = FlowManagerApp
            self.ContainerManager = ContainerManager
            self.SocketCommunicationHandler = SocketCommunicationHandler
            self.SocketIOEventHandler = SocketIOEventHandler
            self.SystemLogger = SystemLogger
            self.UserActivityLogger = UserActivityLogger

            return FlowManagerApp(socket_dir="/tmp/test_sockets")

    def test_flow_manager_app_initialization(self, app_instance):
        """Test that FlowManagerApp initializes all components correctly."""
        # Verify all components are initialized
        assert isinstance(app_instance.system_logger, self.SystemLogger)
        assert isinstance(app_instance.sio, socketio.AsyncServer)
        assert isinstance(app_instance.user_logger, self.UserActivityLogger)
        assert isinstance(app_instance.container_manager, self.ContainerManager)
        assert isinstance(app_instance.socket_handler, self.SocketCommunicationHandler)
        assert isinstance(app_instance.event_handler, self.SocketIOEventHandler)

        # Verify socket directory is set correctly
        assert app_instance.socket_dir == "/tmp/test_sockets"

        # Verify Socket.IO configuration
        assert app_instance.sio.async_mode == "asgi"

    def test_dependency_injection(self, app_instance):
        """Test that components are properly injected into each other."""
        # Verify SocketIOEventHandler has correct dependencies
        assert app_instance.event_handler.sio is app_instance.sio
        assert (
            app_instance.event_handler.container_manager
            is app_instance.container_manager
        )
        assert app_instance.event_handler.socket_handler is app_instance.socket_handler
        assert app_instance.event_handler.system_logger is app_instance.system_logger
        assert app_instance.event_handler.user_logger is app_instance.user_logger

        # Verify UserActivityLogger has Socket.IO server
        assert app_instance.user_logger.sio is app_instance.sio

        # Verify SocketCommunicationHandler has logger
        assert app_instance.socket_handler.logger is app_instance.system_logger

    def test_socket_io_event_handlers_registered(self, app_instance):
        """Test that all Socket.IO event handlers are registered."""
        # Get registered handlers from Socket.IO server
        handlers = app_instance.sio.handlers

        # Verify all required event handlers are registered
        expected_events = [
            "connect",
            "disconnect",
            "create_container",
            "start_container",
            "stop_container",
            "restart_container",
            "update_container",
            "delete_container",
            "send_message",
            "get_container_status",
            "list_containers",
        ]

        for event in expected_events:
            assert event in handlers["/"], f"Event handler '{event}' not registered"

    def test_container_manager_callbacks_registered(self, app_instance):
        """Test that container manager callbacks are registered."""
        # Verify callbacks are registered (check if callback lists are not empty)
        assert len(app_instance.container_manager._status_change_callbacks) > 0
        assert len(app_instance.container_manager._health_check_callbacks) > 0
        assert len(app_instance.container_manager._crash_callbacks) > 0

    @pytest.mark.asyncio
    async def test_startup_sequence(self, app_instance):
        """Test application startup sequence."""
        with (
            patch("os.makedirs") as mock_makedirs,
            patch.object(
                app_instance.container_manager,
                "start_monitoring",
                new_callable=AsyncMock,
            ) as mock_start_monitoring,
        ):
            await app_instance.startup()

            # Verify socket directory creation
            mock_makedirs.assert_called_with("/tmp/test_sockets", exist_ok=True)

            # Verify container monitoring started
            mock_start_monitoring.assert_called_once()

            # Verify background tasks are created
            assert len(app_instance._background_tasks) > 0

    @pytest.mark.asyncio
    async def test_shutdown_sequence(self, app_instance):
        """Test application shutdown sequence."""
        # Mock background task
        mock_task = Mock()
        mock_task.done.return_value = False
        mock_task.cancel = Mock()
        app_instance._background_tasks = [mock_task]

        with (
            patch.object(
                app_instance.container_manager,
                "stop_monitoring",
                new_callable=AsyncMock,
            ) as mock_stop_monitoring,
            patch.object(
                app_instance.socket_handler,
                "close_all_connections",
                new_callable=AsyncMock,
            ) as mock_close_connections,
            patch("asyncio.gather", new_callable=AsyncMock),
        ):
            await app_instance.shutdown()

            # Verify shutdown event is set
            assert app_instance._shutdown_event.is_set()

            # Verify background task cancellation
            mock_task.cancel.assert_called_once()

            # Verify component shutdown
            mock_stop_monitoring.assert_called_once()
            mock_close_connections.assert_called_once()

    def test_fastapi_integration(self):
        """Test FastAPI integration with Socket.IO."""
        # Test that the main app module can be imported and has the expected structure
        with patch("docker.from_env") as mock_docker:
            mock_docker.return_value = Mock()
            from main import app, socket_app, app_instance

            # Verify that the main app is a Socket.IO ASGI app
            assert isinstance(app, socketio.ASGIApp)
            assert app_instance.sio is not None
            assert isinstance(app_instance.sio, socketio.AsyncServer)

            # Verify that socket_app is properly configured
            assert isinstance(socket_app, socketio.ASGIApp)

    @pytest.mark.asyncio
    async def test_health_check_loop(self, app_instance):
        """Test background health check loop functionality."""
        # Mock container manager methods
        mock_containers = [
            Mock(id="container1", name="test1"),
            Mock(id="container2", name="test2"),
        ]
        mock_status = Mock(
            state=Mock(value="running"),
            health=Mock(value="healthy"),
            socket_connected=True,
            uptime=None,
            resource_usage={},
        )

        with (
            patch.object(
                app_instance.container_manager,
                "list_containers",
                new_callable=AsyncMock,
                return_value=mock_containers,
            ),
            patch.object(
                app_instance.container_manager,
                "get_container_status",
                new_callable=AsyncMock,
                return_value=mock_status,
            ),
            patch.object(app_instance.sio, "emit", new_callable=AsyncMock),
        ):
            # Start health check loop
            health_task = asyncio.create_task(app_instance._health_check_loop())

            # Let it run briefly
            await asyncio.sleep(0.1)

            # Stop the loop
            app_instance._shutdown_event.set()

            # Wait for task to complete
            try:
                await asyncio.wait_for(health_task, timeout=1.0)
            except asyncio.TimeoutError:
                health_task.cancel()
                await asyncio.sleep(0.1)  # Give task time to cancel

    def test_socket_io_asgi_app_creation(self):
        """Test that Socket.IO ASGI app is properly created."""
        # Verify that the main app is a Socket.IO ASGI app
        with patch("docker.from_env") as mock_docker:
            mock_docker.return_value = Mock()
            from main import app, socket_app, app_instance

            # Verify that app is a Socket.IO ASGI app
            assert isinstance(app, socketio.ASGIApp)

            # Verify that the Socket.IO server is properly configured
            assert isinstance(app_instance.sio, socketio.AsyncServer)
            assert app_instance.sio.async_mode == "asgi"

            # Verify that socket_app is properly configured
            assert isinstance(socket_app, socketio.ASGIApp)

    @pytest.mark.asyncio
    async def test_component_error_handling(self, app_instance):
        """Test error handling in component integration."""
        # Test startup error handling
        with patch.object(
            app_instance.container_manager,
            "start_monitoring",
            side_effect=Exception("Test error"),
        ):
            with pytest.raises(Exception, match="Test error"):
                await app_instance.startup()

        # Test shutdown error handling (should not raise)
        with patch.object(
            app_instance.container_manager,
            "stop_monitoring",
            side_effect=Exception("Shutdown error"),
        ):
            # Should not raise exception
            await app_instance.shutdown()

    def test_logging_integration(self, app_instance):
        """Test that logging is properly integrated across components."""
        # Verify system logger is shared
        assert app_instance.socket_handler.logger is app_instance.system_logger

        # Verify user logger has Socket.IO server
        assert app_instance.user_logger.sio is app_instance.sio

        # Test that loggers are properly initialized
        assert app_instance.system_logger.logger.name == "flow_manager"

    @pytest.mark.asyncio
    async def test_socket_io_event_flow(self, app_instance):
        """Test complete Socket.IO event flow integration."""
        # Mock a client connection
        mock_sid = "test_session_id"
        mock_environ = {"HTTP_USER_AGENT": "test"}

        # Test connection handling
        await app_instance.event_handler.handle_connect(mock_sid, mock_environ)

        # Test disconnection handling
        await app_instance.event_handler.handle_disconnect(mock_sid)

    def test_configuration_consistency(self, app_instance):
        """Test that configuration is consistent across components."""
        # Verify socket directory consistency
        assert app_instance.container_manager.socket_dir == app_instance.socket_dir
        assert str(app_instance.socket_handler.socket_dir) == app_instance.socket_dir

    @pytest.mark.asyncio
    async def test_container_callback_integration(self, app_instance):
        """Test that container callbacks properly integrate with Socket.IO."""
        # Test status change callback
        await app_instance.event_handler._on_status_change(
            "test_container", "stopped", "running"
        )

        # Test health check failure callback
        await app_instance.event_handler._on_health_check_failure(
            "test_container", "unhealthy"
        )

        # Test container crash callback
        await app_instance.event_handler._on_container_crash(
            "test_container", 1, {"error": "test"}
        )

    def test_all_requirements_covered(self, app_instance):
        """Test that all task requirements are satisfied."""
        # Requirement: Wire together ContainerManager, SocketCommunicationHandler, and loggers
        assert app_instance.container_manager is not None
        assert app_instance.socket_handler is not None
        assert app_instance.system_logger is not None
        assert app_instance.user_logger is not None

        # Requirement: Set up Socket.IO server with event handlers
        assert app_instance.sio is not None
        assert app_instance.event_handler is not None
        assert len(app_instance.sio.handlers["/"]) > 0

        # Requirement: Configure FastAPI integration with Socket.IO
        # Verified by the fact that app is a Socket.IO ASGI app

        # Requirement: Add proper dependency injection and initialization
        # Verified by dependency injection tests above
