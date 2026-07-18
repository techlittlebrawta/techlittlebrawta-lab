#!/usr/bin/env python3
"""Command-line tools for a PNETLab 6 lab session."""

from __future__ import annotations

import argparse
import getpass
import os
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

import requests
import urllib3

from pnetlab_client import PNetLabClient, PNetLabError


STATUS_NAMES = {0: "Powered Off", 2: "Powered On"}
TEMPLATE_PROFILES: Dict[str, Dict[str, int]] = {
    "vsrx": {"ram": 8192, "ethernet": 8},
    "windows": {"ram": 16384, "ethernet": 4},
    "cisco": {"ram": 4096, "ethernet": 2},
    "linux": {"ram": 2048, "ethernet": 1},
}


def print_table(headers: Sequence[str], rows: Iterable[Sequence[Any]]) -> None:
    prepared = [[str(value) for value in row] for row in rows]
    widths = [len(header) for header in headers]
    for row in prepared:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))
    print("  ".join(header.ljust(widths[index]) for index, header in enumerate(headers)))
    print("  ".join("-" * width for width in widths))
    for row in prepared:
        print("  ".join(value.ljust(widths[index]) for index, value in enumerate(row)))


def node_rows(client: PNetLabClient) -> List[List[str]]:
    nodes = client.list_nodes()
    statuses = client.get_node_statuses()
    rows: List[List[str]] = []
    for node in sorted(nodes, key=lambda item: str(item.get("name", "")).lower()):
        node_id = str(node.get("id", ""))
        status_code = statuses.get(node_id)
        status = STATUS_NAMES.get(status_code, f"Unknown ({status_code})")
        rows.append([str(node.get("name", "")), node_id, str(node.get("url", "")), status])
    return rows


def show_status(client: PNetLabClient) -> None:
    rows = node_rows(client)
    if not rows:
        print("No nodes were found in the active lab session.")
        return
    print_table(["Name", "ID", "URL", "Status"], rows)


def change_nodes(client: PNetLabClient, action: str) -> int:
    target_status = 0 if action == "start" else 2
    statuses = client.get_node_statuses()
    node_ids = [node_id for node_id, status in statuses.items() if status == target_status]
    if not node_ids:
        print(f"No nodes need to {action}.")
        return 0

    failures = 0
    method = client.start_node if action == "start" else client.stop_node
    for node_id in node_ids:
        try:
            method(node_id)
            print(f"{action.title()}ed node {node_id}.")
        except PNetLabError as exc:
            failures += 1
            print(f"Failed to {action} node {node_id}: {exc}", file=sys.stderr)
    return failures


def confirm_wipe(assume_yes: bool) -> bool:
    if assume_yes:
        return True
    print("WARNING: wiping removes the saved state of every node in the active lab session.")
    answer = input('Type "WIPE ALL NODES" to continue: ')
    return answer == "WIPE ALL NODES"


def wipe_all(client: PNetLabClient, assume_yes: bool) -> int:
    if not confirm_wipe(assume_yes):
        print("Wipe cancelled.")
        return 0

    stop_failures = change_nodes(client, "stop")
    if stop_failures:
        print("Not all running nodes stopped; wipe cancelled.", file=sys.stderr)
        return stop_failures

    nodes = client.list_nodes()
    failures = 0
    for node in nodes:
        node_id = str(node.get("id", ""))
        if not node_id:
            failures += 1
            continue
        try:
            client.wipe_node(node_id)
            print(f"Wiped node {node_id}.")
        except PNetLabError as exc:
            failures += 1
            print(f"Failed to wipe node {node_id}: {exc}", file=sys.stderr)
    return failures


def matching_profile(template_id: str) -> Mapping[str, int]:
    lowered = template_id.lower()
    for prefix, values in TEMPLATE_PROFILES.items():
        if lowered.startswith(prefix):
            return values
    return {}


