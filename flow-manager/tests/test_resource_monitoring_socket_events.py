"""
Tests for resource monitoring Socket.IO event handlers.

This module tests the Socket.IO event handlers for resource monitoring functionality
including threshold management, resource usage history, and monitoring control.
"""

import tempfile
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
import socketio

from container_manager import ContainerManager
from socket_communication_handler import SocketCommunicationHandler
from socket_event_handler import SocketIOEventHandler
from system_logger import SystemLogger
from user_activity_logger import UserActivityLogger


@pytest.mark.asyncio
class TestResourceMonitoringSocketEvents:
    """Test resource monitoring Socket.IO event handlers."""

    @pytest_asyncio.fixture(autouse=True)
    async def setup_test(self):
        """Set up test fixtures and tear down after test."""
        # Setup
        self.temp_dir = tempfile.mkdtemp()

        # Create a patcher for Docker client
        self.docker_patcher = patch("container_manager.docker")
        self.mock_docker = self.docker_patcher.start()

        # Mock Docker client to avoid connection issues
        self.mock_docker_client = Mock()
        self.mock_docker.from_env.return_value = self.mock_docker_client

        # Create Socket.IO server
        self.sio = socketio.AsyncServer(async_mode="asgi")

        # Create components
        self.container_manager = ContainerManager(socket_dir=self.temp_dir)
        self.container_manager.docker_client = self.mock_docker_client

        self.socket_handler = SocketCommunicationHandler(socket_dir=self.temp_dir)
        self.system_logger = SystemLogger()
        self.user_logger = UserActivityLogger(self.sio)

        # Create event handler
        self.event_handler = SocketIOEventHandler(
            self.sio,
            self.container_manager,
            self.socket_handler,
            self.system_logger,
            self.user_logger,
        )

        # Mock SIO emit to track calls
        self.sio.emit = AsyncMock()

        yield

        # Teardown
        self.docker_patcher.stop()

        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_handle_get_resource_thresholds(self):
        """Test getting resource thresholds via Socket.IO."""
        sid = "test_session"
        data = {}

        await self.event_handler.handle_get_resource_thresholds(sid, data)

        # Verify response was emitted
        self.sio.emit.assert_called_once()
        call_args = self.sio.emit.call_args
        assert call_args[0][0] == "resource_thresholds"
        assert "thresholds" in call_args[0][1]
        assert call_args[1]["to"] == sid

    @pytest.mark.asyncio
    async def test_handle_set_resource_thresholds_success(self):
        """Test setting resource thresholds via Socket.IO."""
        sid = "test_session"
        data = {
            "thresholds": {
                "cpu_percent": 90.0,
                "memory_percent": 95.0,
            }
        }

        await self.event_handler.handle_set_resource_thresholds(sid, data)

        # Verify thresholds were set
        thresholds = self.container_manager.get_resource_thresholds()
        assert thresholds["cpu_percent"] == 90.0
        assert thresholds["memory_percent"] == 95.0

        # Verify response was emitted
        self.sio.emit.assert_called()
        # Check that resource_thresholds_updated was emitted (may not be the last call due to activity logging)
        calls = self.sio.emit.call_args_list
        threshold_update_calls = [
            call for call in calls if call[0][0] == "resource_thresholds_updated"
        ]
        assert len(threshold_update_calls) == 1
        assert "thresholds" in threshold_update_calls[0][0][1]

    @pytest.mark.asyncio
    async def test_handle_set_resource_thresholds_missing_field(self):
        """Test setting resource thresholds with missing thresholds field."""
        sid = "test_session"
        data = {}

        await self.event_handler.handle_set_resource_thresholds(sid, data)

        # Verify error was emitted
        self.sio.emit.assert_called()
        # Check that error was emitted (may not be the last call due to activity logging)
        calls = self.sio.emit.call_args_list
        error_calls = [call for call in calls if call[0][0] == "error"]
        assert len(error_calls) == 1
        assert "Missing 'thresholds' field" in error_calls[0][0][1]["message"]

    @pytest.mark.asyncio
    async def test_handle_set_resource_thresholds_invalid_type(self):
        """Test setting resource thresholds with invalid type."""
        sid = "test_session"
        data = {"thresholds": "not_a_dict"}

        await self.event_handler.handle_set_resource_thresholds(sid, data)

        # Verify error was emitted
        self.sio.emit.assert_called()
        # Check that error was emitted (may not be the last call due to activity logging)
        calls = self.sio.emit.call_args_list
        error_calls = [call for call in calls if call[0][0] == "error"]
        assert len(error_calls) == 1
        assert "Thresholds must be a dictionary" in error_calls[0][0][1]["message"]

    @pytest.mark.asyncio
    async def test_handle_set_resource_thresholds_invalid_key(self):
        """Test setting resource thresholds with invalid key."""
        sid = "test_session"
        data = {
            "thresholds": {
                "invalid_key": 50.0,
            }
        }

        await self.event_handler.handle_set_resource_thresholds(sid, data)

        # Verify error was emitted
        self.sio.emit.assert_called()
        # Check that error was emitted (may not be the last call due to activity logging)
        calls = self.sio.emit.call_args_list
        error_calls = [call for call in calls if call[0][0] == "error"]
        assert len(error_calls) == 1
        assert "Invalid threshold key: invalid_key" in error_calls[0][0][1]["message"]

    @pytest.mark.asyncio
    async def test_handle_set_resource_thresholds_invalid_value(self):
        """Test setting resource thresholds with invalid value."""
        sid = "test_session"
        data = {
            "thresholds": {
                "cpu_percent": -10.0,  # Negative value
            }
        }

        await self.event_handler.handle_set_resource_thresholds(sid, data)

        # Verify error was emitted
        self.sio.emit.assert_called()
        # Check that error was emitted (may not be the last call due to activity logging)
        calls = self.sio.emit.call_args_list
        error_calls = [call for call in calls if call[0][0] == "error"]
        assert len(error_calls) == 1
        assert (
            "Threshold value must be a positive number"
            in error_calls[0][0][1]["message"]
        )

    @pytest.mark.asyncio
    async def test_handle_get_resource_usage_history_success(self):
        """Test getting resource usage history via Socket.IO."""
        sid = "test_session"
        container_id = "test_container"
        data = {"container_id": container_id, "limit": 5}

        # Add some mock history
        self.container_manager._resource_usage_history[container_id] = [
            {"timestamp": "2025-01-19T10:00:00", "cpu_percent": 50.0},
            {"timestamp": "2025-01-19T10:01:00", "cpu_percent": 60.0},
        ]

        await self.event_handler.handle_get_resource_usage_history(sid, data)

        # Verify response was emitted
        self.sio.emit.assert_called_once()
        call_args = self.sio.emit.call_args
        assert call_args[0][0] == "resource_usage_history"
        assert call_args[0][1]["container_id"] == container_id
        assert len(call_args[0][1]["history"]) == 2
        assert call_args[0][1]["limit"] == 5

    @pytest.mark.asyncio
    async def test_handle_get_resource_usage_history_missing_container_id(self):
        """Test getting resource usage history without container_id."""
        sid = "test_session"
        data = {"limit": 5}

        await self.event_handler.handle_get_resource_usage_history(sid, data)

        # Verify error was emitted
        self.sio.emit.assert_called()
        # Check that error was emitted (may not be the last call due to activity logging)
        calls = self.sio.emit.call_args_list
        error_calls = [call for call in calls if call[0][0] == "error"]
        assert len(error_calls) == 1
        assert "Missing 'container_id' field" in error_calls[0][0][1]["message"]

    @pytest.mark.asyncio
    async def test_handle_get_resource_usage_history_invalid_limit(self):
        """Test getting resource usage history with invalid limit."""
        sid = "test_session"
        data = {"container_id": "test_container", "limit": -1}

        await self.event_handler.handle_get_resource_usage_history(sid, data)

        # Verify error was emitted
        self.sio.emit.assert_called()
        # Check that error was emitted (may not be the last call due to activity logging)
        calls = self.sio.emit.call_args_list
        error_calls = [call for call in calls if call[0][0] == "error"]
        assert len(error_calls) == 1
        assert "Limit must be a non-negative integer" in error_calls[0][0][1]["message"]

    @pytest.mark.asyncio
    async def test_handle_get_resource_usage_history_default_limit(self):
        """Test getting resource usage history with default limit."""
        sid = "test_session"
        container_id = "test_container"
        data = {"container_id": container_id}  # No limit specified

        await self.event_handler.handle_get_resource_usage_history(sid, data)

        # Verify response was emitted with default limit
        self.sio.emit.assert_called_once()
        call_args = self.sio.emit.call_args
        assert call_args[0][0] == "resource_usage_history"
        assert call_args[0][1]["limit"] == 10  # Default limit

    @pytest.mark.asyncio
    async def test_handle_enable_resource_monitoring(self):
        """Test enabling resource monitoring via Socket.IO."""
        sid = "test_session"
        data = {}

        # Disable monitoring first
        self.container_manager.disable_resource_monitoring()
        assert not self.container_manager._resource_monitoring_enabled

        await self.event_handler.handle_enable_resource_monitoring(sid, data)

        # Verify monitoring was enabled
        assert self.container_manager._resource_monitoring_enabled

        # Verify response was emitted
        self.sio.emit.assert_called()
        # Check that resource_monitoring_enabled was emitted (may not be the last call due to activity logging)
        calls = self.sio.emit.call_args_list
        enabled_calls = [
            call for call in calls if call[0][0] == "resource_monitoring_enabled"
        ]
        assert len(enabled_calls) == 1
        assert enabled_calls[0][0][1]["enabled"] is True

    @pytest.mark.asyncio
    async def test_handle_disable_resource_monitoring(self):
        """Test disabling resource monitoring via Socket.IO."""
        sid = "test_session"
        data = {}

        # Ensure monitoring is enabled first
        self.container_manager.enable_resource_monitoring()
        assert self.container_manager._resource_monitoring_enabled

        await self.event_handler.handle_disable_resource_monitoring(sid, data)

        # Verify monitoring was disabled
        assert not self.container_manager._resource_monitoring_enabled

        # Verify response was emitted
        self.sio.emit.assert_called()
        # Check that resource_monitoring_disabled was emitted (may not be the last call due to activity logging)
        calls = self.sio.emit.call_args_list
        disabled_calls = [
            call for call in calls if call[0][0] == "resource_monitoring_disabled"
        ]
        assert len(disabled_calls) == 1
        assert disabled_calls[0][0][1]["enabled"] is False

    @pytest.mark.asyncio
    async def test_resource_alert_callback(self):
        """Test resource alert callback emits Socket.IO event."""
        container_id = "test_container"
        resource_type = "cpu_percent"
        current_value = 95.0
        threshold = 80.0
        usage_data = {"cpu_percent": 95.0, "memory_percent": 50.0}

        await self.event_handler._on_resource_alert(
            container_id, resource_type, current_value, threshold, usage_data
        )

        # Verify alert was emitted
        self.sio.emit.assert_called()
        # Check that resource_alert was emitted (may not be the last call due to activity logging)
        calls = self.sio.emit.call_args_list
        alert_calls = [call for call in calls if call[0][0] == "resource_alert"]
        assert len(alert_calls) == 1
        alert_data = alert_calls[0][0][1]
        assert alert_data["container_id"] == container_id
        assert alert_data["resource_type"] == resource_type
        assert alert_data["current_value"] == current_value
        assert alert_data["threshold"] == threshold
        assert alert_data["usage_data"] == usage_data

    @pytest.mark.asyncio
    async def test_resource_alert_callback_error_handling(self):
        """Test resource alert callback handles errors gracefully."""
        # Mock sio.emit to raise an exception
        self.sio.emit.side_effect = Exception("Emit failed")

        container_id = "test_container"
        resource_type = "cpu_percent"
        current_value = 95.0
        threshold = 80.0
        usage_data = {"cpu_percent": 95.0}

        # Should not raise exception
        await self.event_handler._on_resource_alert(
            container_id, resource_type, current_value, threshold, usage_data
        )

        # Verify emit was attempted
        self.sio.emit.assert_called_once()

    @pytest.mark.asyncio
    async def test_all_valid_threshold_keys(self):
        """Test that all valid threshold keys are accepted."""
        sid = "test_session"
        data = {
            "thresholds": {
                "cpu_percent": 90.0,
                "memory_percent": 95.0,
                "disk_read_bytes_per_sec": 100000000,
                "disk_write_bytes_per_sec": 100000000,
                "network_rx_bytes_per_sec": 50000000,
                "network_tx_bytes_per_sec": 50000000,
            }
        }

        await self.event_handler.handle_set_resource_thresholds(sid, data)

        # Verify all thresholds were set
        thresholds = self.container_manager.get_resource_thresholds()
        for key, value in data["thresholds"].items():
            assert thresholds[key] == value

        # Verify success response was emitted
        self.sio.emit.assert_called()
        # Check that resource_thresholds_updated was emitted (may not be the last call due to activity logging)
        calls = self.sio.emit.call_args_list
        threshold_update_calls = [
            call for call in calls if call[0][0] == "resource_thresholds_updated"
        ]
        assert len(threshold_update_calls) == 1

    @pytest.mark.asyncio
    async def test_resource_monitoring_integration(self):
        """Test integration between resource monitoring and Socket.IO events."""
        # Register the resource alert callback
        self.container_manager.register_resource_alert_callback(
            self.event_handler._on_resource_alert
        )

        # Set low threshold
        self.container_manager.set_resource_thresholds({"cpu_percent": 10.0})

        # Mock container with high CPU usage
        mock_container = Mock()
        mock_container.id = "test_container_id"
        mock_container.stats.return_value = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 8000000000},
                "system_cpu_usage": 10000000000,
                "online_cpus": 2,
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 2000000000},
                "system_cpu_usage": 8000000000,
            },
            "memory_stats": {"usage": 268435456, "limit": 536870912},
            "networks": {},
            "blkio_stats": {"io_service_bytes_recursive": []},
        }

        # Trigger resource usage check
        await self.container_manager._check_resource_usage(mock_container)

        # Verify resource alert was emitted
        self.sio.emit.assert_called()
        # Check that resource_alert was emitted (may not be the last call due to activity logging)
        calls = self.sio.emit.call_args_list
        alert_calls = [call for call in calls if call[0][0] == "resource_alert"]
        # The callback is registered twice (once in event handler init, once in test), so we get 2 alerts
        assert len(alert_calls) >= 1
        assert alert_calls[0][0][1]["container_id"] == "test_container_id"
        assert alert_calls[0][0][1]["resource_type"] == "cpu_percent"
