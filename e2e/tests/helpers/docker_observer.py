from __future__ import annotations

import time
from typing import Dict, Optional

import docker
from docker.models.containers import Container
from tenacity import RetryError, retry, stop_after_delay, wait_fixed


class DockerObserver:
    def __init__(self) -> None:
        self._client = docker.from_env()

    def find_container(self, labels: Dict[str, str]) -> Optional[Container]:
        filters = {"label": [f"{key}={value}" for key, value in labels.items()]}
        containers = self._client.containers.list(all=True, filters=filters)
        if not containers:
            return None

        def sort_key(container: Container) -> tuple[int, str]:
            run_id = container.labels.get("kawaflow.flow_run_id")
            run_id_value = int(run_id) if run_id and run_id.isdigit() else -1
            created = ""
            try:
                created = container.attrs.get("Created", "")
            except Exception:
                container.reload()
                created = container.attrs.get("Created", "")
            return (run_id_value, created)

        return max(containers, key=sort_key)

    def list_containers(self, labels: Dict[str, str]) -> list[Container]:
        filters = {"label": [f"{key}={value}" for key, value in labels.items()]}
        return self._client.containers.list(all=True, filters=filters)

    def wait_for_container(self, labels: Dict[str, str], timeout: int) -> Container:
        @retry(stop=stop_after_delay(timeout), wait=wait_fixed(2))
        def _lookup() -> Container:
            container = self.find_container(labels)
            if not container:
                raise RuntimeError("container not found")
            return container

        try:
            return _lookup()
        except RetryError as exc:
            raise TimeoutError("container not found within timeout") from exc

    def container_status(self, container: Container) -> str:
        container.reload()
        return container.status

    def container_labels(self, container: Container) -> Dict[str, str]:
        container.reload()
        return container.attrs.get("Config", {}).get("Labels", {}) or {}

    def container_logs(self, container: Container, tail: int = 200) -> str:
        raw = container.logs(tail=tail)
        return raw.decode("utf-8", errors="replace")

    def wait_for_status(self, container: Container, status: str, timeout: int) -> None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.container_status(container) == status:
                return
            time.sleep(2)
        raise TimeoutError(f"container did not reach status '{status}'")
