# Disaster Recovery

Create a replacement from the existing PNETLab RHEL 10 image with the hostname,
sizing, and two-interface addressing in the build document. Register and patch
RHEL, create the locked `ansible` account and automation group, and restore its
AAP public SSH key.

Clone this repository, install the maintenance script, and run `configure`.
Reapply `automation/controller/mbj-community.yml` only if AAP objects were also
lost. Restore protected credentials from the organization secret escrow into
AAP; secrets are intentionally not recoverable from Git.

Run health twice, dependency validation, inventory validation, a controlled
failure, a succeeding read-only run, and the complete workflow. Confirm the
result Git SHA matches the restored branch before returning schedules to service.
