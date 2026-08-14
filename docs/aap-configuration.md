# AAP Configuration

`automation/controller/mbj-community.yml` is the canonical desired state. Apply
it with `automation/tools/aap_reconcile.py --config` using certificate-validated
controller access and either a short-lived OAuth token or prompted Basic auth.
The SSH key is supplied through `MBJ_AAP_SSH_KEY_FILE` and never stored in Git.

Managed objects include:

- inventory `TLB | MBJ Community Ansible` and host `MBJ-PRD-ANSIBLE001`;
- machine credential `TLB | MBJ Community Ansible SSH`;
- custom credential `TLB | Community Downstream Secret`;
- project `TLB | MBJ Community Automation`;
- configure, health, sync, dependency, inventory, connectivity, platform,
  execution, result, credential-migration, and controlled-failure templates;
- `MBJ Community Ansible - Operational Workflow`;
- six-hour health and hourly Git synchronization schedules.

The reconciler is idempotent and synchronizes the project before creating job
templates. Existing non-PNETLab inventories, projects, templates, schedules,
credentials, and workflows remain outside its scope.
