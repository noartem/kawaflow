import pytest
from unittest.mock import MagicMock, patch

from main import sio, start_container, stop_container


@pytest.mark.asyncio
@patch("main.docker")
async def test_start_container(mock_docker):
    mock_container = MagicMock()
    mock_container.id = "12345"
    mock_container.name = "test_container"
    mock_docker.from_env.return_value.containers.run.return_value = mock_container

    sid = "test_sid"
    data = {"image": "test_image"}

    with patch.object(sio, "emit") as mock_emit:
        await start_container(sid, data)
        mock_emit.assert_called_once_with(
            "container_started", {"id": "12345", "name": "test_container"}, to=sid
        )


@pytest.mark.asyncio
@patch("main.docker")
async def test_stop_container(mock_docker):
    mock_container = MagicMock()
    mock_container.id = "12345"
    mock_docker.from_env.return_value.containers.get.return_value = mock_container

    sid = "test_sid"
    data = {"container_id": "12345"}

    with patch.object(sio, "emit") as mock_emit:
        await stop_container(sid, data)
        mock_emit.assert_called_once_with("container_stopped", {"id": "12345"}, to=sid)
