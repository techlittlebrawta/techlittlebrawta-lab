# MBJ Community Ansible Build

The persistent PNETLab node is `MBJ-PRD-ANSIBLE001`, node ID 25, built from the
existing `linux-rhel-10.2` image with 4 vCPU, 8 GiB RAM, and 40 GiB disk.

Networking is persistent:

- `ens3`: Cloud0/pnet0, `192.168.1.250/24`, default gateway and DNS
  `192.168.1.1`.
- `ens4`: pnet9, `10.255.255.125/24`, no default route.

RHEL BaseOS and AppStream provide the system packages. The runtime uses a
Python virtual environment and the pinned files `requirements.txt` and
`collections/requirements.yml`. SELinux is enforcing; firewalld, sshd,
chronyd, and rsyslog are enabled. Root remote password login is disabled. AAP
uses the locked `ansible` account and a dedicated SSH key.

Rebuild from a registered RHEL 10 image by assigning the two interfaces above,
installing the required system packages, creating `ansible:automation`, cloning
this branch, and installing `automation/files/mbj-control-maintenance` as
`/usr/local/sbin/mbj-control-maintenance`. Run its `configure` action as root.
The action creates the directory permissions, Python environment, collections,
runner, sudo policy, log rotation, AAP CA trust, and repository checkout.

Validate with `automation/playbooks/community_control_node_health.yml`; a
second configuration run must complete without configuration drift.
