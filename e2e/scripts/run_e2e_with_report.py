#!/usr/bin/env python3
import datetime as dt
import html
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from collections import deque
from typing import Protocol, cast

import httpx


class DockerContainers(Protocol):
    def list(self, *args: object, **kwargs: object) -> list: ...


class DockerClient(Protocol):
    containers: DockerContainers


REPORTS_DIR = Path("reports")
PROJECT_NAME = os.getenv("E2E_DOCKER_PROJECT", "kawaflow-e2e")
BASE_URL = os.getenv("E2E_BASE_URL", "http://ui-app.local:8000")
HEALTH_PATH = os.getenv("E2E_HEALTH_PATH", "/up")
HEALTH_TIMEOUT = int(os.getenv("E2E_HEALTH_TIMEOUT", "60"))
LOG_LINE_LIMIT = int(os.getenv("E2E_LOG_LINE_LIMIT", "5000"))
PYTEST_OUTPUT_LIMIT = int(os.getenv("E2E_PYTEST_OUTPUT_LIMIT", "200000"))
PYTEST_DISABLE_PLUGIN_AUTOLOAD = (
    os.getenv("E2E_PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1").strip() == "1"
)
TEST_RUN_ID = os.getenv("E2E_TEST_RUN_ID", "")
TEMPLATE_PATH = Path(__file__).with_name("report_template.html")


def get_docker_client() -> DockerClient | None:
    try:
        import docker
    except Exception as exc:  # pragma: no cover - defensive import
        sys.stderr.write(f"Docker SDK unavailable: {exc}\n")
        return None
    try:
        return cast(DockerClient, docker.from_env())
    except Exception as exc:
        sys.stderr.write(f"Docker SDK init failed: {exc}\n")
        return None


def project_name_candidates() -> list[str]:
    names: list[str] = []

    def add(name: str | None) -> None:
        if name and name not in names:
            names.append(name)

    add(PROJECT_NAME)
    add(os.getenv("COMPOSE_PROJECT_NAME"))

    for name in list(names):
        add(name.replace("-", "_"))
        add(name.replace("_", "-"))

    return names


def run_pytest() -> tuple[int, str]:
    env = os.environ.copy()
    if PYTEST_DISABLE_PLUGIN_AUTOLOAD:
        env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "no:terminal",
            "-p",
            "no:cacheprovider",
            "--assert=plain",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    output_lines: deque[str] = deque()
    output_size = 0
    truncated = False
    assert process.stdout is not None
    for line in process.stdout:
        sys.stdout.write(line)
        output_lines.append(line)
        output_size += len(line)
        while output_size > PYTEST_OUTPUT_LIMIT and output_lines:
            output_size -= len(output_lines.popleft())
            truncated = True
    process.wait()
    output = "".join(output_lines)
    if truncated:
        output = f"<pytest output truncated at {PYTEST_OUTPUT_LIMIT} chars>\n" + output
    return process.returncode, output


def cleanup_flow_containers() -> None:
    if not TEST_RUN_ID:
        return
    client = get_docker_client()
    if client is None:
        return
    containers = client.containers.list(
        all=True,
        filters={"label": f"kawaflow.test_run_id={TEST_RUN_ID}"},
    )
    for container in containers:
        try:
            container.reload()
            if container.status == "running":
                container.stop(timeout=5)
            container.remove(force=True)
        except Exception:
            continue


def wait_for_ui() -> None:
    deadline = time.time() + HEALTH_TIMEOUT
    url = f"{BASE_URL}{HEALTH_PATH}"
    last_error: str | None = None

    while time.time() < deadline:
        try:
            response = httpx.get(url, timeout=5.0)
            if response.status_code < 500:
                return
            last_error = f"status {response.status_code}"
        except Exception as exc:  # pragma: no cover - network readiness
            last_error = str(exc)
        time.sleep(2)

    raise RuntimeError(f"UI health check failed for {url}: {last_error}")


