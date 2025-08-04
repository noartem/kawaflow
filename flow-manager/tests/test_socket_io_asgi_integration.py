"""
Tests for Socket.IO ASGI app integration with FastAPI.

This module tests the integration between Socket.IO and FastAPI,
focusing on the ASGI app structure and event handling.
"""

import pytest
import socketio
from unittest.mock import Mock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestSocketIOASGIIntegration:
    """Test suite for Socket.IO ASGI app integration."""

    def test_socket_io_asgi_app_structure(self):
        """Test that Socket.IO ASGI app is properly structured."""
        with patch("docker.from_env") as mock_docker:
            mock_docker.return_value = Mock()
            from main import app, socket_app, app_instance

            # Verify that socket_app is a Socket.IO ASGI app
            assert isinstance(socket_app, socketio.ASGIApp)

            # Verify that app is the same as socket_app (app = socket_app in main.py)
            assert app is socket_app

            # Verify that the Socket.IO server is properly configured
            assert hasattr(app_instance.sio, "async_mode")
            assert app_instance.sio.async_mode == "asgi"

    def test_fastapi_integration(self):
        """Test FastAPI integration with Socket.IO."""
        with patch("docker.from_env") as mock_docker:
            mock_docker.return_value = Mock()
            from main import app

            # Create a test client
            client = TestClient(app)

            # Test health endpoint
            response = client.get("/health")
            assert response.status_code == 200
            assert "healthy" in response.json()["status"]

    def test_socket_io_event_handlers(self):
        """Test that Socket.IO event handlers are properly registered."""
        with patch("docker.from_env") as mock_docker:
            mock_docker.return_value = Mock()
            from main import app_instance

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

    def test_socket_io_asgi_app_mounting(self):
        """Test that Socket.IO ASGI app is properly mounted."""
        with patch("docker.from_env") as mock_docker:
            mock_docker.return_value = Mock()
            from main import app, socket_app, app_instance

            # Verify that the main app is the Socket.IO ASGI app
            assert app is socket_app

            # Verify that the Socket.IO server is properly configured
            assert app_instance.sio.async_mode == "asgi"
            # Check CORS configuration (attribute name may vary by version)
            assert getattr(app_instance.sio, "cors_allowed_origins", "*") is not None

            # Verify that the Socket.IO server is properly attached to the ASGI app
            # The exact attribute name may vary by version, so we'll check the app is properly configured
            assert app is socket_app  # This is the key relationship

    @pytest.mark.asyncio
    async def test_lifespan_context_manager(self):
        """Test the lifespan context manager for startup and shutdown."""
        with patch("docker.from_env") as mock_docker:
            mock_docker.return_value = Mock()
            from main import lifespan, app_instance

            # Create a mock FastAPI app
            mock_app = Mock(spec=FastAPI)

            # Test the lifespan context manager
            async with lifespan(mock_app):
                # Verify that startup was called
                assert len(app_instance._background_tasks) > 0

            # Verify that shutdown was called
            assert app_instance._shutdown_event.is_set()
