# Implemented Automation Architecture

GitHub is authoritative for automation source. AAP 2.7 at `192.168.1.251` is
the operator UI, scheduler, workflow engine, credential store, and audit trail.
It directly manages `MBJ-PRD-ANSIBLE001` at `192.168.1.250` through a dedicated
locked `ansible` account and SSH key.

The RHEL 10 control node runs Community Ansible from
`/opt/automation/runtime/venv`, checks out this repository under
`/opt/automation/repos/techlittlebrawta-lab`, and directly manages all 51
PNETLab nodes over `pnet9` (`10.255.255.0/24`). Its second NIC is attached to
Cloud0 (`192.168.1.0/24`) for AAP, DNS, RHEL, NTP, and GitHub access.

AAP jobs can select only the runner's three allowlisted operations. The runner
validates the request schema, inventory limit, and extra variables; consumes a
mode-0600 transient secret envelope; serializes execution; records Git SHA and
AAP job identifiers; redacts secret values; and returns the actual Ansible exit
status. JSON results live in `/opt/automation/artifacts` and text logs in
`/opt/automation/logs`.

Downstream PNETLab nodes do not exist as AAP hosts. AAP contains one inventory
for the MBJ control node, one project for this repository, machine and custom
downstream credentials, job templates, schedules, and an operational workflow.
