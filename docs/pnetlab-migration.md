# PNETLab Migration

The canonical source inventory is `automation/inventories/lab/hosts.yml`.
`automation/tools/build_community_inventory.py` mechanically produces the
direct inventory at `automation/inventories/pnetlab/hosts.yml`. It maps each of
the 51 node records to its `10.255.255.x` OOB address and retains site, role,
platform, and vendor groups.

The migration changes the control path from AAP through PNETLab proxy ports to
Community Ansible directly over pnet9. It does not alter production topology
connections. The sanitized persistent topology is
`pnetlab/topologies/tech-little-brawta-lab.unl`.

After direct Community validation, legacy AAP PNETLab hosts and inventory
sources are deleted. Host Metrics for those deleted hosts are cleaned only after
confirming they are not used by non-PNETLab automation. Re-running the source
generator and AAP reconciliation cannot recreate downstream nodes in AAP.
