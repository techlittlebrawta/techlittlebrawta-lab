# Archived securitylab content

This directory preserves the remaining unique file content and Git history from
the former `techlittlebrawta/securitylab` repository before that repository was
deleted.

## Preservation policy

The original files under this archive were copied without content changes. Do
not silently edit them. If a modernized implementation is needed, create it in
the appropriate current project folder and leave the archived source available
for comparison.

The original code contains environment-specific addresses, credentials,
disabled TLS verification, enabled inputs, and destructive operations. An
unchanged copy is not automatically a safe or portable copy. Read the matching
usage guide before running anything.

## Contents

| Component | Original content | Documentation |
| --- | --- | --- |
| Repository record | Original root `README.md` | This index and [`SOURCE-MANIFEST.md`](SOURCE-MANIFEST.md) |
| Nmap | `nmap/nmap_scan_subnet.yml` | [`nmap/USAGE.md`](nmap/USAGE.md) |
| PNETLab | Seven Python programs and original placeholder README | [`pnetlab/USAGE.md`](pnetlab/USAGE.md) |
| Splunk | Original TA-Veracode program and Splunk configuration | [`splunk/USAGE.md`](splunk/USAGE.md) |

## Intentionally excluded

The source `ansible/` folder contained older Ansible Automation Platform 2.4
installation notes and inventory examples. It was intentionally deleted during
migration because this repository already contains a newer, documented Ansible
Automation Platform implementation under [`../../ansible/`](../../ansible/).

## Previously completed moves

- Placeholder-only topic folders were moved in
  [`techlittlebrawta-lab` PR #9](https://github.com/techlittlebrawta/techlittlebrawta-lab/pull/9).
- The unchanged VMware lab playbook and its lab-only documentation were moved in
  [`techlittlebrawta-lab` PR #10](https://github.com/techlittlebrawta/techlittlebrawta-lab/pull/10).

## History

The final source `main`, `test`, and migration-cleanup branch histories were
joined into the destination repository history before source deletion. The
source tree and branch-tip record are in
[`SOURCE-MANIFEST.md`](SOURCE-MANIFEST.md).
