#!/usr/bin/env python3
"""
Tests for UserActivityLogger demo functionality.

This module tests the demo functionality of the UserActivityLogger
to ensure it correctly emits activity_log events to Socket.IO clients.
"""

import pytest
import socketio

from user_activity_logger import UserActivityLogger


@pytest.mark.asyncio
async def test_user_activity_logger_demo():
    """Test the UserActivityLogger demo functionality."""
    # Create a Socket.IO server
    sio = socketio.AsyncServer(async_mode="asgi")

    # Create the UserActivityLogger
    activity_logger = UserActivityLogger(sio)

    # Create a list to capture emitted events
    emitted_events = []

    # Store the original emit method
    original_emit = sio.emit

    # Define a wrapper function that captures events and calls the original
    async def emit_wrapper(event_name, data, *args, **kwargs):
        emitted_events.append({"event": event_name, "data": data})
        return await original_emit(event_name, data, *args, **kwargs)

    # Monkey patch the emit method
    setattr(sio, "emit", emit_wrapper)

    # Demo container lifecycle events
    await activity_logger.log_container_created(
        "container_123", "my-app", "nginx:latest"
    )
    await activity_logger.log_container_started("container_123", "my-app")
    await activity_logger.log_container_stopped("container_123", "my-app")
    await activity_logger.log_container_deleted("container_123", "my-app")

    # Demo message logging
    message_data = {"command": "status", "params": {"verbose": True}}
    await activity_logger.log_container_message("container_123", message_data, "sent")

    response_data = {"status": "running", "uptime": "2h 30m"}
    await activity_logger.log_container_message(
        "container_123", response_data, "received"
    )

    # Demo sensitive data filtering
    sensitive_message = {
        "type": "auth",
        "credentials": {
            "username": "admin",
            "password": "secret123",
            "api_key": "abc123xyz",
        },
        "config": {"database": {"host": "localhost", "password": "dbpass"}},
    }
    await activity_logger.log_container_message(
        "container_123", sensitive_message, "received"
    )

    # Demo actor events
    await activity_logger.log_actor_event(
        "container_123",
        "EmailActor",
        "email_sent",
        {"recipient": "user@example.com", "subject": "Workflow Complete"},
    )

    # Demo error logging
    await activity_logger.log_container_error(
        "container_123", "Connection timeout", "start_container"
    )

    # Verify events were emitted
    assert len(emitted_events) > 0

    # Verify all events are of type 'activity_log'
    for event in emitted_events:
        assert event["event"] == "activity_log"
        assert "timestamp" in event["data"]
        assert "message" in event["data"]
        assert "container_id" in event["data"]

    # Verify auth message was emitted
    auth_message_event = None
    for event in emitted_events:
        if "auth" in str(event["data"]):
            auth_message_event = event
            break

    assert auth_message_event is not None
