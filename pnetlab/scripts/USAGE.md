# Original PNETLab Python tools

The seven Python programs in this folder are preserved byte-for-byte from the
former `securitylab` repository. They operate against the PNETLab API and assume
a currently selected lab session.

## Programs

| Program | Behavior |
| --- | --- |
| `pnetlab_main_script.py` | Shared API client for authentication, templates, topology, status, node lifecycle, and wipe operations |
| `pnetlab_get_nodes_status.py` | Prints node names, IDs, URLs, and status |
| `pnetlab_start_all_nodes.py` | Starts every powered-off node in the selected lab |
| `pnetlab_stop_all_nodes.py` | Stops every powered-on node in the selected lab |
| `pnetlab_wipe_all_nodes.py` | Stops powered-on nodes and wipes every node without an interactive confirmation |
| `pnetlab_add_nodes.py` | Prompts for a template, base name, and count, then adds numbered nodes |
| `pnetlab_add_nodes_custom_payload.py` | Adds one node and overrides RAM/interface values for configured template prefixes |

## Requirements

- Python 3.
- The `requests` and `tabulate` packages.
- Network access to the PNETLab server.
- A PNETLab account authorized to operate the selected lab.
- A lab snapshot or export before stop, wipe, or node-add operations.

Create an isolated environment outside this scripts folder:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install requests tabulate
```

## Environment-specific values and security warnings

Every entry-point program contains these original values:

- URL: `http://192.168.1.252`
- User: `LabNodeManager`
- Password: `pnet`

The shared client disables TLS verification on all requests and sets no request
timeouts. These values and behaviors are intentionally unchanged for archival
fidelity. Do not expose this lab service to an untrusted network, reuse the
credential elsewhere, or treat this as production-ready code. If the lab values
differ, make a working copy outside this scripts folder and keep secrets out of Git.

## Running the tools

Run commands from this directory so the local client import resolves:

```sh
python pnetlab_get_nodes_status.py
python pnetlab_start_all_nodes.py
python pnetlab_stop_all_nodes.py
python pnetlab_add_nodes.py
python pnetlab_add_nodes_custom_payload.py
```

The wipe program is intentionally omitted from the routine command list. It has
no confirmation prompt and wipes every node returned by the current lab session:

```sh
python pnetlab_wipe_all_nodes.py
```

Run it only when complete loss of node state is intended.

## Validation and recovery

Compile without contacting PNETLab:

```sh
python -m py_compile *.py
```

Use the status program before any mutating program, confirm the selected lab in
the PNETLab interface, and export or snapshot the lab. Recovery from a wipe
requires the lab's own saved configuration, snapshot, or image state.

There are no source unit tests, request timeouts, dry-run mode, transaction, or
automatic rollback.
