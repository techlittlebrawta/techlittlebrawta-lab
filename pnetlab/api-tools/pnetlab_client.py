"""Small, defensive client for the PNETLab session API.

The endpoints used here are based on the PNETLab 6 web interface and may change
between releases.  Callers should handle :class:`PNetLabError` and test against
their own PNETLab version before using a mutating operation.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Union
from urllib.parse import unquote, urljoin, urlparse

import requests


VerifyValue = Union[bool, str]


class PNetLabError(RuntimeError):
    """Raised when PNETLab rejects a request or returns unexpected data."""


class PNetLabClient:
    """Authenticated PNETLab API client with TLS verification and timeouts."""

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        *,
        verify: VerifyValue = True,
        timeout: float = 30.0,
        session: Optional[requests.Session] = None,
    ) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("base_url must be an absolute HTTP or HTTPS URL")
        if not username:
            raise ValueError("username is required")
        if not password:
            raise ValueError("password is required")
        if timeout <= 0:
            raise ValueError("timeout must be greater than zero")

        self.base_url = base_url.rstrip("/") + "/"
        self.username = username
        self._password = password
        self.verify = verify
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": "techlittlebrawta-pnetlab-api-tools/1.0",
            }
        )
        self._authenticated = False

    def _url(self, path: str) -> str:
        return urljoin(self.base_url, path.lstrip("/"))

    def _request(
        self,
        method: str,
        path: str,
        *,
        expected: Sequence[int] = (200,),
        **kwargs: Any,
    ) -> requests.Response:
        kwargs.setdefault("timeout", self.timeout)
        kwargs.setdefault("verify", self.verify)
        try:
            response = self.session.request(method, self._url(path), **kwargs)
        except requests.RequestException as exc:
            raise PNetLabError(f"{method.upper()} {path} failed: {exc}") from exc

        if response.status_code not in expected:
            excerpt = " ".join(response.text.split())[:300]
            raise PNetLabError(
                f"{method.upper()} {path} returned HTTP {response.status_code}"
                + (f": {excerpt}" if excerpt else "")
            )
        return response

    @staticmethod
    def _json(response: requests.Response, description: str) -> Mapping[str, Any]:
        try:
            payload = response.json()
        except ValueError as exc:
            raise PNetLabError(f"{description} did not return valid JSON") from exc
        if not isinstance(payload, Mapping):
            raise PNetLabError(f"{description} returned an unexpected JSON structure")
        return payload

    def _require_authentication(self) -> None:
        if not self._authenticated:
            raise PNetLabError("authenticate() must succeed before using the API")

    def authenticate(self) -> None:
        """Create a PNETLab web session without logging credentials."""

        self._request("GET", "/", expected=(200,))
        token = unquote(self.session.cookies.get("XSRF-TOKEN", ""))
        if not token:
            raise PNetLabError("PNETLab did not issue an XSRF token")

        self.session.headers.update({"X-XSRF-TOKEN": token})
        self._request(
            "POST",
            "/store/public/auth/login/login",
            expected=(200, 202),
            json={
                "username": self.username,
                "password": self._password,
                "html": "0",
                "captcha": "",
            },
        )
        self._password = ""
        self._authenticated = True

    def sign_out(self) -> None:
        """End the web session. Failure is intentionally non-fatal."""

        if not self._authenticated:
            return
        try:
            self._request("GET", "/api/auth/logout", expected=(200, 204))
        except PNetLabError:
            pass
        finally:
            self._authenticated = False
            self.session.close()

    def list_nodes(self) -> List[Dict[str, Any]]:
        self._require_authentication()
        response = self._request("GET", "/api/labs/session/topology")
        payload = self._json(response, "node topology")
        nodes = payload.get("data", {}).get("nodes", {})
        if not isinstance(nodes, Mapping):
            raise PNetLabError("node topology does not contain a node mapping")
        return [dict(node) for node in nodes.values() if isinstance(node, Mapping)]

    def get_node_statuses(self) -> Dict[str, int]:
        self._require_authentication()
        response = self._request("POST", "/api/labs/session/nodestatus")
        payload = self._json(response, "node status")
        statuses = payload.get("data", {})
        if not isinstance(statuses, Mapping):
            raise PNetLabError("node status does not contain a status mapping")

        normalized: Dict[str, int] = {}
        for node_id, status in statuses.items():
            try:
                normalized[str(node_id)] = int(status)
            except (TypeError, ValueError) as exc:
                raise PNetLabError(f"invalid status for node {node_id!r}: {status!r}") from exc
        return normalized

    def _node_action(self, action: str, node_id: Union[str, int]) -> None:
        self._require_authentication()
        if action not in {"start", "stop", "wipe"}:
            raise ValueError(f"unsupported node action: {action}")
        self._request(
            "POST",
            f"/api/labs/session/nodes/{action}",
            expected=(200, 201),
            json={"id": str(node_id)},
        )

    def start_node(self, node_id: Union[str, int]) -> None:
        self._node_action("start", node_id)

    def stop_node(self, node_id: Union[str, int]) -> None:
        self._node_action("stop", node_id)

    def wipe_node(self, node_id: Union[str, int]) -> None:
        self._node_action("wipe", node_id)

    def list_templates(self) -> List[Dict[str, str]]:
        self._require_authentication()
        response = self._request("GET", "/api/list/templates/")
        payload = self._json(response, "template list")
        raw_templates = payload.get("data", {})
        templates: List[Dict[str, str]] = []

        if isinstance(raw_templates, Mapping):
            iterator: Iterable[Any] = raw_templates.items()
            for template_id, item in iterator:
                if isinstance(item, Mapping):
                    name = str(item.get("name") or item.get("template") or template_id)
                    normalized_id = str(item.get("id") or template_id)
                else:
                    name = str(item)
                    normalized_id = str(template_id)
                if ".missing" not in name:
                    templates.append({"id": normalized_id, "name": name})
        elif isinstance(raw_templates, list):
            for item in raw_templates:
                if not isinstance(item, Mapping):
                    continue
                name = str(item.get("name") or item.get("template") or item.get("id") or "")
                template_id = str(item.get("id") or item.get("template") or "")
                if template_id and ".missing" not in name:
                    templates.append({"id": template_id, "name": name})
        else:
            raise PNetLabError("template list has an unexpected data structure")

        return sorted(templates, key=lambda item: (item["name"].lower(), item["id"]))

    def get_template_payload(self, template_id: str) -> Dict[str, Any]:
        self._require_authentication()
        if not template_id:
            raise ValueError("template_id is required")
        response = self._request("GET", f"/api/list/templates/{template_id}")
        payload = self._json(response, "template details")
        options = payload.get("data", {}).get("options", {})
        if not isinstance(options, Mapping):
            raise PNetLabError("template details do not contain an options mapping")

        result: Dict[str, Any] = {}
        for key, item in options.items():
            if isinstance(item, Mapping) and "value" in item:
                result[str(key)] = item["value"]
        result.setdefault("template", template_id)
        return result

    def add_node(self, payload: Mapping[str, Any]) -> None:
        self._require_authentication()
        prepared = deepcopy(dict(payload))
        if not prepared.get("name"):
            raise ValueError("node payload requires a name")
        if not prepared.get("template"):
            raise ValueError("node payload requires a template")
        self._request(
            "POST",
            "/api/labs/session/nodes/add",
            expected=(200, 201),
            json=prepared,
        )
