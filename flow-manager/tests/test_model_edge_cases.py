"""
Tests for edge cases in data models.

This module tests edge cases and validation for data models,
particularly focusing on type conversions and validations.
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError
from models import (
    ContainerState,
    ContainerHealth,
    ContainerConfig,
    ContainerInfo,
    ContainerStatus,
)


def test_container_status_string_enum_conversion():
    """Test ContainerStatus model with string enum values."""
    # Test with string values that should be converted to enums
    status = ContainerStatus(
        id="test",
        state="running",  # String value should be converted to enum
        health="healthy",  # String value should be converted to enum
        socket_connected=True,
    )

    # Verify conversion worked
    assert isinstance(status.state, ContainerState)
    assert status.state == ContainerState.RUNNING
    assert isinstance(status.health, ContainerHealth)
    assert status.health == ContainerHealth.HEALTHY


def test_container_status_invalid_state():
    """Test ContainerStatus model with invalid state value."""
    # Test with invalid state value
    with pytest.raises(ValidationError) as exc_info:
        ContainerStatus(
            id="test",
            state="invalid_state",  # Invalid state value
            health=ContainerHealth.HEALTHY,
            socket_connected=True,
        )

    assert "Invalid container state" in str(exc_info.value)


def test_container_status_invalid_health():
    """Test ContainerStatus model with invalid health value."""
    # Test with invalid health value
    with pytest.raises(ValidationError) as exc_info:
        ContainerStatus(
            id="test",
            state=ContainerState.RUNNING,
            health="invalid_health",  # Invalid health value
            socket_connected=True,
        )

    assert "Invalid container health" in str(exc_info.value)


def test_container_info_datetime_validation():
    """Test ContainerInfo model with invalid datetime value."""
    # Test with invalid datetime value
    with pytest.raises(ValidationError) as exc_info:
        ContainerInfo(
            id="test",
            name="test",
            status="running",
            image="nginx",
            created="not-a-datetime",  # Invalid datetime value
            socket_path="/tmp/test.sock",
        )

    assert "Invalid datetime value" in str(exc_info.value)


def test_container_status_timedelta_validation():
    """Test ContainerStatus model with invalid timedelta value."""
    # Test with invalid timedelta value
    with pytest.raises(ValidationError) as exc_info:
        ContainerStatus(
            id="test",
            state=ContainerState.RUNNING,
            health=ContainerHealth.HEALTHY,
            uptime="not-a-timedelta",  # Invalid timedelta value
            socket_connected=True,
        )

    assert "Invalid timedelta value" in str(exc_info.value)


def test_container_info_valid_iso_datetime():
    """Test ContainerInfo model with valid ISO datetime string."""
    # Test with valid ISO datetime string
    info = ContainerInfo(
        id="test",
        name="test",
        status="running",
        image="nginx",
        created="2023-01-01T00:00:00",  # Valid ISO datetime string
        socket_path="/tmp/test.sock",
    )

    # Verify conversion worked
    assert isinstance(info.created, datetime)
    assert info.created.year == 2023
    assert info.created.month == 1
    assert info.created.day == 1
