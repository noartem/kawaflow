#!/usr/bin/env python3
import datetime as dt
import html
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import docker
import httpx


REPORTS_DIR = Path("reports")
PROJECT_NAME = os.getenv("E2E_DOCKER_PROJECT", "kawaflow-e2e")
BASE_URL = os.getenv("E2E_BASE_URL", "http://ui-app.local:8000")
HEALTH_PATH = os.getenv("E2E_HEALTH_PATH", "/up")
HEALTH_TIMEOUT = int(os.getenv("E2E_HEALTH_TIMEOUT", "60"))
TEST_RUN_ID = os.getenv("E2E_TEST_RUN_ID", "")
TEMPLATE_PATH = Path(__file__).with_name("report_template.html")


def run_pytest() -> tuple[int, str]:
    process = subprocess.Popen(
        [sys.executable, "-m", "pytest"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    output_lines: list[str] = []
    assert process.stdout is not None
    for line in process.stdout:
        sys.stdout.write(line)
        output_lines.append(line)
    process.wait()
    return process.returncode, "".join(output_lines)


def cleanup_flow_containers() -> None:
    if not TEST_RUN_ID:
        return
    client = docker.from_env()
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


def collect_logs() -> tuple[list[dict[str, str]], list[str]]:
    client = docker.from_env()
    containers = client.containers.list(
        all=True,
        filters={"label": f"com.docker.compose.project={PROJECT_NAME}"},
    )
    containers.sort(key=lambda container: container.name or "")
    lines: list[dict[str, str]] = []
    services: list[str] = []
    for container in containers:
        service = container.labels.get("com.docker.compose.service", container.name)
        if service not in services:
            services.append(service)
        try:
            raw = container.logs(timestamps=True, stdout=True, stderr=True)
        except Exception as exc:  # pragma: no cover - defensive for docker API errors
            lines.append(
                {
                    "service": service,
                    "timestamp": "",
                    "message": f"<failed to read logs: {exc}>",
                }
            )
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
            continue
        for line in text.splitlines():
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

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    cleanup_flow_containers()
    wait_for_ui()
    exit_code, pytest_output = run_pytest()
    log_lines, services = collect_logs()

    duration = str(dt.datetime.now() - start).split(".")[0]
    status = "passed" if exit_code == 0 else f"failed ({exit_code})"
    report_html = build_report(pytest_output, log_lines, services, status, ts, duration)

    report_path = REPORTS_DIR / f"e2e-report-{ts}.html"
    report_path.write_text(report_html, encoding="utf-8")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
