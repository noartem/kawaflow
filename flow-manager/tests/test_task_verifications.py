"""
Lightweight verification of core components after RabbitMQ migration.
"""

from unittest.mock import Mock, patch


from container_manager import ContainerManager
from messaging import InMemoryMessaging
from rabbitmq_event_handler import RabbitMQEventHandler
from socket_communication_handler import SocketCommunicationHandler
from system_logger import SystemLogger
from user_activity_logger import UserActivityLogger
from models import ContainerState, ContainerHealth, ContainerConfig


class TestTaskVerification:
    def test_data_models_exist(self):
        config = ContainerConfig(image="test:latest")
        assert config.image == "test:latest"
        assert hasattr(ContainerState, "RUNNING")
        assert hasattr(ContainerHealth, "HEALTHY")

    def test_system_logger_methods(self):
        logger = SystemLogger("test_logger")
        assert hasattr(logger, "log_container_operation")
        assert hasattr(logger, "log_error")
        assert hasattr(logger, "log_debug")

    def test_user_activity_logger_methods(self):
        logger = UserActivityLogger(InMemoryMessaging())
        assert hasattr(logger, "container_created")
        assert hasattr(logger, "log_container_message")
        assert hasattr(logger, "log_container_error")

    def test_container_manager_methods(self):
        with patch("docker.from_env"):
            manager = ContainerManager()
            assert hasattr(manager, "create_container")
            assert hasattr(manager, "start_container")
            assert hasattr(manager, "stop_container")
            assert hasattr(manager, "restart_container")
            assert hasattr(manager, "delete_container")

    def test_socket_communication_handler_methods(self, tmp_path):
        handler = SocketCommunicationHandler(socket_dir=str(tmp_path), logger=Mock())
        assert hasattr(handler, "setup_socket")
        assert hasattr(handler, "cleanup_socket")
        assert hasattr(handler, "send_message")
        assert hasattr(handler, "receive_message")

    def test_rabbitmq_event_handler_methods(self):
        handler = RabbitMQEventHandler(
            messaging=InMemoryMessaging(),
            container_manager=Mock(spec=ContainerManager),
            socket_handler=Mock(spec=SocketCommunicationHandler),
            system_logger=Mock(spec=SystemLogger),
            user_logger=Mock(spec=UserActivityLogger),
        )
        assert hasattr(handler, "handle_create_container")
        assert hasattr(handler, "handle_send_message")
