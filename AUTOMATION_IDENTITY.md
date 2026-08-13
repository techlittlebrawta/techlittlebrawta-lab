# Automation identity standard

All managed lab endpoints use the dedicated `tlb-automation` service identity. Human and built-in administrator accounts are break-glass identities and must not be attached to TLB inventories, job templates, workflows, or schedules in Ansible Automation Platform (AAP).

## Authentication boundaries

- Linux and the AAP host use Ed25519 SSH authentication. The account is non-root and may invoke only exact subcommands of the root-owned `tlb-linux-maintenance` helper; arbitrary sudo is denied.
- Junos uses a dedicated Network credential over NETCONF. The identity is mapped to the `tlb-aap-operator` command class, not `super-user`, and may change only the NTP hierarchy.
- Standalone ESXi automation uses the VMware API with the `TLB Automation Time Operator` custom role. Routine templates do not attach the ESXi SSH credential.
- AAP self-management uses a non-superuser platform account assigned only to `TLB-Automation-Maintainers`. The built-in `admin` account is not used by TLB automation.
- GitHub source control uses a read-only deploy key and is not a device identity.

Credential values never belong in Git. They must be entered directly into AAP or supplied by an approved external secret-management integration. Declarative credential objects intentionally omit `inputs` so reconciliation cannot blank or replace encrypted live secrets.

## Operating controls

1. Rotate each trust boundary independently and validate the new credential before removing the old binding.
2. Run `TLB | Identity | Validate Least Privilege`, the time audit, Junos facts, and VMware discovery after rotation.
3. Review every TLB template and workflow for credentials whose username is not `tlb-automation`; `git` is the sole expected exception for source control.
4. Keep administrator accounts outside AAP as monitored break-glass access. Do not delete the final recovery path from a device.
5. Revoke temporary bootstrap credentials immediately after independent validation.
6. Keep host-key checking enabled and manage trusted host keys through the execution environment or an approved credential-injection control.
7. Run privilege-changing jobs only through the approval-gated workflow after verifying console recovery and an off-device configuration backup.

## Rotation cadence

Rotate immediately after suspected disclosure, operator departure, or privilege-boundary change. Otherwise review access quarterly and rotate authentication material at least annually, or more frequently when organizational policy requires it. Record the validation job IDs in the change record.
