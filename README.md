# techlittlebrawta-lab

Public Tech Little Brawta lab catalog, reproducible lab organization, and approved automation content.

## Automation architecture

Red Hat Ansible Automation Platform (AAP) is the private-network execution plane. GitHub is the source of truth for reviewed automation code.

- `ansible.cfg` — repository Ansible defaults.
- `collections/requirements.yml` — required Ansible collections.
- `inventories/lab/inventory.example.yml` — public inventory shape only; no management IPs or credentials.
- `playbooks/preflight.yml` — management-plane reachability validation.
- `playbooks/linux_facts.yml` — Linux managed-node fact gathering.
- `playbooks/junos_facts.yml` — Juniper Junos fact gathering over NETCONF.
- `docs/AAP_SETUP.md` — AAP project, inventory, credentials, RBAC, templates, and workflow baseline.
- `docs/GITHUB_BASELINE.md` — repository protection and security baseline.

AAP must store the live host addressing and credentials. Do not add them to this public repository.

## Change management

Automation changes should be made on a feature branch, validated by GitHub Actions, reviewed through a pull request, and squash-merged to `main`. AAP should consume `main` as its stable project branch.

## Ownership

This repository is maintained by the **Tech Little Brawta** organization.

## Security

Do not commit credentials, API keys, tokens, private keys, passwords, certificates containing private keys, private management inventory, or other secrets.

See [SECURITY.md](SECURITY.md) and [PUBLIC_REPOSITORY_POLICY.md](PUBLIC_REPOSITORY_POLICY.md).
