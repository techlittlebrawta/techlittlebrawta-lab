# securitylab migration record

This directory records the migration of the former
`techlittlebrawta/securitylab` repository into this repository. The migrated
working files are stored in their appropriate project locations, not in a
`legacy` wrapper.

## Current locations

| Component | Current location | Documentation |
| --- | --- | --- |
| Original source README | [`original-README.md`](original-README.md) | Preserved byte-for-byte because the destination already has its own root README |
| Nmap | [`../../nmap/`](../../nmap/) | [`../../nmap/USAGE.md`](../../nmap/USAGE.md) |
| PNETLab Python tools | [`../../pnetlab/scripts/`](../../pnetlab/scripts/) | [`../../pnetlab/scripts/USAGE.md`](../../pnetlab/scripts/USAGE.md) |
| PNETLab local installer | [`../../pnetlab/pnetlab-v6-local/`](../../pnetlab/pnetlab-v6-local/) | Kept separate and unchanged |
| Splunk | [`../../splunk/`](../../splunk/) | [`../../splunk/USAGE.md`](../../splunk/USAGE.md) |

## Preservation policy

The original scripts, playbooks, placeholders, and Splunk configuration retain
their original Git blob IDs. Only the migration-specific usage documentation
was updated to reflect the corrected paths. Review each usage guide before
running lab code because the source includes environment-specific settings and
destructive operations.

## Intentionally excluded

The source `ansible/` folder contained an older Ansible Automation Platform 2.4
setup. It was intentionally excluded because this repository already contains a
newer Ansible implementation under [`../../ansible/`](../../ansible/).

See [`SOURCE-MANIFEST.md`](SOURCE-MANIFEST.md) for the source commit, branch-tip,
pull-request, and original blob records.