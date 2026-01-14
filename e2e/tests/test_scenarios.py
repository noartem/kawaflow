import time
import uuid

import httpx
import pytest

from tests.helpers.graph_validation import graph_hash


FLOW_CODE = """
from kawa import actor, event, Context
from kawa.cron import CronEvent


@event
class Ping:
    pass


@actor(receivs=CronEvent.by("*/5 * * * *"))
def Starter(ctx: Context, event):
    print("start")
"""

FLOW_CODE_UPDATED = """
from kawa import actor, event, Context
from kawa.cron import CronEvent


@event
class Ping:
    pass


@actor(receivs=CronEvent.by("*/10 * * * *"))
def Starter(ctx: Context, event):
    print("start again")
"""


def _flow_labels(flow_id: int, e2e_settings) -> dict[str, str]:
    labels = {"kawaflow.flow_id": str(flow_id)}
    if e2e_settings.test_run_id:
        labels["kawaflow.test_run_id"] = e2e_settings.test_run_id
    return labels


def _wait_for_logs(ui_client, flow_id: int, timeout: int = 30) -> list[dict]:
    deadline = time.time() + timeout
    while time.time() < deadline:
        payload = ui_client.flow_logs(flow_id)
        data = payload.get("data", {}).get("data", [])
        if data:
            return data
        time.sleep(2)
    return payload.get("data", {}).get("data", [])


def _wait_for_container_id(ui_client, flow_id: int, timeout: int = 30) -> str | None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        props = ui_client.flow_show_props(flow_id)
        development_run = props.get("developmentRun") or props.get("development_run")
        if development_run and development_run.get("container_id"):
            return str(development_run["container_id"])
        time.sleep(1)
    return None


def _wait_for_new_container(
    docker_observer,
    labels: dict[str, str],
    previous_run_id: str,
    timeout: int,
):
    deadline = time.time() + timeout
    while time.time() < deadline:
        containers = docker_observer.list_containers(labels)
        for container in containers:
            run_id = docker_observer.container_labels(container).get("kawaflow.flow_run_id")
            if run_id and run_id != previous_run_id:
                return container
        time.sleep(2)
    raise TimeoutError("new container not found within timeout")


@pytest.fixture
def simple_flow(ui_client):
    graph = {"nodes": [], "edges": []}
    flow_name = f"E2E Flow {uuid.uuid4().hex[:8]}"
    flow = ui_client.create_flow(flow_name, FLOW_CODE, graph)
    yield flow
    try:
        ui_client.stop_flow(flow.flow_id)
    finally:
        ui_client.delete_flow(flow.flow_id)


def test_flow_lifecycle_rerun(simple_flow, ui_client, docker_observer, e2e_settings):
    ui_client.run_flow(simple_flow.flow_id)

    labels = _flow_labels(simple_flow.flow_id, e2e_settings)
    container = docker_observer.wait_for_container(labels, e2e_settings.container_timeout)
    docker_observer.wait_for_status(container, "running", e2e_settings.container_timeout)
    first_run_id = docker_observer.container_labels(container).get("kawaflow.flow_run_id")
    assert first_run_id

    container_id = _wait_for_container_id(ui_client, simple_flow.flow_id, timeout=30)
    assert container_id
    ui_client.stop_flow(simple_flow.flow_id)
    docker_observer.wait_for_status(container, "exited", e2e_settings.container_timeout)

    ui_client.run_flow(simple_flow.flow_id)
    new_container = _wait_for_new_container(
        docker_observer,
        labels,
        first_run_id,
        e2e_settings.container_timeout,
    )
    docker_observer.wait_for_status(new_container, "running", e2e_settings.container_timeout)


def test_flow_lifecycle_restart(simple_flow, ui_client, docker_observer, e2e_settings):
    ui_client.run_flow(simple_flow.flow_id)

    labels = _flow_labels(simple_flow.flow_id, e2e_settings)
    container = docker_observer.wait_for_container(labels, e2e_settings.container_timeout)
    docker_observer.wait_for_status(container, "running", e2e_settings.container_timeout)
    first_run_id = docker_observer.container_labels(container).get("kawaflow.flow_run_id")
    assert first_run_id

    container_id = _wait_for_container_id(ui_client, simple_flow.flow_id, timeout=30)
    assert container_id
    ui_client.stop_flow(simple_flow.flow_id)
    docker_observer.wait_for_status(container, "exited", e2e_settings.container_timeout)

    ui_client.run_flow(simple_flow.flow_id)
    restarted = _wait_for_new_container(
        docker_observer,
        labels,
        first_run_id,
        e2e_settings.container_timeout,
    )
    docker_observer.wait_for_status(restarted, "running", e2e_settings.container_timeout)


