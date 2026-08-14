#!/usr/bin/env python3
"""Idempotently reconcile scoped AAP controller objects with a bearer token.

AAP 2.7's certified ansible.controller 4.8.1 collection declares ``aap_token``
but does not attach it to HTTP requests. This narrow reconciler uses the same
public controller API with the supported gateway Bearer authentication scheme.
It intentionally does not manage users, teams, organizations, secret inputs,
or gateway role assignments.
"""

from __future__ import annotations

import argparse
import json
import getpass
import os
import sys
import time
from typing import Any

import requests
import yaml


class Controller:
    def __init__(self) -> None:
        self.host = os.environ["CONTROLLER_HOST"].rstrip("/")
        verify_value = os.getenv("AAP_VALIDATE_CERTS", "true").lower()
        self.verify: bool | str = verify_value not in {"0", "false", "no"}
        self.session = requests.Session()
        token = os.getenv("CONTROLLER_OAUTH_TOKEN")
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        elif os.getenv("CONTROLLER_BASIC_USER"):
            self.session.auth = (
                os.environ["CONTROLLER_BASIC_USER"],
                getpass.getpass("AAP password: "),
            )
        else:
            raise RuntimeError("Controller bearer token or prompted basic user is required")
        self.session.headers.update({"Accept": "application/json"})
        self.changed: list[str] = []

    def url(self, path: str) -> str:
        return path if path.startswith("http") else f"{self.host}{path}"

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        response = self.session.request(
            method, self.url(path), timeout=60, verify=self.verify, **kwargs
        )
        if not response.ok:
            detail = response.text[:1000]
            if os.getenv("CONTROLLER_OAUTH_TOKEN"):
                detail = detail.replace(os.environ["CONTROLLER_OAUTH_TOKEN"], "***")
            raise RuntimeError(
                f"{method} {path} returned HTTP {response.status_code}: {detail}"
            )
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    def list(self, endpoint: str, **filters: Any) -> list[dict[str, Any]]:
        filters["page_size"] = 200
        data = self.request(
            "GET", f"/api/controller/v2/{endpoint}/", params=filters
        )
        return data["results"]

    def one(self, endpoint: str, name: str, **filters: Any) -> dict[str, Any]:
        results = self.list(endpoint, name=name, **filters)
        if len(results) != 1:
            raise RuntimeError(
                f"Expected one {endpoint} named {name!r}; found {len(results)}"
            )
        return results[0]

    @staticmethod
    def _equal(current: Any, desired: Any) -> bool:
        if isinstance(desired, dict) and isinstance(current, str):
            try:
                current = yaml.safe_load(current) or {}
            except yaml.YAMLError:
                return False
        if isinstance(desired, str) and isinstance(current, str) and "\n" in desired:
            try:
                return yaml.safe_load(current) == yaml.safe_load(desired)
            except yaml.YAMLError:
                return False
        return current == desired

    def ensure(
        self,
        endpoint: str,
        name: str,
        payload: dict[str, Any],
        filters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        results = self.list(endpoint, name=name, **(filters or {}))
        if len(results) > 1:
            raise RuntimeError(f"Ambiguous {endpoint} name {name!r}")
        if not results:
            item = self.request(
                "POST",
                f"/api/controller/v2/{endpoint}/",
                json={"name": name, **payload},
            )
            self.changed.append(f"created {endpoint}:{name}")
            return item
        item = results[0]
        delta = {
            key: value
            for key, value in payload.items()
            if not self._equal(item.get(key), value)
        }
        if delta:
            item = self.request("PATCH", item["url"], json=delta)
            self.changed.append(f"updated {endpoint}:{name}")
        return item

    def reconcile_association(
        self, path: str, desired_ids: set[int], label: str
    ) -> None:
        current = self.request("GET", path, params={"page_size": 200})["results"]
        current_ids = {item["id"] for item in current}
        for object_id in sorted(desired_ids - current_ids):
            self.request("POST", path, json={"id": object_id})
            self.changed.append(f"associated {label}:{object_id}")
        for object_id in sorted(current_ids - desired_ids):
            self.request("POST", path, json={"id": object_id, "disassociate": True})
            self.changed.append(f"disassociated {label}:{object_id}")


def organization_id(api: Controller, name: str) -> int:
    return api.one("organizations", name)["id"]


def ujt(api: Controller, name: str) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    for endpoint in ("job_templates", "workflow_job_templates", "projects"):
        matches.extend(api.list(endpoint, name=name))
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one unified job template named {name!r}; found {len(matches)}"
        )
    return matches[0]


