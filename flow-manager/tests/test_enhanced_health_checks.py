"""
Tests for enhanced container health checks functionality.

This module tests the customizable health check mechanisms, automatic recovery,
health status history tracking, and health check configuration options.
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from container_manager import ContainerManager
from models import (
    HealthCheckConfig,
    HealthCheckType,
    HealthCheckResult,
    HealthStatusHistory,
    ContainerHealth,
    HealthCheckConfigEvent,
)
from socket_event_handler import SocketIOEventHandler
from system_logger import SystemLogger
from user_activity_logger import UserActivityLogger


class TestEnhancedHealthChecks:
    """Test enhanced health check functionality."""

    @pytest.fixture
    def mock_docker_client(self):
        """Mock Docker client."""
        client = Mock()
        client.containers = Mock()
        return client

    @pytest.fixture
    def mock_container(self):
        """Mock Docker container."""
        container = Mock()
        container.id = "test_container_123"
        container.name = "test_container"
        container.status = "running"
        container.attrs = {
            "State": {
                "Status": "running",
                "Health": {"Status": "healthy"},
                "StartedAt": "2025-01-19T10:00:00Z",
            },
            "NetworkSettings": {"IPAddress": "172.17.0.2"},
            "Config": {"Env": []},
        }
        container.reload = Mock()
        container.exec_run = Mock()
        return container

    @pytest.fixture
    def container_manager(self, mock_docker_client):
        """Container manager with mocked Docker client."""
        with patch(
            "container_manager.docker.from_env", return_value=mock_docker_client
        ):
            manager = ContainerManager()
            return manager

    @pytest.fixture
    def mock_sio(self):
        """Mock Socket.IO server."""
        sio = AsyncMock()
        return sio

    @pytest.fixture
    def socket_handler(self, socket_event_handler):
        """Socket.IO event handler."""
        return socket_event_handler

    def test_health_check_config_creation(self):
        """Test creating health check configurations."""
        # Test HTTP health check config
        http_config = HealthCheckConfig(
            enabled=True,
            check_type=HealthCheckType.HTTP,
            endpoint="/health",
            port=8080,
            interval=30,
            timeout=10,
            retries=3,
            auto_recovery=True,
            recovery_action="restart",
        )

        assert http_config.enabled is True
        assert http_config.check_type == HealthCheckType.HTTP
        assert http_config.endpoint == "/health"
        assert http_config.port == 8080
        assert http_config.interval == 30
        assert http_config.timeout == 10
        assert http_config.retries == 3
        assert http_config.auto_recovery is True
        assert http_config.recovery_action == "restart"

        # Test TCP health check config
        tcp_config = HealthCheckConfig(
            check_type=HealthCheckType.TCP,
            port=5432,
            interval=60,
        )

        assert tcp_config.check_type == HealthCheckType.TCP
        assert tcp_config.port == 5432
        assert tcp_config.interval == 60

        # Test command health check config
        cmd_config = HealthCheckConfig(
            check_type=HealthCheckType.COMMAND,
            command=["curl", "-f", "http://localhost:8080/health"],
            interval=45,
        )

        assert cmd_config.check_type == HealthCheckType.COMMAND
        assert cmd_config.command == ["curl", "-f", "http://localhost:8080/health"]

    def test_health_check_config_validation(self):
        """Test health check configuration validation."""
        # Test invalid interval
        with pytest.raises(
            ValueError, match="Health check interval must be at least 5 seconds"
        ):
            HealthCheckConfig(interval=3)

        # Test invalid timeout
        with pytest.raises(
            ValueError, match="Health check timeout must be at least 1 second"
        ):
            HealthCheckConfig(timeout=0)

        # Test invalid retries
        with pytest.raises(ValueError, match="Health check retries must be at least 1"):
            HealthCheckConfig(retries=0)

        # Test invalid recovery action
        with pytest.raises(ValueError, match="Recovery action must be one of"):
            HealthCheckConfig(recovery_action="invalid_action")

    def test_health_status_history(self):
        """Test health status history tracking."""
        history = HealthStatusHistory(container_id="test_container")

        # Test initial state
        assert history.container_id == "test_container"
        assert history.current_health == ContainerHealth.NONE
        assert history.consecutive_failures == 0
        assert len(history.history) == 0

        # Add successful health check result
        success_result = HealthCheckResult(
            container_id="test_container",
            health=ContainerHealth.HEALTHY,
            check_type=HealthCheckType.HTTP,
            success=True,
            response_time=0.5,
        )

        history.add_result(success_result)

        assert history.current_health == ContainerHealth.HEALTHY
        assert history.consecutive_failures == 0
        assert history.last_healthy is not None
        assert len(history.history) == 1

        # Add failed health check result
        failure_result = HealthCheckResult(
            container_id="test_container",
            health=ContainerHealth.UNHEALTHY,
            check_type=HealthCheckType.HTTP,
            success=False,
            response_time=None,
            error_message="Connection timeout",
        )

        history.add_result(failure_result)

        assert history.current_health == ContainerHealth.UNHEALTHY
        assert history.consecutive_failures == 1
        assert history.last_unhealthy is not None
        assert len(history.history) == 2

    def test_should_recover_logic(self):
        """Test recovery decision logic."""
        config = HealthCheckConfig(
            auto_recovery=True,
            recovery_action="restart",
            max_recovery_attempts=3,
            recovery_cooldown=300,
        )

        history = HealthStatusHistory(container_id="test_container")
        history.current_health = ContainerHealth.UNHEALTHY

        # Should recover when unhealthy and within limits
        assert history.should_recover(config) is True

        # Should not recover when auto_recovery is disabled
        config.auto_recovery = False
        assert history.should_recover(config) is False

        # Should not recover when recovery_action is "none"
        config.auto_recovery = True
        config.recovery_action = "none"
        assert history.should_recover(config) is False

        # Should not recover when max attempts reached
        config.recovery_action = "restart"
        history.recovery_attempts = 3
        assert history.should_recover(config) is False

        # Should not recover during cooldown period
        history.recovery_attempts = 1
        history.last_recovery_attempt = datetime.now() - timedelta(seconds=100)
        assert history.should_recover(config) is False

        # Should recover after cooldown period
        history.last_recovery_attempt = datetime.now() - timedelta(seconds=400)
        assert history.should_recover(config) is True

    @pytest.mark.asyncio
    async def test_set_health_check_config(self, container_manager):
        """Test setting health check configuration."""
        container_id = "test_container"
        config = HealthCheckConfig(
            enabled=True,
            check_type=HealthCheckType.HTTP,
            endpoint="/health",
            port=8080,
        )

        # Set configuration
        container_manager.set_health_check_config(container_id, config)

        # Verify configuration was set
        retrieved_config = container_manager.get_health_check_config(container_id)
        assert retrieved_config is not None
        assert retrieved_config.enabled is True
        assert retrieved_config.check_type == HealthCheckType.HTTP
        assert retrieved_config.endpoint == "/health"
        assert retrieved_config.port == 8080

        # Verify history was initialized
        history = container_manager.get_health_status_history(container_id)
        assert history is not None
        assert history.container_id == container_id

    def test_default_health_config(self, container_manager):
        """Test default health check configuration."""
        # Get default config
        default_config = container_manager.get_default_health_config()
        assert default_config is not None
        assert isinstance(default_config, HealthCheckConfig)

        # Set custom default config
        custom_config = HealthCheckConfig(
            check_type=HealthCheckType.TCP,
            port=5432,
            interval=60,
        )

        container_manager.set_default_health_config(custom_config)

        # Verify custom default was set
        retrieved_default = container_manager.get_default_health_config()
        assert retrieved_default.check_type == HealthCheckType.TCP
        assert retrieved_default.port == 5432
        assert retrieved_default.interval == 60

    @pytest.mark.asyncio
    async def test_http_health_check(self, container_manager, mock_container):
        """Test HTTP health check implementation."""
        config = HealthCheckConfig(
            check_type=HealthCheckType.HTTP,
            endpoint="/health",
            port=8080,
            timeout=5,
        )

        # Mock successful HTTP response
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.headers = {"Content-Type": "application/json"}

            # Set up the async context manager properly
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)

            # Set up the get method to return an async context manager
            mock_get_context = AsyncMock()
            mock_get_context.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get_context.__aexit__ = AsyncMock(return_value=None)
            mock_session.get = Mock(
                return_value=mock_get_context
            )  # Make get() synchronous

            mock_session_class.return_value = mock_session

            # Perform health check
            (
                success,
                error_message,
                details,
            ) = await container_manager._http_health_check(mock_container, config)

            assert success is True
            assert error_message is None
            assert details["status_code"] == 200
            assert "url" in details

    @pytest.mark.asyncio
    async def test_tcp_health_check(self, container_manager, mock_container):
        """Test TCP health check implementation."""
        config = HealthCheckConfig(
            check_type=HealthCheckType.TCP,
            port=5432,
            timeout=5,
        )

        # Mock successful TCP connection
        with patch("asyncio.open_connection") as mock_open_connection:
            mock_reader = AsyncMock()
            mock_writer = AsyncMock()
            mock_writer.close = Mock()  # Make close() synchronous
            mock_open_connection.return_value = (mock_reader, mock_writer)

            # Perform health check
            success, error_message, details = await container_manager._tcp_health_check(
                mock_container, config
            )

            assert success is True
            assert error_message is None
            assert details["host"] == "172.17.0.2"
            assert details["port"] == 5432

    @pytest.mark.asyncio
    async def test_command_health_check(self, container_manager, mock_container):
        """Test command-based health check implementation."""
        config = HealthCheckConfig(
            check_type=HealthCheckType.COMMAND,
            command=["echo", "healthy"],
        )

        # Mock successful command execution
        mock_result = Mock()
        mock_result.exit_code = 0
        mock_result.output = b"healthy\n"
        mock_container.exec_run.return_value = mock_result

        # Perform health check
        success, error_message, details = await container_manager._command_health_check(
            mock_container, config
        )

        assert success is True
        assert error_message is None
        assert details["exit_code"] == 0
        assert details["output"] == "healthy\n"

    @pytest.mark.asyncio
    async def test_socket_health_check(self, container_manager, mock_container):
        """Test Unix socket health check implementation."""
        config = HealthCheckConfig(
            check_type=HealthCheckType.SOCKET,
            timeout=5,
        )

        # Mock socket file existence and connection
        with (
            patch("os.path.exists", return_value=True),
            patch("asyncio.open_unix_connection") as mock_open_unix,
        ):
            mock_reader = AsyncMock()
            mock_writer = AsyncMock()
            mock_reader.readline.return_value = b'{"status": "ok"}\n'
            mock_writer.write = Mock()  # Make write() synchronous
            mock_writer.close = Mock()  # Make close() synchronous
            mock_open_unix.return_value = (mock_reader, mock_writer)

            # Perform health check
            (
                success,
                error_message,
                details,
            ) = await container_manager._socket_health_check(mock_container, config)

            assert success is True
            assert error_message is None
            assert "socket_path" in details
            assert details["response"] == '{"status": "ok"}'

    @pytest.mark.asyncio
    async def test_health_check_event_handlers(self, socket_handler, mock_sio):
        """Test Socket.IO health check event handlers."""
        # Test set_health_check_config event
        config_data = {
            "container_id": "test_container",
            "config": {
                "enabled": True,
                "check_type": "http",
                "endpoint": "/health",
                "port": 8080,
                "interval": 30,
                "timeout": 10,
                "retries": 3,
                "auto_recovery": True,
                "recovery_action": "restart",
            },
        }

        await socket_handler.handle_set_health_check_config("test_sid", config_data)

        # Verify response was emitted (check all calls to find the right one)
        mock_sio.emit.assert_called()
        calls = mock_sio.emit.call_args_list

        # Find the health_check_config_set call
        config_set_call = None
        for call in calls:
            if call[0][0] == "health_check_config_set":
                config_set_call = call
                break

        assert (
            config_set_call is not None
        ), f"Expected 'health_check_config_set' event, got calls: {[call[0][0] for call in calls]}"
        assert config_set_call[0][1]["container_id"] == "test_container"

        # Test get_health_check_config event
        get_data = {"container_id": "test_container"}
        await socket_handler.handle_get_health_check_config("test_sid", get_data)

        # Verify response was emitted
        mock_sio.emit.assert_called()
        call_args = mock_sio.emit.call_args
        assert call_args[0][0] == "health_check_config"

    @pytest.mark.asyncio
    async def test_health_status_history_event_handler(self, socket_handler, mock_sio):
        """Test health status history event handler."""
        # First set up a health check config to create history
        container_id = "test_container"
        config = HealthCheckConfig(enabled=True)
        socket_handler.container_manager.set_health_check_config(container_id, config)

        # Add some history
        history = socket_handler.container_manager.get_health_status_history(
            container_id
        )
        result = HealthCheckResult(
            container_id=container_id,
            health=ContainerHealth.HEALTHY,
            check_type=HealthCheckType.HTTP,
            success=True,
            response_time=0.5,
        )
        history.add_result(result)

        # Test get_health_status_history event
        history_data = {"container_id": container_id, "limit": 10}
        await socket_handler.handle_get_health_status_history("test_sid", history_data)

        # Verify response was emitted
        mock_sio.emit.assert_called()
        call_args = mock_sio.emit.call_args
        assert call_args[0][0] == "health_status_history"
        assert call_args[0][1]["container_id"] == container_id
        assert len(call_args[0][1]["history"]) == 1

    @pytest.mark.asyncio
    async def test_default_health_config_event_handlers(self, socket_handler, mock_sio):
        """Test default health config event handlers."""
        # Test set_default_health_config event
        config_data = {
            "config": {
                "enabled": True,
                "check_type": "tcp",
                "port": 5432,
                "interval": 60,
            }
        }

        await socket_handler.handle_set_default_health_config("test_sid", config_data)

        # Verify response was emitted (check all calls to find the right one)
        mock_sio.emit.assert_called()
        calls = mock_sio.emit.call_args_list

        # Find the default_health_config_set call
        config_set_call = None
        for call in calls:
            if call[0][0] == "default_health_config_set":
                config_set_call = call
                break

        assert (
            config_set_call is not None
        ), f"Expected 'default_health_config_set' event, got calls: {[call[0][0] for call in calls]}"
        assert (
            config_set_call[0][1]["config"]["check_type"] == "tcp"
            or config_set_call[0][1]["config"]["check_type"] == HealthCheckType.TCP
        )

        # Test get_default_health_config event
        await socket_handler.handle_get_default_health_config("test_sid", {})

        # Verify response was emitted
        mock_sio.emit.assert_called()
        call_args = mock_sio.emit.call_args
        assert call_args[0][0] == "default_health_config"

    @pytest.mark.asyncio
    async def test_automatic_recovery(self, container_manager, mock_container):
        """Test automatic recovery functionality."""
        container_id = "test_container"

        # Set up health check config with recovery enabled
        config = HealthCheckConfig(
            enabled=True,
            auto_recovery=True,
            recovery_action="restart",
            max_recovery_attempts=2,
        )

        container_manager.set_health_check_config(container_id, config)
        history = container_manager.get_health_status_history(container_id)

        # Simulate unhealthy state
        history.current_health = ContainerHealth.UNHEALTHY

        # Mock container manager methods
        with patch.object(
            container_manager, "restart_container", new_callable=AsyncMock
        ) as mock_restart:
            # Attempt recovery
            await container_manager._attempt_recovery(container_id, config, history)

            # Verify restart was called
            mock_restart.assert_called_once_with(container_id)

            # Verify recovery attempt was recorded
            assert history.recovery_attempts == 1
            assert history.last_recovery_attempt is not None

    def test_health_check_config_event_validation(self):
        """Test health check configuration event validation."""
        # Test valid event data
        valid_data = {
            "container_id": "test_container",
            "config": {
                "enabled": True,
                "check_type": "http",
                "endpoint": "/health",
                "port": 8080,
            },
        }

        event = HealthCheckConfigEvent(**valid_data)
        assert event.container_id == "test_container"
        assert event.config.enabled is True
        assert event.config.check_type == HealthCheckType.HTTP

        # Test invalid container_id
        with pytest.raises(ValueError):
            HealthCheckConfigEvent(container_id="", config=valid_data["config"])

        # Test invalid config - missing required fields
        with pytest.raises(ValueError):
            HealthCheckConfigEvent(
                container_id="test_container",
                config={"invalid": "config", "enabled": "not_boolean"},
            )

    @pytest.mark.asyncio
    async def test_health_check_cleanup(self, container_manager):
        """Test health check resource cleanup."""
        container_id = "test_container"

        # Set up health check
        config = HealthCheckConfig(enabled=True)
        container_manager.set_health_check_config(container_id, config)

        # Verify resources exist
        assert container_id in container_manager._health_check_configs
        assert container_id in container_manager._health_status_history

        # Clean up resources
        container_manager._cleanup_health_check_resources(container_id)

        # Verify resources were cleaned up
        assert container_id not in container_manager._health_check_configs
        assert container_id not in container_manager._health_status_history

    @pytest.mark.asyncio
    async def test_health_check_loop_cancellation(self, container_manager):
        """Test health check loop cancellation."""
        container_id = "test_container"

        # Set up health check config
        config = HealthCheckConfig(enabled=True, interval=5)
        container_manager.set_health_check_config(container_id, config)

        # Verify task was started
        assert container_id in container_manager._health_check_tasks
        task = container_manager._health_check_tasks[container_id]
        assert not task.done()

        # Stop health check task
        container_manager._stop_health_check_task(container_id)

        # Give a small delay for task cancellation to complete
        await asyncio.sleep(0.1)

        # Verify task was cancelled and removed
        assert container_id not in container_manager._health_check_tasks
        assert task.cancelled()