def collect_logs(since: int | None) -> tuple[list[dict[str, str]], list[str]]:
    client = get_docker_client()
    if client is None:
        return (
            [
                {
                    "service": "docker",
                    "timestamp": "",
                    "message": "<docker client unavailable>",
                }
            ],
            ["docker"],
        )
    containers: list = []
    for name in project_name_candidates():
        containers = client.containers.list(
            all=True,
            filters={"label": f"com.docker.compose.project={name}"},
        )
        if containers:
            break

    if not containers:
        containers = client.containers.list(all=True)

    containers.sort(key=lambda container: container.name or "")
    lines: list[dict[str, str]] = []
    services: list[str] = []
    total_lines = 0
    truncated = False
    for container in containers:
        service = container.labels.get("com.docker.compose.service", container.name)
        if service not in services:
            services.append(service)
        try:
            raw = container.logs(
                timestamps=True,
                stdout=True,
                stderr=True,
                since=since,
            )
        except Exception as exc:  # pragma: no cover - defensive for docker API errors
            lines.append(
                {
                    "service": service,
                    "timestamp": "",
                    "message": f"<failed to read logs: {exc}>",
                }
            )
            total_lines += 1
            if total_lines >= LOG_LINE_LIMIT:
                truncated = True
                break
            continue
        text = raw.decode("utf-8", errors="replace").strip()
        if not text:
            lines.append(
                {
                    "service": service,
                    "timestamp": "",
                    "message": "<no logs>",
                }
            )
            total_lines += 1
            if total_lines >= LOG_LINE_LIMIT:
                truncated = True
                break
            continue
        for line in text.splitlines():
            if total_lines >= LOG_LINE_LIMIT:
                truncated = True
                break
            if " " in line:
                timestamp, message = line.split(" ", 1)
            else:
                timestamp, message = "", line
            lines.append(
                {
                    "service": service,
                    "timestamp": timestamp,
                    "message": message,
                }
            )
            total_lines += 1
        if truncated:
            break
    if truncated:
        if "system" not in services:
            services.append("system")
        lines.append(
            {
                "service": "system",
                "timestamp": "",
                "message": f"<log output truncated at {LOG_LINE_LIMIT} lines>",
            }
        )
    return lines, services


def escape(text: str) -> str:
    return html.escape(text)


def load_report_template() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def build_report(
    pytest_output: str,
    log_lines: list[dict[str, str]],
    services: list[str],
    status: str,
    ts: str,
    duration: str,
) -> str:
    service_data = json.dumps(
        {
            "services": services,
            "lines": log_lines,
        },
        ensure_ascii=True,
    )

    # Prevent breaking out of the JSON <script> tag.
    safe_service_data = service_data.replace("<", "\\u003c")

    status_class = "ok" if status == "passed" else "fail"
    template = load_report_template()

    return (
        template.replace("__E2E_TS__", escape(ts))
        .replace("__E2E_STATUS__", escape(status))
        .replace("__E2E_STATUS_CLASS__", status_class)
        .replace("__E2E_DURATION__", escape(duration))
        .replace("__E2E_PYTEST_OUTPUT__", escape(pytest_output))
        .replace("__E2E_SERVICE_DATA__", safe_service_data)
    )


def main() -> int:
    start = dt.datetime.now()
    ts = start.strftime("%Y%m%d-%H%M%S")
    start_timestamp = int(start.timestamp())

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    cleanup_flow_containers()
    wait_for_ui()
    exit_code, pytest_output = run_pytest()
    log_lines, services = collect_logs(start_timestamp)

    duration = str(dt.datetime.now() - start).split(".")[0]
    status = "passed" if exit_code == 0 else f"failed ({exit_code})"
    report_html = build_report(pytest_output, log_lines, services, status, ts, duration)

    report_path = REPORTS_DIR / f"e2e-report-{ts}.html"
    report_path.write_text(report_html, encoding="utf-8")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