def reconcile(data: dict[str, Any]) -> Controller:
    api = Controller()
    api.request("GET", "/api/controller/v2/me/")

    for item in data["inventories"]:
        org = organization_id(api, item["organization"])
        api.ensure(
            "inventories",
            item["name"],
            {
                "organization": org,
                "description": item.get("description", ""),
                "variables": yaml.safe_dump(item.get("variables", {}), sort_keys=True),
            },
            {"organization": org},
        )

    for item in data["hosts"]:
        inventory = api.one("inventories", item["inventory"])
        api.ensure(
            "hosts",
            item["name"],
            {
                "inventory": inventory["id"],
                "enabled": item.get("enabled", True),
                "variables": yaml.safe_dump(item.get("variables", {}), sort_keys=True),
            },
            {"inventory": inventory["id"]},
        )

    for item in data["groups"]:
        inventory = api.one("inventories", item["inventory"])
        group = api.ensure(
            "groups",
            item["name"],
            {"inventory": inventory["id"]},
            {"inventory": inventory["id"]},
        )
        desired = {
            api.one("hosts", name, inventory=inventory["id"])["id"]
            for name in item.get("hosts", [])
        }
        api.reconcile_association(
            group["related"]["hosts"], desired, f"group-hosts:{item['name']}"
        )

    for item in data.get("credential_types", []):
        api.ensure(
            "credential_types",
            item["name"],
            {
                "description": item.get("description", ""),
                "kind": item.get("kind", "cloud"),
                "inputs": item.get("inputs", {}),
                "injectors": item.get("injectors", {}),
            },
        )

    for item in data["credentials"]:
        org = organization_id(api, item["organization"])
        credential_type = api.one("credential_types", item["credential_type"])["id"]
        credential = api.ensure(
            "credentials",
            item["name"],
            {
                "organization": org,
                "credential_type": credential_type,
                "description": item.get("description", ""),
            },
            {"organization": org},
        )
        input_values = dict(item.get("inputs", {}))
        input_files_available = False
        for field, environment_name in item.get("input_files", {}).items():
            path = os.getenv(environment_name)
            if path:
                input_values[field] = open(path, encoding="utf-8").read()
                input_files_available = True
        if input_values and (input_files_available or not credential.get("inputs")):
            api.request("PATCH", credential["url"], json={"inputs": input_values})
            api.changed.append(f"updated credential-inputs:{item['name']}")

    for item in data.get("execution_environments", []):
        org = (
            organization_id(api, item["organization"])
            if item.get("organization")
            else None
        )
        api.ensure(
            "execution_environments",
            item["name"],
            {
                "organization": org,
                "description": item.get("description", ""),
                "image": item["image"],
                "pull": item.get("pull", "missing"),
            },
        )

    projects_to_update: list[dict[str, Any]] = []
    for item in data["projects"]:
        org = organization_id(api, item["organization"])
        environment = api.one(
            "execution_environments", item["default_environment"]
        )["id"]
        project = api.ensure(
            "projects",
            item["name"],
            {
                "organization": org,
                "description": item.get("description", ""),
                "scm_type": item["scm_type"],
                "scm_url": item["scm_url"],
                "scm_branch": item.get("scm_branch", ""),
                "scm_clean": item.get("scm_clean", True),
                "scm_delete_on_update": item.get("scm_delete_on_update", False),
                "scm_track_submodules": item.get("scm_track_submodules", False),
                "scm_update_on_launch": item.get("scm_update_on_launch", False),
                "allow_override": item.get("allow_override", False),
                "default_environment": environment,
            },
            {"organization": org},
        )
        if item.get("update_project"):
            projects_to_update.append(project)

    for project in projects_to_update:
        update = api.request("POST", project["related"]["update"], json={})
        while update.get("status") not in {"successful", "failed", "error", "canceled"}:
            time.sleep(2)
            update = api.request("GET", update["url"])
        if update.get("status") != "successful":
            raise RuntimeError(f"Project update for {project['name']} ended {update.get('status')}")
        api.changed.append(f"updated project:{project['name']}")

    for item in data["templates"]:
        org = organization_id(api, item["organization"])
        project = api.one("projects", item["project"], organization=org)["id"]
        inventory = (
            api.one("inventories", item["inventory"])["id"]
            if item.get("inventory")
            else None
        )
        environment = api.one(
            "execution_environments", item["execution_environment"]
        )["id"]
        template = api.ensure(
            "job_templates",
            item["name"],
            {
                "organization": org,
                "description": item.get("description", ""),
                "project": project,
                "playbook": item["playbook"],
                "inventory": inventory,
                "execution_environment": environment,
                "limit": item.get("limit", ""),
                "job_type": item.get("job_type", "run"),
                "timeout": item.get("timeout", 600),
                "forks": item.get("forks", 0),
                "become_enabled": item.get("become_enabled", False),
                "ask_credential_on_launch": item.get(
                    "ask_credential_on_launch", False
                ),
                "ask_variables_on_launch": item.get("ask_variables_on_launch", False),
                "ask_limit_on_launch": item.get("ask_limit_on_launch", False),
            },
            {"organization": org},
        )
        credential_ids = {
            api.one("credentials", name, organization=org)["id"]
            for name in item.get("credentials", [])
        }
        api.reconcile_association(
            template["related"]["credentials"],
            credential_ids,
            f"template-credentials:{item['name']}",
        )

    for item in data["workflows"]:
        org = organization_id(api, item["organization"])
        workflow = api.ensure(
            "workflow_job_templates",
            item["name"],
            {
                "organization": org,
                "description": item.get("description", ""),
                "allow_simultaneous": item.get("allow_simultaneous", False),
                "ask_variables_on_launch": False,
                "ask_inventory_on_launch": False,
                "ask_limit_on_launch": False,
                "ask_scm_branch_on_launch": False,
            },
            {"organization": org},
        )
        nodes_path = workflow["related"]["workflow_nodes"]
        existing = api.request("GET", nodes_path, params={"page_size": 200})[
            "results"
        ]
        nodes: dict[str, dict[str, Any]] = {}
        for node_data in item.get("workflow_nodes", []):
            identifier = node_data["identifier"]
            matches = [node for node in existing if node["identifier"] == identifier]
            if matches:
                node = matches[0]
            else:
                payload: dict[str, Any] = {"identifier": identifier}
                if node_data.get("unified_job_template"):
                    payload["unified_job_template"] = ujt(
                        api, node_data["unified_job_template"]
                    )["id"]
                node = api.request("POST", nodes_path, json=payload)
                api.changed.append(
                    f"created workflow-node:{item['name']}:{identifier}"
                )
                if node_data.get("approval_node"):
                    approval = node_data["approval_node"]
                    api.request(
                        "POST",
                        node["related"]["create_approval_template"],
                        json={
                            "name": approval["name"],
                            "description": approval.get("description", ""),
                            "timeout": approval.get("timeout", 0),
                        },
                    )
                    api.changed.append(
                        f"created workflow-approval:{item['name']}:{identifier}"
                    )
            nodes[identifier] = node
        for node_data in item.get("workflow_nodes", []):
            parent = nodes[node_data["identifier"]]
            for relationship in ("success_nodes", "failure_nodes", "always_nodes"):
                desired = {nodes[name]["id"] for name in node_data.get(relationship, [])}
                api.reconcile_association(
                    parent["related"][relationship],
                    desired,
                    f"workflow-edge:{item['name']}:{node_data['identifier']}:{relationship}",
                )

    for item in data["schedules"]:
        api.ensure(
            "schedules",
            item["name"],
            {
                "description": item.get("description", ""),
                "unified_job_template": ujt(
                    api, item["unified_job_template"]
                )["id"],
                "rrule": item["rrule"],
                "enabled": item.get("enabled", True),
            },
        )

    return api


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="YAML or JSON desired-state file; defaults to JSON on stdin")
    args = parser.parse_args()
    if args.config:
        with open(args.config, encoding="utf-8") as source:
            data = yaml.safe_load(source)
    else:
        data = json.load(sys.stdin)
    api = reconcile(data)
    print(json.dumps({"changed": bool(api.changed), "actions": api.changed}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"AAP reconciliation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
