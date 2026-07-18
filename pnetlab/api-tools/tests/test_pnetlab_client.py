import json
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pnetlab_client import PNetLabClient, PNetLabError


class FakeResponse:
    def __init__(self, status_code: int, payload: Optional[Dict[str, Any]] = None) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = "" if payload is None else json.dumps(payload)

    def json(self) -> Dict[str, Any]:
        if self._payload is None:
            raise ValueError("not JSON")
        return self._payload


class FakeSession:
    def __init__(self, responses: List[FakeResponse]) -> None:
        self.responses = responses
        self.headers: Dict[str, str] = {}
        self.cookies = requests.cookies.RequestsCookieJar()
        self.cookies.set("XSRF-TOKEN", "test-token")
        self.calls: List[Dict[str, Any]] = []
        self.closed = False

    def request(self, method: str, url: str, **kwargs: Any) -> FakeResponse:
        self.calls.append({"method": method, "url": url, **kwargs})
        return self.responses.pop(0)

    def close(self) -> None:
        self.closed = True


class PNetLabClientTests(unittest.TestCase):
    def test_authentication_and_node_listing_use_timeout_and_tls(self) -> None:
        session = FakeSession(
            [
                FakeResponse(200),
                FakeResponse(202),
                FakeResponse(
                    200,
                    {"data": {"nodes": {"1": {"id": 1, "name": "r1", "url": "/r1"}}}},
                ),
            ]
        )
        client = PNetLabClient(
            "https://pnetlab.example.test", "user", "secret", session=session, timeout=12
        )

        client.authenticate()
        nodes = client.list_nodes()

        self.assertEqual(nodes[0]["name"], "r1")
        self.assertEqual(session.headers["X-XSRF-TOKEN"], "test-token")
        self.assertTrue(all(call["verify"] is True for call in session.calls))
        self.assertTrue(all(call["timeout"] == 12 for call in session.calls))
        self.assertEqual(client._password, "")

    def test_template_normalization_filters_missing_templates(self) -> None:
        session = FakeSession(
            [
                FakeResponse(200),
                FakeResponse(202),
                FakeResponse(
                    200,
                    {
                        "data": {
                            "iosv": "Cisco IOSv",
                            "bad": "router.missing",
                            "vsrx": {"id": "vsrx", "name": "Juniper vSRX"},
                        }
                    },
                ),
            ]
        )
        client = PNetLabClient("http://pnetlab.test", "user", "secret", session=session)
        client.authenticate()

        templates = client.list_templates()

        self.assertEqual([item["id"] for item in templates], ["iosv", "vsrx"])

    def test_unexpected_status_raises_specific_error(self) -> None:
        session = FakeSession([FakeResponse(500)])
        client = PNetLabClient("https://pnetlab.test", "user", "secret", session=session)

        with self.assertRaisesRegex(PNetLabError, "HTTP 500"):
            client.authenticate()


if __name__ == "__main__":
    unittest.main()