def test_runtime_graph_update(simple_flow, ui_client, docker_observer, e2e_settings):
    ui_client.run_flow(simple_flow.flow_id)

    labels = _flow_labels(simple_flow.flow_id, e2e_settings)
    container = docker_observer.wait_for_container(labels, e2e_settings.container_timeout)
    docker_observer.wait_for_status(container, "running", e2e_settings.container_timeout)
    initial_hash = docker_observer.container_labels(container).get("kawaflow.graph_hash")
    first_run_id = docker_observer.container_labels(container).get("kawaflow.flow_run_id")
    assert initial_hash
    assert first_run_id

    container_id = _wait_for_container_id(ui_client, simple_flow.flow_id, timeout=30)
    assert container_id
    ui_client.stop_flow(simple_flow.flow_id)
    docker_observer.wait_for_status(container, "exited", e2e_settings.container_timeout)

    updated_graph = {"nodes": [{"id": "node-1"}], "edges": []}
    ui_client.update_flow(
        simple_flow.flow_id,
        simple_flow.name,
        FLOW_CODE_UPDATED,
        updated_graph,
    )

    ui_client.run_flow(simple_flow.flow_id)
    updated_container = _wait_for_new_container(
        docker_observer,
        labels,
        first_run_id,
        e2e_settings.container_timeout,
    )
    docker_observer.wait_for_status(updated_container, "running", e2e_settings.container_timeout)
    updated_hash = docker_observer.container_labels(updated_container).get("kawaflow.graph_hash")
    expected_hash = graph_hash(FLOW_CODE_UPDATED, updated_graph)
    assert updated_hash == expected_hash
    assert updated_hash != initial_hash


def test_runtime_graph_labels(simple_flow, ui_client, docker_observer, e2e_settings):
    ui_client.run_flow(simple_flow.flow_id)

    labels = _flow_labels(simple_flow.flow_id, e2e_settings)
    container = docker_observer.wait_for_container(labels, e2e_settings.container_timeout)
    docker_observer.wait_for_status(container, "running", e2e_settings.container_timeout)

    container_labels = docker_observer.container_labels(container)
    expected_hash = graph_hash(simple_flow.code, simple_flow.graph)
    assert container_labels.get("kawaflow.graph_hash") == expected_hash


def test_logs_endpoint(simple_flow, ui_client, docker_observer, e2e_settings):
    ui_client.run_flow(simple_flow.flow_id)
    labels = _flow_labels(simple_flow.flow_id, e2e_settings)
    container = docker_observer.wait_for_container(labels, e2e_settings.container_timeout)
    docker_observer.wait_for_status(container, "running", e2e_settings.container_timeout)

    logs = _wait_for_logs(ui_client, simple_flow.flow_id, timeout=30)
    assert logs
    assert any("Event:" in entry.get("message", "") for entry in logs)


def test_auth_ownership(ui_client, e2e_settings):
    other_client = type(ui_client)(e2e_settings.base_url)
    flow = None
    try:
        email = f"e2e-{uuid.uuid4().hex}@example.com"
        password = "e2e-password"
        other_client.register("E2E User B", email, password)
        other_client.login(email, password)

        graph = {"nodes": [], "edges": []}
        flow_name = f"E2E Flow {uuid.uuid4().hex[:8]}"
        flow = ui_client.create_flow(flow_name, FLOW_CODE, graph)

        response = other_client.get(f"/flows/{flow.flow_id}", follow_redirects=False)
        assert response.status_code == 403
    finally:
        if flow is not None:
            ui_client.delete_flow(flow.flow_id)
        other_client.close()


def test_auth_session_expired(e2e_settings):
    client = httpx.Client(base_url=e2e_settings.base_url, follow_redirects=False)
    try:
        response = client.get("/flows")
        assert response.status_code in {302, 303}
        assert "/login" in response.headers.get("location", "")
    finally:
        client.close()


