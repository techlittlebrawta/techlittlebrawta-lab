# Adding Nodes

Add the node to `automation/inventories/lab/hosts.yml` with a unique hostname,
OOB address, protocol, template, site, role, and vendor group. Configure its OOB
interface on pnet9 and ensure the platform uses the AAP-managed downstream
credential or an explicitly added platform credential design.

Regenerate `automation/inventories/pnetlab/hosts.yml`, run inventory and YAML
validation, and execute the read-only Community playbook limited to the new
host. Commit and push both inventory changes. The existing AAP project and
workflow then operate the node without adding it to an AAP inventory.
