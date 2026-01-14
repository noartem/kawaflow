from __future__ import annotations

import re
from urllib.parse import unquote
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx


@dataclass
class FlowInfo:
    flow_id: int
    name: str
    code: str
    graph: Dict[str, Any]


class UIClient:
    def __init__(self, base_url: str) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            follow_redirects=True,
            timeout=httpx.Timeout(15.0),
        )

    def close(self) -> None:
        self._client.close()

    def _get_csrf(self, path: str = "/") -> str:
        response = self._client.get(path)
        response.raise_for_status()
        match = re.search(r'name="csrf-token" content="([^"]+)"', response.text)
        if match:
            return match.group(1)

        cookie_token = self._client.cookies.get("XSRF-TOKEN")
        if cookie_token:
            return unquote(cookie_token)

        self._client.get("/sanctum/csrf-cookie")
        cookie_token = self._client.cookies.get("XSRF-TOKEN")
        if cookie_token:
            return unquote(cookie_token)

        raise RuntimeError("Unable to find CSRF token")

    def _csrf_headers(self, token: str) -> Dict[str, str]:
        return {
            "X-CSRF-TOKEN": token,
            "X-XSRF-TOKEN": token,
            "X-Requested-With": "XMLHttpRequest",
        }

    def register(self, name: str, email: str, password: str) -> None:
        token = self._get_csrf("/register")
        payload = {
            "name": name,
            "email": email,
            "password": password,
            "password_confirmation": password,
        }
        response = self._client.post(
            "/register",
            data=payload,
            headers=self._csrf_headers(token),
        )
        response.raise_for_status()

    def login(self, email: str, password: str) -> None:
        token = self._get_csrf("/login")
        payload = {
            "email": email,
            "password": password,
        }
        response = self._client.post(
            "/login",
            data=payload,
            headers=self._csrf_headers(token),
        )
        response.raise_for_status()

    def create_flow(self, name: str, code: str, graph: Dict[str, Any]) -> FlowInfo:
        token = self._get_csrf("/flows/create")
        payload = {
            "name": name,
            "description": "e2e flow",
            "code": code,
            "graph": graph,
        }
        response = self._client.post(
            "/flows",
            json=payload,
            headers=self._csrf_headers(token),
        )
        response.raise_for_status()

        flow_id = self._extract_flow_id(str(response.url))
        return FlowInfo(flow_id=flow_id, name=name, code=code, graph=graph)

    def create_flow_raw(self, payload: Dict[str, Any]) -> httpx.Response:
        token = self._get_csrf("/flows/create")
        response = self._client.post(
            "/flows",
            json=payload,
            headers=self._csrf_headers(token),
        )
        return response

    def update_flow(self, flow_id: int, name: str, code: str, graph: Dict[str, Any]) -> None:
        token = self._get_csrf(f"/flows/{flow_id}")
        payload = {
            "name": name,
            "description": "e2e flow update",
            "code": code,
            "graph": graph,
        }
        response = self._client.put(
            f"/flows/{flow_id}",
            json=payload,
            headers=self._csrf_headers(token),
        )
        response.raise_for_status()

    def update_flow_raw(self, flow_id: int, payload: Dict[str, Any]) -> httpx.Response:
        token = self._get_csrf(f"/flows/{flow_id}")
        response = self._client.put(
            f"/flows/{flow_id}",
            json=payload,
            headers=self._csrf_headers(token),
        )
        return response

    def run_flow(self, flow_id: int) -> None:
        token = self._get_csrf(f"/flows/{flow_id}")
        response = self._client.post(
            f"/flows/{flow_id}/run",
            data={},
            headers=self._csrf_headers(token),
        )
        response.raise_for_status()

    def stop_flow(self, flow_id: int) -> None:
        token = self._get_csrf(f"/flows/{flow_id}")
        response = self._client.post(
            f"/flows/{flow_id}/stop",
            data={},
            headers=self._csrf_headers(token),
        )
        response.raise_for_status()

    def delete_flow(self, flow_id: int) -> None:
        token = self._get_csrf(f"/flows/{flow_id}")
        response = self._client.post(
            f"/flows/{flow_id}",
            data={"_method": "DELETE"},
            headers=self._csrf_headers(token),
        )
        response.raise_for_status()

    def flow_logs(self, flow_id: int) -> Dict[str, Any]:
        response = self._client.get(f"/flows/{flow_id}/logs")
        response.raise_for_status()
        return response.json()

    def flow_show_props(self, flow_id: int) -> Dict[str, Any]:
        response = self._client.get(
            f"/flows/{flow_id}",
            headers={
                "X-Inertia": "true",
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("props", {})

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._client.get(path, **kwargs)

    @staticmethod
    def _extract_flow_id(url: str) -> int:
        match = re.search(r"/flows/(\d+)", url)
        if not match:
            raise RuntimeError(f"Unable to extract flow id from {url}")
        return int(match.group(1))


class FlowManagerApi:
    def __init__(self, base_url: str) -> None:
        self._client = httpx.Client(base_url=base_url, follow_redirects=True)

    def close(self) -> None:
        self._client.close()

    def container_graph(self, container_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = self._client.get(
                f"/containers/{container_id}/graph",
                timeout=httpx.Timeout(5.0),
            )
        except httpx.RequestError:
            return None
        if response.status_code != 200:
            return None
        payload = response.json()
        return payload.get("graph")