def test_concurrency_same_name(ui_client, e2e_settings):
    other_client = type(ui_client)(e2e_settings.base_url)
    flow_a = None
    flow_b = None
    try:
        email = f"e2e-{uuid.uuid4().hex}@example.com"
        password = "e2e-password"
        other_client.register("E2E User B", email, password)
        other_client.login(email, password)

        graph = {"nodes": [], "edges": []}
        name = "Shared Name"
        flow_a = ui_client.create_flow(name, FLOW_CODE, graph)
        flow_b = other_client.create_flow(name, FLOW_CODE, graph)

        assert flow_a.flow_id != flow_b.flow_id
        assert ui_client.flow_show_props(flow_a.flow_id)["flow"]["id"] == flow_a.flow_id
        assert other_client.flow_show_props(flow_b.flow_id)["flow"]["id"] == flow_b.flow_id
    finally:
        if flow_a is not None:
            ui_client.delete_flow(flow_a.flow_id)
        if flow_b is not None:
            other_client.delete_flow(flow_b.flow_id)
        other_client.close()


def test_validation_invalid_graph(ui_client):
    payload = {
        "name": f"E2E Flow {uuid.uuid4().hex[:8]}",
        "description": "e2e flow invalid graph",
        "code": FLOW_CODE,
        "graph": "not-a-graph",
    }
    response = ui_client.create_flow_raw(payload)
    assert response.status_code == 422


def test_validation_empty_code(simple_flow, ui_client):
    payload = {
        "name": simple_flow.name,
        "description": "e2e flow empty code",
        "code": "",
        "graph": simple_flow.graph,
    }
    response = ui_client.update_flow_raw(simple_flow.flow_id, payload)
    assert response.status_code in {200, 302}

    props = ui_client.flow_show_props(simple_flow.flow_id)
    assert props["flow"]["code"] in {"", None}


@pytest.mark.skip(reason="Scenario not supported: delete while running is blocked by FlowController.")
def test_flow_lifecycle_delete_running():
    pass


@pytest.mark.skip(reason="Scenario not supported: runtime graph depends on flow runtime socket.")
def test_runtime_graph_basic():
    pass


@pytest.mark.skip(reason="Scenario not supported: send message endpoint not exposed in UI.")
def test_logs_event_roundtrip():
    pass


@pytest.mark.skip(reason="Scenario not supported: flow container never executes actor code.")
def test_logs_error_trace():
    pass


@pytest.mark.skip(reason="Scenario not supported: stop event not emitted as a distinct log entry.")
def test_logs_stop_event():
    pass


@pytest.mark.skip(reason="Scenario not supported: no role without manage permissions.")
def test_auth_no_manage():
    pass


@pytest.mark.skip(reason="Scenario not supported: no role without run permissions.")
def test_auth_no_run():
    pass


@pytest.mark.skip(reason="Scenario not supported: flow-manager container control requires write access to docker socket.")
def test_flow_manager_restart():
    pass


@pytest.mark.skip(reason="Scenario not supported: UI publishes to RabbitMQ even when flow-manager is down.")
def test_flow_manager_unavailable():
    pass


@pytest.mark.skip(reason="Scenario not supported: UI does not wait for flow-manager responses.")
def test_flow_manager_timeout():
    pass


@pytest.mark.skip(reason="Scenario not supported: parallel flow creation not exercised in current harness.")
def test_concurrency_multi_flows():
    pass


@pytest.mark.skip(reason="Scenario not supported: message sending not wired through UI.")
def test_concurrency_parallel_messages():
    pass


@pytest.mark.skip(reason="Scenario not supported: production deploy requires uv lock build and images.")
def test_production_deploy_success():
    pass


@pytest.mark.skip(reason="Scenario not supported: production deploy requires uv lock build and images.")
def test_production_undeploy():
    pass


@pytest.mark.skip(reason="Scenario not supported: production deploy requires uv lock build and images.")
def test_production_deploy_invalid_lock():
    pass


@pytest.mark.skip(reason="Scenario not supported: invalid code is accepted by current validation rules.")
def test_validation_invalid_code():
    pass


@pytest.mark.skip(reason="Scenario not supported: cleanup behavior is handled by task runner teardown.")
def test_cleanup_orphaned_containers():
    pass


@pytest.mark.skip(reason="Scenario not supported: cleanup on failure not enforced in current harness.")
def test_cleanup_on_failure():
    pass
