# Rollback

Rollback is Git-based. Disable the two MBJ schedules, identify the last known
good commit from a successful result artifact, and revert the faulty commit on
the repository branch. Run the AAP project update, MBJ Git sync, configure, and
health templates, then execute the full validation workflow.

If the MBJ node itself must be rolled back, restore its persistent PNETLab disk
or rebuild from the documented image while retaining `192.168.1.250` and
`10.255.255.125`. AAP continues managing unrelated systems throughout.

The former direct-PNETLab AAP inventories are not a normal rollback target.
Reintroducing them risks duplicate execution and Host Metrics churn; use the
PNETLab console recovery path while repairing Community Ansible instead.
