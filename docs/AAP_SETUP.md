# AAP + GitHub Operating Baseline

This repository is the reviewed source of truth for Tech Little Brawta lab automation. Red Hat Ansible Automation Platform (AAP) is the execution plane for the private lab network.

## Security boundary

GitHub stores automation code, examples, documentation, and non-secret metadata. AAP stores live management IPs, usernames, passwords, SSH private keys, API credentials, and other environment-specific values.

Do not commit the 192.168.1.0/24 management inventory or credentials to this public repository.

## AAP objects

### Organization

Create `Tech Little Brawta`.

### Project

Create `TLB | Lab Automation` with:

- Organization: `Tech Little Brawta`
- Source control type: Git
- Source control URL: `https://github.com/techlittlebrawta/techlittlebrawta-lab.git`
- Source control branch: `main`
- Clean: enabled
- Delete on update: disabled
- Update revision on launch: disabled
- Allow branch override: disabled

The repository is public, so a source-control credential is not required for read-only synchronization. If it becomes private, use a dedicated read-only GitHub credential rather than a personal administrator token.

### Inventory

Create standard inventory `TLB | Lab` in `Tech Little Brawta` and maintain the live inventory in AAP.

Groups and hosts:

- `aap_control_plane`: `LAB-AAP-CONT-01` -> live `ansible_host` maintained in AAP
- `linux_managed`: `LAB-PNETLAB-01` -> live `ansible_host` maintained in AAP
- `virtualization`: `LAB-ESXI-01` -> live `ansible_host` maintained in AAP
- `juniper`: `LAB-SW-EX2200` -> live `ansible_host` maintained in AAP

Set non-secret service variables:

- `LAB-AAP-CONT-01`: `tlb_preflight_port: 22`
- `LAB-PNETLAB-01`: `tlb_preflight_port: 22`
- `LAB-ESXI-01`: `tlb_preflight_port: 443`
- `LAB-SW-EX2200`: `ansible_port: 830` and `tlb_preflight_port: 830`

NETCONF over SSH must be enabled on the EX2200 before the Junos facts job will work.

## Credentials

Create separate least-privilege credentials; do not reuse one administrator account across platforms.

- `TLB | Linux SSH` — AAP Machine credential for Linux-managed systems.
- `TLB | Junos Automation` — dedicated Junos automation identity using SSH keys and only required Junos permissions.
- `TLB | VMware API` — dedicated ESXi/vSphere API identity when VMware API automation is enabled.
- `TLB | GitHub SCM` — only if the repository becomes private; read-only repository access preferred.

Keep privilege escalation separate from login credentials and use SSH keys instead of passwords where supported.

## Execution environment

Build a dedicated image from `execution-environment.yml` and publish it to private automation hub or another approved registry as `TLB | EE | Network`.

The definition uses Red Hat's Ansible Core 2.18 minimal RHEL 9 execution-environment stream and installs the pinned `juniper.device` collection plus its Python dependencies. Do not use the built-in Core 2.16 execution environment for the current Juniper collection.

Promote immutable image tags through testing rather than running production jobs from an unreviewed `latest` tag.

## Job templates

Create:

1. `TLB | Lab | Preflight`
   - Project: `TLB | Lab Automation`
   - Inventory: `TLB | Lab`
   - Playbook: `playbooks/preflight.yml`
   - Credentials: none
   - Purpose: validate that the selected execution node can reach each management service.

2. `TLB | Linux | Gather Facts`
   - Project: `TLB | Lab Automation`
   - Inventory: `TLB | Lab`
   - Playbook: `playbooks/linux_facts.yml`
   - Credential: `TLB | Linux SSH`
   - Limit: `linux_managed`

3. `TLB | Junos | Gather Facts`
   - Project: `TLB | Lab Automation`
   - Inventory: `TLB | Lab`
   - Playbook: `playbooks/junos_facts.yml`
   - Execution environment: `TLB | EE | Network`
   - Credential: `TLB | Junos Automation`
   - Limit: `juniper`

Do not target the AAP control-plane host from general infrastructure templates. Control-plane maintenance must use dedicated automation and explicit approval.

## Workflow

Create workflow `TLB | Lab | Validate`:

1. Project sync: `TLB | Lab Automation`
2. On success: `TLB | Lab | Preflight`
3. On success: `TLB | Linux | Gather Facts`
4. On success: `TLB | Junos | Gather Facts`

Add ESXi API validation after the VMware credential and approved VMware collection are established.

## RBAC

Prefer team-based access:

- `TLB-AAP-Admins` — platform administration.
- `TLB-Automation-Maintainers` — project/template administration without platform-wide administration.
- `TLB-Automation-Operators` — execute approved templates/workflows only.
- `TLB-Automation-Auditors` — read-only job, inventory, and template access.

## AAP 2.7 Configuration as Code

If `LAB-AAP-CONT-01` is running AAP 2.7, manage supported platform configuration through the `ansible.platform` collection and the platform gateway. Store desired-state YAML in Git, authenticate using a platform-gateway token/credential held by AAP, run in check mode before apply, and keep controller configuration changes behind pull requests.

Do not place a platform gateway token in GitHub Actions or expose the private AAP endpoint to GitHub merely to perform controller configuration.

## Change flow

1. Feature branch.
2. Pull request.
3. YAML/Ansible CI.
4. Code-owner review.
5. Squash merge to `main`.
6. AAP project sync.
7. Run `TLB | Lab | Validate` before higher-risk automation.

GitHub is the source of truth for code; AAP is the source of truth for secrets and live private-network inventory.
