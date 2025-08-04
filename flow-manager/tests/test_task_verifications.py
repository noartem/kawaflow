"""
Tests for verifying task implementations.

This module contains tests that verify the implementation of specific tasks
from the container lifecycle management spec.
"""

import pytest
from unittest.mock import Mock, patch

from container_manager import ContainerManager
from socket_communication_handler import SocketCommunicationHandler
from socket_event_handler import SocketIOEventHandler
from system_logger import SystemLogger
from user_activity_logger import UserActivityLogger
from models import ContainerState, ContainerHealth


class TestTask1Verification:
    """Tests for Task 1: Set up project structure and core data models."""

    def test_data_models_exist(self):
        """Test that core data models are implemented."""
        from models import (
            ContainerState,
            ContainerConfig,
        )

        # Verify enums
        assert hasattr(ContainerState, "RUNNING")
        assert hasattr(ContainerState, "STOPPED")
        assert hasattr(ContainerHealth, "HEALTHY")
        assert hasattr(ContainerHealth, "UNHEALTHY")

        # Create instances to verify models work
        config = ContainerConfig(image="test:latest")
        assert config.image == "test:latest"


class TestTask2Verification:
    """Tests for Task 2: Implement system logging infrastructure."""

    def test_system_logger_implementation(self):
        """Test that SystemLogger is properly implemented."""
        logger = SystemLogger("test_logger")

        # Verify logger methods exist
        assert hasattr(logger, "log_container_operation")
        assert hasattr(logger, "log_socket_event")
        assert hasattr(logger, "log_communication")
        assert hasattr(logger, "log_error")
        assert hasattr(logger, "log_state_change")
        assert hasattr(logger, "log_debug")


class TestTask3Verification:
    """Tests for Task 3: Implement user activity logging with Socket.IO integration."""

    def test_user_activity_logger_implementation(self, mock_sio):
        """Test that UserActivityLogger is properly implemented."""
        logger = UserActivityLogger(mock_sio)

        # Verify logger methods exist
        assert hasattr(logger, "log_container_created")
        assert hasattr(logger, "log_container_started")
        assert hasattr(logger, "log_container_stopped")
        assert hasattr(logger, "log_container_message")
        assert hasattr(logger, "log_actor_event")
        assert hasattr(logger, "log_user_activity")


class TestTask4Verification:
    """Tests for Task 4: Create container manager core functionality."""

    def test_container_manager_implementation(self):
        """Test that ContainerManager is properly implemented."""
        with patch("docker.from_env"):
            manager = ContainerManager()

            # Verify manager methods exist
            assert hasattr(manager, "create_container")
            assert hasattr(manager, "start_container")
            assert hasattr(manager, "stop_container")
            assert hasattr(manager, "restart_container")
            assert hasattr(manager, "delete_container")


class TestTask5Verification:
    """Tests for Task 5: Implement Unix socket communication handler."""

    def test_socket_communication_handler_implementation(
        self, temp_socket_dir, mock_logger
    ):
        """Test that SocketCommunicationHandler is properly implemented."""
        handler = SocketCommunicationHandler(
            socket_dir=temp_socket_dir, logger=mock_logger
        )

        # Verify handler methods exist
        assert hasattr(handler, "setup_socket")
        assert hasattr(handler, "cleanup_socket")
        assert hasattr(handler, "send_message")
        assert hasattr(handler, "receive_message")
        assert hasattr(handler, "is_socket_connected")
        assert hasattr(handler, "close_all_connections")


class TestTask6Verification:
    """Tests for Task 6: Add container update functionality."""

    @pytest.mark.asyncio
    async def test_container_update_implementation(
        self, container_manager, mock_container
    ):
        """Test that container update functionality is implemented."""
        # Setup
        container_manager.docker_client.containers.get.return_value = mock_container
        mock_container.status = "running"  # Set container status to running

        # Mock os.listdir to return a list of files
        mock_files = ["file1.py", "file2.py", "config.json"]

        # Create a mock for the new container
        mock_new_container = Mock()
        container_manager.docker_client.containers.create.return_value = (
            mock_new_container
        )

        with (
            patch("os.path.exists", return_value=True),
            patch("os.listdir", return_value=mock_files),
            patch("os.path.isdir", return_value=False),
            patch("os.remove"),
            patch("shutil.copytree"),
            patch("shutil.copy2"),
            patch("os.makedirs"),
        ):
            # Verify update_container method exists and works
            assert hasattr(container_manager, "update_container")
            await container_manager.update_container(
                "test-container-id", "/test/code/path"
            )

            # In the update_container method, a new container is created and started
            # rather than restarting the original container
            mock_container.stop.assert_called_once()
            mock_container.remove.assert_called_once()

            # Verify the new container was started (since original was running)
            mock_new_container.start.assert_called_once()


class TestTask7Verification:
    """Tests for Task 7: Implement container status monitoring."""

    @pytest.mark.asyncio
    async def test_container_status_monitoring_implementation(
        self, container_manager, mock_container
    ):
        """Test that container status monitoring is implemented."""
        # Setup
        container_manager.docker_client.containers.get.return_value = mock_container

        with patch("os.path.exists", return_value=True):
            # Verify status monitoring methods exist
            assert hasattr(container_manager, "get_container_status")
            assert hasattr(container_manager, "list_containers")
            assert hasattr(container_manager, "start_monitoring")
            assert hasattr(container_manager, "stop_monitoring")

            # Test get_container_status
            status = await container_manager.get_container_status("test-container-id")
            assert status.id == "test-container-id"
            assert status.state == ContainerState.RUNNING


class TestTask8Verification:
    """Tests for Task 8: Create Socket.IO event handlers."""

    def test_socket_io_event_handler_implementation(
        self, mock_sio, container_manager, socket_handler, mock_logger, activity_logger
    ):
        """Test that SocketIOEventHandler is properly implemented."""
        handler = SocketIOEventHandler(
            sio=mock_sio,
            container_manager=container_manager,
            socket_handler=socket_handler,
            system_logger=mock_logger,
            user_logger=activity_logger,
        )

        # Verify event handler methods exist
        assert hasattr(handler, "handle_connect")
        assert hasattr(handler, "handle_disconnect")
        assert hasattr(handler, "handle_create_container")
        assert hasattr(handler, "handle_start_container")
        assert hasattr(handler, "handle_stop_container")
        assert hasattr(handler, "handle_restart_container")
        assert hasattr(handler, "handle_update_container")
        assert hasattr(handler, "handle_delete_container")
        assert hasattr(handler, "handle_send_message")
        assert hasattr(handler, "handle_get_status")
        assert hasattr(handler, "handle_list_containers")


class TestTask9Verification:
    """Tests for Task 9: Add comprehensive error handling."""

    @pytest.mark.asyncio
    async def test_error_handling_implementation(
        self, container_manager, mock_container
    ):
        """Test that error handling is properly implemented."""
        # Setup error condition
        container_manager.docker_client.containers.get.side_effect = Exception(
            "Test error"
        )

        # Verify error handling in container operations
        with pytest.raises(Exception):
            await container_manager.start_container("test-container-id")


class TestTask10Verification:
    """Tests for Task 10: Integrate all components in main application."""

    def test_main_application_integration(self):
        """Test that all components are integrated in the main application."""
        with patch("docker.from_env") as mock_docker:
            mock_docker.return_value = Mock()
            from main import app_instance

            # Verify all components are initialized
            assert app_instance.system_logger is not None
            assert app_instance.sio is not None
            assert app_instance.user_logger is not None
            assert app_instance.container_manager is not None
            assert app_instance.socket_handler is not None
            assert app_instance.event_handler is not None
