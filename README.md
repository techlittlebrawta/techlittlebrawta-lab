# techlittlebrawta-lab

Public Tech Little Brawta lab catalog and reproducible lab organization.

## Ownership

This repository is maintained by the **Tech Little Brawta** organization.

## Security

Do not commit credentials, API keys, tokens, private keys, passwords, certificates containing private keys, or other secrets.

See [SECURITY.md](SECURITY.md) for vulnerability reporting guidance.

## Automation identity

AAP-managed devices use the dedicated `tlb-automation` service identity. Built-in administrator accounts are retained only as out-of-band break-glass access and are not attached to TLB automation objects.

See [automation identity](automation/docs/automation-identity.md) for credential boundaries, validation, and rotation controls.

## Operations

Linux security updates, cross-platform time integrity, least privilege, AAP schedules, approvals, recovery gates, and GitHub controls are defined in [automation operations](automation/docs/operations.md).

## MBJ Community Ansible

AAP remains the operator interface and directly manages `MBJ-PRD-ANSIBLE001` at
`192.168.1.250`. That RHEL 10 control node directly manages the 51 PNETLab
appliances over the isolated `10.255.255.0/24` OOB network. GitHub is the source
of truth for inventory, playbooks, controller desired state, and the constrained
execution boundary.

Start with [architecture](docs/architecture.md), [operations](docs/operations.md),
and [disaster recovery](docs/disaster-recovery.md). The canonical controller
objects are in `automation/controller/mbj-community.yml`.