def add_nodes(client: PNetLabClient, args: argparse.Namespace) -> int:
    base_payload = client.get_template_payload(args.template_id)
    if args.use_profile:
        base_payload.update(matching_profile(args.template_id))
    if args.ram is not None:
        base_payload["ram"] = args.ram
    if args.ethernet is not None:
        base_payload["ethernet"] = args.ethernet

    failures = 0
    for number in range(1, args.count + 1):
        payload = deepcopy(base_payload)
        payload["name"] = args.name if args.count == 1 else f"{args.name}-{number:02d}"
        try:
            client.add_node(payload)
            print(f"Added node {payload['name']}.")
        except (PNetLabError, ValueError) as exc:
            failures += 1
            print(f"Failed to add {payload['name']}: {exc}", file=sys.stderr)
    return failures


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=os.getenv("PNETLAB_URL"), help="PNETLab base URL")
    parser.add_argument(
        "--username", default=os.getenv("PNETLAB_USERNAME"), help="PNETLab username"
    )
    parser.add_argument(
        "--timeout", type=float, default=30.0, help="HTTP timeout in seconds (default: 30)"
    )
    tls = parser.add_mutually_exclusive_group()
    tls.add_argument("--ca-bundle", help="PEM CA bundle for the PNETLab HTTPS certificate")
    tls.add_argument(
        "--insecure",
        action="store_true",
        help="disable TLS certificate verification (trusted lab networks only)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status", help="show nodes and their current state")
    subparsers.add_parser("start-all", help="start every powered-off node")
    subparsers.add_parser("stop-all", help="stop every powered-on node")
    wipe = subparsers.add_parser("wipe-all", help="wipe every node in the active session")
    wipe.add_argument("--yes", action="store_true", help="skip the typed destructive confirmation")
    subparsers.add_parser("templates", help="list usable node templates")

    add = subparsers.add_parser("add-nodes", help="add one or more nodes from a template")
    add.add_argument("template_id", help="template ID reported by the templates command")
    add.add_argument("name", help="node name, or base name when count is greater than one")
    add.add_argument("--count", type=int, default=1, help="number of nodes to add (default: 1)")
    add.add_argument("--ram", type=int, help="override RAM in MiB")
    add.add_argument("--ethernet", type=int, help="override Ethernet interface count")
    add.add_argument(
        "--use-profile",
        action="store_true",
        help="apply the built-in vSRX, Windows, Cisco, or Linux profile when matched",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    if not args.url:
        raise ValueError("set PNETLAB_URL or supply --url")
    if not args.username:
        raise ValueError("set PNETLAB_USERNAME or supply --username")
    if args.timeout <= 0:
        raise ValueError("--timeout must be greater than zero")
    if getattr(args, "count", 1) <= 0:
        raise ValueError("--count must be greater than zero")
    if getattr(args, "ram", None) is not None and args.ram <= 0:
        raise ValueError("--ram must be greater than zero")
    if getattr(args, "ethernet", None) is not None and args.ethernet <= 0:
        raise ValueError("--ethernet must be greater than zero")

    verify: Any = True
    if args.insecure:
        verify = False
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    elif args.ca_bundle:
        ca_bundle = Path(args.ca_bundle).expanduser()
        if not ca_bundle.is_file():
            raise ValueError(f"CA bundle does not exist: {ca_bundle}")
        verify = str(ca_bundle)

    password = os.getenv("PNETLAB_PASSWORD") or getpass.getpass("PNETLab password: ")
    client = PNetLabClient(
        args.url,
        args.username,
        password,
        verify=verify,
        timeout=args.timeout,
    )
    try:
        client.authenticate()
        if args.command == "status":
            show_status(client)
            return 0
        if args.command == "start-all":
            result = change_nodes(client, "start")
            show_status(client)
            return min(result, 1)
        if args.command == "stop-all":
            result = change_nodes(client, "stop")
            show_status(client)
            return min(result, 1)
        if args.command == "wipe-all":
            result = wipe_all(client, args.yes)
            show_status(client)
            return min(result, 1)
        if args.command == "templates":
            templates = client.list_templates()
            print_table(["Template ID", "Name"], [[item["id"], item["name"]] for item in templates])
            return 0
        if args.command == "add-nodes":
            return min(add_nodes(client, args), 1)
        raise ValueError(f"unknown command: {args.command}")
    finally:
        client.sign_out()


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return run(args)
    except (PNetLabError, ValueError, requests.RequestException) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
