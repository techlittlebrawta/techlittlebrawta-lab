# AAP + GitHub Operating Baseline

Red Hat Ansible Automation Platform (AAP) is the **only automation, validation, scheduling, orchestration, and execution plane** for the Tech Little Brawta lab. GitHub is passive source storage and version history only.

## Non-negotiable execution boundary

GitHub must not run automation for this repository. Do not configure GitHub Actions, Dependabot automation, GitHub-hosted runners, self-hosted GitHub runners, repository-dispatch jobs, deployment workflows, scheduled GitHub workflows, or GitHub webhooks that trigger AAP.

AAP initiates all SCM synchronization and all lab activity. GitHub never needs a route to AAP or to the private management network.

## Security boundary

GitHub stores automation code, examples, documentation, and non-secret metadata. AAP stores live management IPs, usernames, passwords, SSH private keys, API credentials, and other environment-specific values.

Do not commit the live `192.168.1.0/24` management inventory or credentials to this public repository.

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
- Update Revision on Launch: enabled
- Allow Branch Override: disabled
- SCM credential: none while the repository remains public

`Update Revision on Launch` is intentionally enabled because **AAP**, not GitHub, must initiate synchronization. Do not configure a webhook on this project.

If the repository becomes private, create a dedicated read-only SCM credential in AAP scoped only to this repository. Do not use a personal organization-administrator token.

### Inventory

Create standard inventory `TLB | Lab` in `Tech Little Brawta`. Maintain the live host addresses only in AAP.

Groups and hosts:

- `aap_control_plane`: `LAB-AAP-CONT-01`
- `linux_managed`: `LAB-PNETLAB-01`
- `virtualization`: `LAB-ESXI-01`
- `juniper`: `LAB-SW-EX2200`

Enter each host's real `ansible_host` in AAP, not GitHub.

Set non-secret service variables in AAP:

- `LAB-AAP-CONT-01`: `tlb_preflight_port: 22`
- `LAB-PNETLAB-01`: `tlb_preflight_port: 22`
- `LAB-ESXI-01`: `tlb_preflight_port: 443`
- `LAB-SW-EX2200`: `ansible_port: 830` and `tlb_preflight_port: 830`

NETCONF over SSH must be enabled on the EX2200 before Junos automation will work.

## Credentials

Create separate least-privilege credentials in AAP. Do not reuse one administrator identity across platforms.

- `TLB | Linux SSH` — AAP Machine credential for Linux-managed systems.
- `TLB | Junos Automation` — dedicated Junos automation identity using SSH keys and only required Junos permissions.
- `TLB | VMware API` — dedicated ESXi/vSphere API identity when VMware API automation is enabled.
- `TLB | GitHub SCM` — only if the repository becomes private; read-only repository access.

Keep privilege escalation separate from login credentials and use SSH keys instead of passwords where supported.

## Execution environment

Build a dedicated image from `execution-environment.yml` and publish it to private automation hub or another approved registry as `TLB | EE | Network`.

The image contains the Ansible/Juniper runtime plus `ansible-lint` and `yamllint`, because repository validation is executed by AAP rather than GitHub.

Promote immutable image tags through testing rather than running important jobs from an unreviewed `latest` tag.

## Job templates

Create the following templates.

### 1. TLB | Repository | Validate

- Project: `TLB | Lab Automation`
- Inventory: `TLB | Lab`
- Playbook: `playbooks/repository_validate.yml`
- Execution environment: `TLB | EE | Network`
- Credentials: none
- Purpose: run YAML linting, Ansible linting, and syntax checks inside AAP before lab execution

Although the AAP inventory is attached to the template for controller consistency, this validation playbook targets `localhost` inside the execution environment and does not connect to lab hosts.

### 2. TLB | Lab | Preflight

- Project: `TLB | Lab Automation`
- Inventory: `TLB | Lab`
- Playbook: `playbooks/preflight.yml`
- Credentials: none
- Purpose: validate that the selected AAP execution node can reach each required management service

### 3. TLB | Linux | Gather Facts

- Project: `TLB | Lab Automation`
- Inventory: `TLB | Lab`
- Playbook: `playbooks/linux_facts.yml`
- Credential: `TLB | Linux SSH`
- Limit: `linux_managed`

### 4. TLB | Junos | Gather Facts

- Project: `TLB | Lab Automation`
- Inventory: `TLB | Lab`
- Playbook: `playbooks/junos_facts.yml`
- Execution environment: `TLB | EE | Network`
- Credential: `TLB | Junos Automation`
- Limit: `juniper`

Do not target the AAP control-plane host from general infrastructure templates. Control-plane maintenance must use dedicated automation and explicit approval.

## AAP workflow

Create workflow `TLB | Lab | Validate` with the following success path:

1. **Project Sync — `TLB | Lab Automation`**
2. **`TLB | Repository | Validate`**
3. **`TLB | Lab | Preflight`**
4. **`TLB | Linux | Gather Facts`**
5. **`TLB | Junos | Gather Facts`**

Every node is launched by AAP. A failure at any validation or preflight node must prevent downstream execution.

Add ESXi API validation after the VMware credential and approved VMware automation implementation are established.

## Scheduling

Any recurring automation must be scheduled in AAP only.

Examples:

- periodic project synchronization;
- inventory validation;
- configuration backups;
- compliance checks;
- fact collection;
- patching or maintenance workflows.

Do not reproduce an AAP schedule in GitHub.

## RBAC

Prefer team-based access:

- `TLB-AAP-Admins` — platform administration.
- `TLB-Automation-Maintainers` — project/template administration without platform-wide administration.
- `TLB-Automation-Operators` — execute approved templates/workflows only.
- `TLB-Automation-Auditors` — read-only job, inventory, and template access.

Use separate credentials and execution permissions so operators can launch approved jobs without viewing the underlying secrets.

## AAP Configuration as Code

Where supported by the installed AAP version, manage controller/platform desired state with the supported Red Hat configuration collection. Store the non-secret desired-state content in GitHub, but **execute the configuration from AAP** with platform credentials held only by AAP.

Run controller configuration in check mode before apply when the module supports it. Never place an AAP platform token in GitHub and never expose the AAP API to GitHub automation.

## Approved change and execution flow

1. Store or update approved automation content in GitHub.
2. Launch the AAP workflow or AAP job template.
3. AAP pulls the selected `main` revision from GitHub.
4. AAP runs `TLB | Repository | Validate`.
5. AAP runs `TLB | Lab | Preflight`.
6. AAP performs the approved lab automation.
7. AAP retains the job events, status, output, and audit history.

The architecture is intentionally one-way from the automation plane: **AAP pulls from GitHub; GitHub never pushes into AAP.**
