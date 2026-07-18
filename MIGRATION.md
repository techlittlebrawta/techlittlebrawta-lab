# securitylab migration record

This draft proposes absorbing the maintained content from
[`techlittlebrawta/securitylab`](https://github.com/techlittlebrawta/securitylab).

## Review status

- This migration is presented in a draft pull request for owner review.
- The nine placeholder-only topic folders and the unchanged VMware lab folder
  were completed separately and removed from source `main` and `test` after
  their destination copies were verified.
- Remaining source code and configuration are unchanged. Nothing else should be
  merged or removed until the proposed remediation decisions are explicitly
  approved.

## Source inventory

- Source default branch: `main`
- Reviewed source commit: `a9b94ca`
- Tracked items at reviewed source commit: 33
- Additional source branch: `test`
- Unique content on `test`: none; it was an older subset of `main`
- Source releases, issues, workflows, tags, Wiki pages, submodules, and Git LFS objects: none found

## Path map

| Source path | Destination path | Treatment |
| --- | --- | --- |
| Empty topic `README.md` files | Same top-level topic folders | Replaced blank files with useful scope and safety documentation |
| `ansible/ansible_automation_platform/*` | `ansible/legacy/ansible-automation-platform-2.4-bundle/` | Corrected group names, examples, secrets guidance, and installation documentation |
| `nmap/nmap_scan_subnet.yml` | `nmap/scan-subnet.yml` | Removed hard-coded hosts/target and shell execution; added validation and documentation |
| Seven `pnetlab/*.py` scripts | `pnetlab/api-tools/` | Consolidated into a reusable client and CLI with secure defaults, confirmation, tests, and documentation |
| `splunk/add-ons/TA-veracode/*` | `splunk/add-ons/TA-veracode/` | Reworked retries, JSON event output, credential handling, app layout, tests, and documentation |
| Placeholder file `splunk/apps` | `splunk/apps/README.md` | Converted the accidental file into a documented directory |
| `vmware/esxi/vmware_esxi_license.yml` | `vmware/esxi/vmware_esxi_license.yml` | Moved byte-for-byte in destination PR #10 and documented as authorized, disposable-lab-only automation |

## Important remediation decisions

At the repository owner's direction, the original ESXi playbook was migrated
byte-for-byte in separate destination PR #10 because it is used to recover a
private, disposable lab host without rebuilding it between exercises. Separate
documentation identifies the direct license-file replacement and `vpxa`
restart, requires an authorized lab host and recovery copy, prohibits production
use, and points normal environments to the vendor-supported licensing workflow.
This draft does not replace or otherwise modify that playbook.

The original PNETLab programs stored a server address, account name, and default
password in code and disabled TLS validation for every request. The replacement
uses environment variables or a hidden password prompt, verifies TLS by default,
adds timeouts and structured errors, and protects node wiping with confirmation.

The original Splunk add-on wrote temporary JSON arrays to disk and used a batch
input to delete them. The replacement emits one JSON finding per line directly
to Splunk, keeps logs on standard error, validates pagination hosts, and ships a
disabled, override-friendly app configuration.

## Validation

The migrated Python is compiled and unit tested without contacting live PNETLab,
Veracode, Splunk, or Nmap systems. YAML and repository hygiene checks
run in [`.github/workflows/validate.yml`](.github/workflows/validate.yml).

Live mutating tests are intentionally excluded because starting, stopping,
wiping, adding, or relicensing systems changes lab infrastructure. Each project
README documents the required manual validation.
