import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "runner/mbj_ansible_runner.py"
SPEC = importlib.util.spec_from_file_location("mbj_runner", MODULE_PATH)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class RunnerValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.requests = self.root / "requests"
        self.secrets = self.root / "secrets"
        self.requests.mkdir()
        self.secrets.mkdir()
        self.old_request_root = runner.REQUEST_ROOT
        self.old_secret_root = runner.SECRET_ROOT
        runner.REQUEST_ROOT = self.requests
        runner.SECRET_ROOT = self.secrets

    def tearDown(self):
        runner.REQUEST_ROOT = self.old_request_root
        runner.SECRET_ROOT = self.old_secret_root
        self.temp.cleanup()

    def request(self, **changes):
        payload = {"schema": 1, "playbook": "read_only", "limit": "linux", "extra_vars": {}, "aap_job_id": "123"}
        payload.update(changes)
        path = self.requests / "request.json"
        path.write_text(json.dumps(payload))
        return path

    def test_valid_request(self):
        request, path = runner.validate_request(str(self.request()))
        self.assertEqual(request["playbook"], "read_only")
        self.assertEqual(path.parent, self.requests)

    def test_rejects_path_traversal(self):
        outside = self.root / "outside.json"
        outside.write_text("{}")
        with self.assertRaises(ValueError):
            runner.validate_request(str(outside))

    def test_rejects_shell_limit(self):
        with self.assertRaises(ValueError):
            runner.validate_request(str(self.request(limit="linux;id")))

    def test_rejects_unapproved_playbook(self):
        with self.assertRaises(ValueError):
            runner.validate_request(str(self.request(playbook="../../shell")))

    def test_rejects_secret_extra_variable(self):
        with self.assertRaises(ValueError):
            runner.validate_request(str(self.request(extra_vars={"password": "bad"})))

    def test_secret_file_is_consumed_and_not_logged(self):
        secret = self.secrets / "secret.json"
        secret.write_text(json.dumps({"TLB_LAB_PASSWORD": "sensitive-value"}))
        os.chmod(secret, 0o600)
        environment, redactions = runner.load_secret_environment({"secret_file": str(secret)})
        self.assertEqual(environment["TLB_LAB_PASSWORD"], "sensitive-value")
        self.assertFalse(secret.exists())
        self.assertEqual(runner.redact("value=sensitive-value", redactions), "value=***")


if __name__ == "__main__":
    unittest.main()
