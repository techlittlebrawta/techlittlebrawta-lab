# Security Controls

The MBJ host enforces SELinux and firewalld, uses patched RHEL repositories,
trusts the AAP internal CA, and allows AAP SSH access through a dedicated locked
account. Sudo permits only the root-owned maintenance command and never an
arbitrary shell.

Initial downstream SSH host keys are learned only from the isolated OOB segment
during the AAP configuration job and stored in the locked service account's
`known_hosts`. Subsequent key changes fail closed and require explicit
investigation and replacement.

The Community runner uses argv execution with no shell, a fixed playbook map,
path containment, strict request fields, a conservative inventory-limit regex,
scalar extra-variable limits, file-mode checks, execution locking, secret
redaction, and one-time secret deletion. Unit tests cover traversal, command
injection, unsupported fields, secret handling, and result propagation.

AAP remains the credential and audit authority. Downstream secrets do not enter
Git, AAP surveys, command lines, logs, or result JSON. The public topology is
sanitized. Existing non-PNETLab AAP automation is isolated from the migration
scope and must pass regression validation after controller cleanup.
