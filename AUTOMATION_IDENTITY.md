# Automation identity standard

All managed lab endpoints use the dedicated `tlb-automation` service identity. Human and built-in administrator accounts are break-glass identities and must not be attached to TLB inventories, job templates, workflows, or schedules in Ansible Automation Platform (AAP).

## Authentication boundaries

- Linux and the AAP host use Ed25519 SSH authentication. A unique, randomly generated fallback password remains encrypted in AAP; the account escalates through an audited sudo identity.
- Junos uses a dedicated Network credential over NETCONF or SSH. The EX2200 requires its platform-native legacy password-hash format on the device; the AAP secret itself is a high-entropy random password.
- Standalone ESXi uses separate VMware API and Machine credential objects with the same device-local service identity. This keeps API and SSH attachment explicit in job templates.
- AAP self-management uses a non-superuser platform account assigned only to `TLB-Automation-Maintainers`. The built-in `admin` account is not used by TLB automation.
- GitHub source control uses a read-only deploy key and is not a device identity.

Credential values never belong in Git. They must be entered directly into AAP or supplied by an approved external secret-management integration. Declarative credential objects intentionally omit `inputs` so reconciliation cannot blank or replace encrypted live secrets.

## Operating controls

1. Rotate each trust boundary independently and validate the new credential before removing the old binding.
2. Run `TLB | Identity | Validate Linux`, Junos facts, and VMware discovery after rotation.
3. Review every TLB template and workflow for credentials whose username is not `tlb-automation`; `git` is the sole expected exception for source control.
4. Keep administrator accounts outside AAP as monitored break-glass access. Do not delete the final recovery path from a device.
5. Revoke temporary bootstrap credentials immediately after independent validation.
6. Keep host-key checking enabled and manage trusted host keys through the execution environment or an approved credential-injection control.

## Rotation cadence

Rotate immediately after suspected disclosure, operator departure, or privilege-boundary change. Otherwise review access quarterly and rotate authentication material at least annually, or more frequently when organizational policy requires it. Record the validation job IDs in the change record.
