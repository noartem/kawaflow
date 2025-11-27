from unittest.mock import Mock, patch

from messaging import InMemoryMessaging
from main import FlowManagerApp
from rabbitmq_event_handler import RabbitMQEventHandler


def test_flow_manager_app_uses_pluggable_messaging(monkeypatch):
    monkeypatch.setenv("MESSAGING_BACKEND", "inmemory")
    with patch("docker.from_env") as mock_docker:
        mock_docker.return_value = Mock()
        app = FlowManagerApp(socket_dir="/tmp/test_sockets")

    assert isinstance(app.messaging, InMemoryMessaging)
    assert isinstance(app.event_handler, RabbitMQEventHandler)
    assert app.event_handler.messaging is app.messaging
