import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import requests


MODULE_PATH = Path(__file__).resolve().parents[1] / "bin" / "veracode.py"
SPEC = importlib.util.spec_from_file_location("ta_veracode_script", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def response(status, payload, headers=None):
    result = requests.Response()
    result.status_code = status
    result._content = json.dumps(payload).encode("utf-8")
    result.headers.update(headers or {})
    result.url = MODULE.APPLICATIONS_URL
    return result


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


class VeracodeTests(unittest.TestCase):
    def test_retry_after_is_honored_for_rate_limit(self):
        session = FakeSession(
            [
                response(429, {}, {"Retry-After": "3"}),
                response(200, {"_embedded": {"applications": []}, "_links": {}}),
            ]
        )
        with patch.object(MODULE.time, "sleep") as sleep:
            payload = MODULE.request_json(session, MODULE.APPLICATIONS_URL, object())

        self.assertIn("_embedded", payload)
        sleep.assert_called_once_with(3.0)
        self.assertEqual(len(session.calls), 2)

    def test_untrusted_pagination_host_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unexpected pagination URL"):
            MODULE._validated_api_url("https://example.com/steal")

    def test_finding_event_keeps_application_context(self):
        event = MODULE.finding_event(
            {"guid": "app-guid", "profile": {"name": "Example App"}},
            {"issue_id": 42, "severity": 3},
        )

        self.assertEqual(event["veracode_application"]["name"], "Example App")
        self.assertEqual(event["veracode_finding"]["issue_id"], 42)


if __name__ == "__main__":
    unittest.main()
