# GitHub Passive Storage Baseline

GitHub is passive source storage and version history for `techlittlebrawta-lab`. It is **not** an automation, validation, scheduling, orchestration, deployment, or execution platform for this lab.

## Allowed role

GitHub may:

- store approved source code, configuration examples, documentation, and non-secret metadata;
- retain source history;
- serve repository content to AAP when AAP initiates an outbound SCM synchronization.

## Prohibited automation

Do not configure or use the following for this repository:

- GitHub Actions workflows;
- GitHub-hosted or self-hosted Actions runners;
- Dependabot automation;
- GitHub deployment workflows or environments as an execution mechanism;
- GitHub scheduled workflows;
- repository dispatch automation;
- GitHub webhooks that trigger AAP;
- GitHub automation that calls the AAP API;
- GitHub automation that connects to the private lab network.

GitHub must never possess credentials that provide access to AAP or the private lab solely for automation purposes.

## AAP integration

AAP owns every automated action:

1. AAP initiates the SCM project synchronization over outbound HTTPS/443.
2. AAP validates the synchronized repository content.
3. AAP performs management-plane preflight checks.
4. AAP executes approved playbooks and workflows.
5. AAP stores job history and execution output.

Do not configure a GitHub webhook for the AAP project. Project synchronization must be manual, scheduled from AAP, or performed by AAP through `Update Revision on Launch`.

## Repository security boundary

- Do not store credentials, tokens, SSH private keys, private certificates, or live private-management inventory in GitHub.
- Keep the real lab inventory and all credentials in AAP.
- AAP requires only outbound access to GitHub; GitHub requires no inbound route to AAP or the lab.
- If the repository becomes private, use an AAP-held read-only SCM credential scoped only to this repository.

This boundary is intentional: **GitHub stores; AAP acts.**
