# Operations

Operators launch the AAP workflow or individual MBJ templates. The health job
checks RHEL identity, SELinux, services, both addresses, repository cleanliness,
trusted AAP HTTPS, and GitHub access. Git sync permits fast-forward-only updates
of a clean checkout. Dependency validation uses `pip check` and collection
inventory. Inventory validation checks the generated group graph.

Runner logs are under `/opt/automation/logs`; structured results are under
`/opt/automation/artifacts`. Both include the execution UUID, and result JSON
includes AAP job/workflow IDs and Git SHA. System logging is handled by rsyslog
and runner log retention by the installed logrotate policy.

Patch RHEL through normal approved maintenance, reboot into the newest kernel,
then run the health, dependency, inventory, connectivity, and platform jobs.
Commit source changes before AAP execution so every run is attributable to a
Git revision.
