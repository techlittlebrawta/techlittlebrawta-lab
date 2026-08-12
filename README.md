# techlittlebrawta-lab

Public Tech Little Brawta lab catalog, reproducible lab organization, and approved automation content.

## Operating model

Red Hat Ansible Automation Platform (AAP) is the **only automation and execution plane** for this lab. GitHub is passive source storage and version history only.

GitHub must not:

- run GitHub Actions or any CI/CD workflow;
- run Dependabot automation for this repository;
- use webhooks to trigger AAP;
- schedule automation;
- deploy anything;
- hold lab credentials;
- receive a network path to the private lab;
- initiate connections to AAP or any lab host.

AAP is responsible for:

- pulling the repository over outbound HTTPS;
- validating repository content;
- storing live inventory and credentials;
- scheduling approved automation;
- running preflight checks;
- executing all changes and read operations against lab systems.

## Repository contents

- `ansible.cfg` — repository Ansible defaults.
- `collections/requirements.yml` — required Ansible collections.
- `execution-environment.yml` — AAP execution-environment definition.
- `requirements.txt` — Python dependencies used by the AAP execution environment.
- `inventories/lab/inventory.example.yml` — public inventory shape only; no management IPs or credentials.
- `playbooks/repository_validate.yml` — repository quality validation executed by AAP.
- `playbooks/preflight.yml` — management-plane reachability validation executed by AAP.
- `playbooks/linux_facts.yml` — Linux fact gathering executed by AAP.
- `playbooks/junos_facts.yml` — Juniper Junos fact gathering over NETCONF executed by AAP.
- `docs/AAP_SETUP.md` — AAP project, inventory, credentials, RBAC, templates, and workflow baseline.
- `docs/GITHUB_BASELINE.md` — passive-storage boundary for GitHub.

AAP must store the live host addressing and credentials. Do not add them to this public repository.

## Change and execution flow

1. Automation content is stored in GitHub.
2. AAP initiates the project sync from GitHub.
3. AAP runs `TLB | Repository | Validate`.
4. AAP runs `TLB | Lab | Preflight`.
5. AAP runs the approved job or workflow.
6. AAP retains the execution history and job output.

There are no GitHub-triggered automation steps in this flow.

## Ownership

This repository is maintained by the **Tech Little Brawta** organization.

## Security

Do not commit credentials, API keys, tokens, private keys, passwords, certificates containing private keys, private management inventory, or other secrets.

See [SECURITY.md](SECURITY.md) and [PUBLIC_REPOSITORY_POLICY.md](PUBLIC_REPOSITORY_POLICY.md).
