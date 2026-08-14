#!/usr/bin/env python3
"""Validated execution boundary between AAP and Community Ansible."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import stat
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

AUTOMATION_ROOT = Path("/opt/automation")
REPOSITORY = AUTOMATION_ROOT / "repos/techlittlebrawta-lab"
INVENTORY = REPOSITORY / "automation/inventories/pnetlab/hosts.yml"
PLAYBOOK_ROOT = REPOSITORY / "automation/playbooks/community"
ANSIBLE_PLAYBOOK = AUTOMATION_ROOT / "runtime/venv/bin/ansible-playbook"
REQUEST_ROOT = AUTOMATION_ROOT / "runtime/requests"
SECRET_ROOT = AUTOMATION_ROOT / "runtime/secrets"
RESULT_ROOT = AUTOMATION_ROOT / "artifacts"
LOG_ROOT = AUTOMATION_ROOT / "logs"
LOCK_FILE = AUTOMATION_ROOT / "runtime/runner.lock"

APPROVED_PLAYBOOKS = {
    "read_only": "pnetlab_read_only.yml",
    "platform_validate": "pnetlab_platform_validate.yml",
    "controlled_failure": "controlled_failure.yml",
}
ALLOWED_EXTRA_VARS = {"operation", "validation_mode", "expected_failure"}
SAFE_LIMIT = re.compile(r"^[A-Za-z0-9_.:-]{1,240}$")
SAFE_CONTEXT = re.compile(r"^[A-Za-z0-9_.:-]{0,128}$")
SECRET_KEY = re.compile(r"pass|secret|token|private|key", re.IGNORECASE)
RECAP = re.compile(
    r"^(?P<host>\S+)\s+:\s+ok=(?P<ok>\d+)\s+changed=(?P<changed>\d+)\s+"
    r"unreachable=(?P<unreachable>\d+)\s+failed=(?P<failed>\d+)",
    re.MULTILINE,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def contained(path: Path, root: Path) -> Path:
    resolved = path.resolve(strict=True)
    if resolved.parent != root.resolve():
        raise ValueError(f"path is outside {root}")
    return resolved


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def validate_request(raw_path: str) -> tuple[dict, Path]:
    request_path = contained(Path(raw_path), REQUEST_ROOT)
    request = load_json(request_path)
    if set(request) - {"schema", "playbook", "limit", "extra_vars", "aap_job_id", "aap_workflow_job_id", "secret_file"}:
        raise ValueError("request contains unsupported fields")
    if request.get("schema") != 1:
        raise ValueError("unsupported request schema")
    if request.get("playbook") not in APPROVED_PLAYBOOKS:
        raise ValueError("playbook is not approved")
    limit = request.get("limit", "pnetlab")
    if not isinstance(limit, str) or not SAFE_LIMIT.fullmatch(limit):
        raise ValueError("invalid inventory limit")
    for field in ("aap_job_id", "aap_workflow_job_id"):
        value = str(request.get(field, ""))
        if not SAFE_CONTEXT.fullmatch(value):
            raise ValueError(f"invalid {field}")
    extra_vars = request.get("extra_vars", {})
    if not isinstance(extra_vars, dict) or set(extra_vars) - ALLOWED_EXTRA_VARS:
        raise ValueError("extra_vars contains unsupported keys")
    if any(SECRET_KEY.search(str(key)) for key in extra_vars):
        raise ValueError("secrets are not accepted as extra variables")
    if any(not isinstance(value, (str, int, bool)) or len(str(value)) > 256 for value in extra_vars.values()):
        raise ValueError("invalid extra variable value")
    return request, request_path


def load_secret_environment(request: dict) -> tuple[dict[str, str], list[str]]:
    environment = os.environ.copy()
    environment["ANSIBLE_CONFIG"] = "/etc/ansible/mbj-ansible.cfg"
    environment["ANSIBLE_COLLECTIONS_PATH"] = "/opt/automation/collections:/usr/share/ansible/collections"
    redactions: list[str] = []
    raw_path = request.get("secret_file")
    if not raw_path:
        return environment, redactions
    secret_path = contained(Path(raw_path), SECRET_ROOT)
    mode = stat.S_IMODE(secret_path.stat().st_mode)
    if mode & 0o077:
        raise ValueError("secret file permissions are too broad")
    try:
        secret_values = load_json(secret_path)
    finally:
        secret_path.unlink(missing_ok=True)
    if not isinstance(secret_values, dict):
        raise ValueError("secret file must contain an object")
    for key, value in secret_values.items():
        if not re.fullmatch(r"TLB_[A-Z0-9_]{1,80}", str(key)) or not isinstance(value, str):
            raise ValueError("invalid secret environment field")
        environment[str(key)] = value
        if value:
            redactions.append(value)
    return environment, redactions


def redact(text: str, secrets: list[str]) -> str:
    for secret in sorted(secrets, key=len, reverse=True):
        text = text.replace(secret, "***")
    text = re.sub(r"(?i)(password|token|secret)(\s*[=:]\s*)\S+", r"\1\2***", text)
    return text


def git_sha() -> str:
    result = subprocess.run(
        ["/usr/bin/git", "-C", str(REPOSITORY), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def execute(request: dict, execution_id: str, environment: dict[str, str], redactions: list[str]) -> dict:
    playbook = PLAYBOOK_ROOT / APPROVED_PLAYBOOKS[request["playbook"]]
    if not playbook.is_file() or not INVENTORY.is_file() or not ANSIBLE_PLAYBOOK.is_file():
        raise RuntimeError("Community Ansible runtime is incomplete")
    command = [str(ANSIBLE_PLAYBOOK), "-i", str(INVENTORY), str(playbook), "--limit", request.get("limit", "pnetlab")]
    if request.get("extra_vars"):
        command.extend(["--extra-vars", json.dumps(request["extra_vars"], separators=(",", ":"))])

    started = utc_now()
    process = subprocess.run(command, capture_output=True, text=True, env=environment, cwd=REPOSITORY)
    finished = utc_now()
    output = redact(process.stdout + process.stderr, redactions)
    (LOG_ROOT / f"{execution_id}.log").write_text(output)

    host_results = []
    for match in RECAP.finditer(output):
        host_results.append({"host": match["host"], **{key: int(match[key]) for key in ("ok", "changed", "unreachable", "failed")}})
    result = {
        "execution_id": execution_id,
        "aap_job_id": str(request.get("aap_job_id", "")),
        "aap_workflow_job_id": str(request.get("aap_workflow_job_id", "")),
        "git_commit": git_sha(),
        "playbook": request["playbook"],
        "inventory": str(INVENTORY),
        "limit": request.get("limit", "pnetlab"),
        "started": started,
        "finished": finished,
        "return_code": process.returncode,
        "changed": sum(item["changed"] for item in host_results),
        "failed": sum(item["failed"] for item in host_results),
        "unreachable": sum(item["unreachable"] for item in host_results),
        "hosts": host_results,
    }
    (RESULT_ROOT / f"{execution_id}.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    args = parser.parse_args()
    execution_id = str(uuid.uuid4())
    request_path: Path | None = None
    try:
        request, request_path = validate_request(args.request)
        environment, redactions = load_secret_environment(request)
        LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOCK_FILE.open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            result = execute(request, execution_id, environment, redactions)
        print(json.dumps(result, sort_keys=True))
        return int(result["return_code"])
    except Exception as exc:
        error = {"execution_id": execution_id, "return_code": 2, "error": redact(str(exc), [])}
        print(json.dumps(error, sort_keys=True), file=sys.stderr)
        return 2
    finally:
        if request_path is not None:
            request_path.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
