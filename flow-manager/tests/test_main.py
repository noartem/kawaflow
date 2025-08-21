import os
import shutil
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app

# --- Fixtures ---


@pytest.fixture
def client():
    """Provides a FastAPI TestClient, ensuring the app's flow_manager is mocked."""
    with patch("main.docker.from_env") as mock_from_env:
        mock_from_env.return_value = MagicMock()
        with TestClient(app) as c:
            # Make the mock accessible to tests
            c.app.state.flow_manager.docker_client = mock_from_env.return_value
            yield c


@pytest.fixture(autouse=True)
def setup_teardown():
    """Clean up flow directories before and after tests."""
    base_dir = "/tmp/kawaflow"
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    os.makedirs(base_dir)
    # Create the template file for the tests
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    os.makedirs(template_dir, exist_ok=True)
    with open(os.path.join(template_dir, "main.py.template"), "w") as f:
        f.write("{{ FILE }}")
    yield
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)


# --- Integration Tests ---


def test_websocket_full_lifecycle(client):
    """Integration test for the WebSocket endpoint, covering the full lifecycle."""
    flow_id = "ws-integ-flow"
    script = """from kawa import Actor

@Actor
def my_actor():
    pass"""

    flow_manager = client.app.state.flow_manager
    mock_container = MagicMock()
    mock_container.id = "ws_container_id"
    flow_manager.docker_client.containers.run.return_value = mock_container

    with client.websocket_connect("/ws") as websocket:
        # 1. Create
        websocket.send_json(
            {"action": "create", "payload": {"flow_id": flow_id, "script": script}}
        )
        response = websocket.receive_json()
        assert response["status"] == "created"
        assert flow_id in flow_manager.active_flows

        # 2. Send Command (mocking the socket part)
        socket_path = os.path.join("/tmp/kawaflow", flow_id, "flow.sock")
        os.makedirs(os.path.dirname(socket_path), exist_ok=True)
        with open(socket_path, "w") as f:
            f.write("")

        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_reader.read.return_value = json.dumps({"actors": ["my_actor"]}).encode()

        with patch(
            "main.asyncio.open_unix_connection",
            new=AsyncMock(return_value=(mock_reader, mock_writer)),
        ):
            websocket.send_json(
                {
                    "action": "send_command",
                    "payload": {"flow_id": flow_id, "command": "dump"},
                }
            )
            response = websocket.receive_json()
            assert response["actors"] == ["my_actor"]

        # 3. Stop
        websocket.send_json({"action": "stop", "payload": {"flow_id": flow_id}})
        response = websocket.receive_json()
        assert response["status"] == "stopped"
        assert flow_id not in flow_manager.active_flows
