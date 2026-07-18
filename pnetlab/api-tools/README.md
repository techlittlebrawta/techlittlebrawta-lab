# PNETLab API tools

These tools replace the seven experimental scripts migrated from
`techlittlebrawta/securitylab`. They provide the same node-status, start, stop,
wipe, template, and node-creation workflows through one reusable client and one
command-line program.

The PNETLab endpoints used by these tools are based on the PNETLab 6 web
interface and are not guaranteed to remain stable across releases. Test against
a disposable lab before using a mutating command.

## Security improvements

- No URL, username, or password is stored in source code.
- Passwords come from a protected environment variable or a hidden prompt.
- HTTPS certificate verification is enabled by default.
- Every HTTP request has a timeout and validates its response status.
- `wipe-all` requires an exact typed confirmation unless automation explicitly
  supplies `--yes`.
- Repeated scripts and unused imports were consolidated into tested modules.

## Requirements

- Python 3.8 or newer
- Network access to a PNETLab 6 instance
- A PNETLab account authorized for the requested operation
- An active lab session in PNETLab for node operations

Create a virtual environment and install the dependency:

```bash
cd pnetlab/api-tools
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows PowerShell, activate the environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Configure credentials

Set the non-secret connection values and put the password in the environment
only for the current shell:

```bash
export PNETLAB_URL="https://pnetlab.example.com"
export PNETLAB_USERNAME="LabNodeManager"
export PNETLAB_PASSWORD="replace-with-the-real-password"
```

If `PNETLAB_PASSWORD` is not set, the CLI prompts for it without displaying the
characters. Do not put passwords in Git, shell scripts, command-line arguments,
or screenshots.

If PNETLab uses a private certificate authority, pass its PEM bundle:

```bash
python pnetlab_cli.py --ca-bundle /path/to/lab-ca.pem status
```

`--insecure` disables certificate verification and should be used only for a
temporary test on a trusted lab network. Installing the correct CA certificate
is preferred.

## Commands

Show nodes in the active lab session:

```bash
python pnetlab_cli.py status
```

List templates:

```bash
python pnetlab_cli.py templates
```

Add one node:

```bash
python pnetlab_cli.py add-nodes iosv Router-01
```

Add three nodes named `Router-01` through `Router-03`:

```bash
python pnetlab_cli.py add-nodes iosv Router --count 3
```

Override the template's RAM and Ethernet interface count:

```bash
python pnetlab_cli.py add-nodes vsrx vSRX-01 --ram 8192 --ethernet 8
```

The migrated vSRX, Windows, Cisco, and Linux defaults are available only when
`--use-profile` is explicitly supplied. Explicit `--ram` or `--ethernet` values
take precedence over a profile.

Start or stop every applicable node:

```bash
python pnetlab_cli.py start-all
python pnetlab_cli.py stop-all
```

Wipe every node's saved state in the active session:

```bash
python pnetlab_cli.py wipe-all
```

The command requires typing `WIPE ALL NODES`. Noninteractive automation may use
`wipe-all --yes` only when that destructive operation is intentional.

## Test

The tests use fake HTTP sessions and do not contact a PNETLab system:

```bash
python -m unittest discover -s tests -v
```

Live tests are intentionally not automated because start, stop, add, and wipe
operations change the active lab.
