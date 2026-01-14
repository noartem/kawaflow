import uuid
import pytest

from tests.fixtures.clients import FlowManagerApi, UIClient
from tests.helpers.config import settings
from tests.helpers.docker_observer import DockerObserver


@pytest.fixture(scope="session")
def e2e_settings():
    return settings


@pytest.fixture(scope="session")
def ui_client(e2e_settings):
    client = UIClient(e2e_settings.base_url)
    email = f"e2e-{uuid.uuid4().hex}@example.com"
    password = "e2e-password"
    client.register("E2E User", email, password)
    client.login(email, password)
    yield client
    client.close()


@pytest.fixture(scope="session")
def flow_manager_api(e2e_settings):
    api = FlowManagerApi(e2e_settings.flow_manager_url)
    yield api
    api.close()


@pytest.fixture(scope="session")
def docker_observer():
    return DockerObserver()
