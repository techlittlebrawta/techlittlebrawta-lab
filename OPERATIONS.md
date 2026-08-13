# Governed infrastructure operations

## Control model

Git is the reviewed source of truth; AAP is the only normal execution plane. Job templates pin project, inventory, execution environment, credential, limit, timeout, and playbook. Operators cannot substitute credentials, arbitrary variables, limits, or SCM branches.

Routine controller reconciliation runs as the resource-scoped `tlb-automation` account and deliberately skips organization, team, and gateway-role bootstrap. Set `tlb_reconcile_identity_boundary=true` only in a separately approved bootstrap session using an Organization Editor credential; never grant that role permanently to the routine service identity.

Changes follow this sequence:

1. Merge a reviewed pull request after required CI passes.
2. Synchronize the AAP project to the immutable merged revision.
3. Run a read-only audit and retain the job ID.
4. Confirm backup freshness, recovery access, vendor support, and the maintenance window.
5. Approve the AAP workflow.
6. Apply changes serially and stop on the first failure.
7. Run post-change validation and attach its job ID to the change record.

Configure GitHub `main` protection to require pull requests, CODEOWNERS review, the `Lint and syntax check` status, resolved conversations, linear history, signed commits where supported, and administrator enforcement. Prohibit force pushes and deletion. Enable secret scanning, push protection, dependency alerts, and Dependabot security updates.

## Linux security updates

- `TLB | Linux | Patch Audit` runs daily without root and records distribution, kernel, available updates, Ubuntu Pro visibility, policy, and reboot state.
- `TLB | Linux | Governed Security Maintenance` starts weekly but cannot modify a host until an operator approves the workflow after checking backups and vendor compatibility.
- `TLB | Linux | Apply Security Updates` runs one host at a time and invokes only the root-owned `/usr/local/sbin/tlb-linux-maintenance patch-security` interface.
- RPM hosts apply vendor security advisories through DNF. Debian/Ubuntu hosts use `unattended-upgrade`, restricting changes to configured security origins. Appliance compatibility remains an explicit approval responsibility.
- Reboots are reported but never automatic. Use a separate outage-approved reboot workflow after dependency and recovery checks.

Critical updates should be reviewed within 24 hours and deployed within 72 hours when vendor-supported. Other security updates have a 30-day maximum SLA. Exceptions require an owner, compensating controls, and expiry.

## Least privilege

Linux grants `tlb-automation` passwordless access only to four exact subcommands of a root-owned helper. Arbitrary `sudo` is denied and terminal I/O is logged by sudo. Updating the helper or sudo policy requires the separately controlled console break-glass path and another reviewed bootstrap run.

Junos maps `tlb-automation` to `tlb-aap-operator`, which permits operational reads and configuration only under `system ntp`. Changes use commit-confirmed rollback protection. The unsupported EX2200 limits available cryptographic and authorization controls; replacement remains mandatory.

ESXi maps `tlb-automation` to `TLB Automation Time Operator`, containing read, time-settings, service-control, and license-management privileges. The legacy scheduled SSH Administrator license job is disabled. Root remains outside AAP as monitored break-glass.

Run `TLB | Identity | Validate Least Privilege` after every credential, role, sudo, or device-software change. Access reviews are quarterly.

## Time integrity

The two Linux hosts synchronize from three independent external sources and provide NTP only to the private management network. ESXi and Junos use both Linux hosts, avoiding dependence on Internet routing from appliance management planes.

`TLB | Time | Audit` runs every six hours. `TLB | Time | Governed Remediation` requires approval because a large clock correction can affect authentication, logs, databases, and certificates. All systems use UTC internally; presentation time zones belong at the user interface or reporting layer.

The VMware certificate is not yet trusted, so the inventory explicitly documents a temporary validation exception. Replace the default certificate and set `tlb_vmware_validate_certs: true`; this exception must not become permanent.

## Recovery and evidence

Before privilege or time changes, confirm console/DCUI access and current encrypted off-device configurations. Keep AAP job events, approval actor, Git commit SHA, device commit comment, package transaction logs, sudo I/O logs, and validation results in the central audit system. Test the break-glass path and representative restore quarterly.
