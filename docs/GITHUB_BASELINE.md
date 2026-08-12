# GitHub Repository Protection Baseline

The repository should use GitHub rulesets and native security controls to protect `main`.

## Main branch ruleset

Target the default branch and enforce:

- Require a pull request before merging.
- Require at least one approval.
- Require review from Code Owners.
- Dismiss stale approvals when new commits are pushed.
- Require all review conversations to be resolved.
- Require the `ansible-ci` status check to pass.
- Require branches to be up to date before merge when supported by the selected status-check configuration.
- Require linear history.
- Block force pushes.
- Block branch deletion.
- Do not permit routine bypasses; reserve bypass for organization administrators for break-glass recovery.

The repository already uses squash merging as its only merge strategy. Keep that setting.

## Security controls

- Keep GitHub secret scanning enabled.
- Enable repository push protection when the organization plan supports it.
- Keep the repository free of credentials, tokens, SSH private keys, private certificates, and sensitive environment inventory.
- Use Dependabot for GitHub Actions updates.
- Keep workflow permissions read-only unless a workflow explicitly requires write access.
- Pin third-party actions to reviewed versions or immutable commit SHAs for higher-assurance workflows.

## Access

- Grant access through organization teams rather than ad-hoc collaborators where possible.
- Keep administrator membership small.
- Require multi-factor authentication at the organization level.
- Prefer GitHub Apps or fine-grained credentials scoped to the minimum repository permissions needed by automation.

## AAP integration

AAP should pull this repository over outbound HTTPS. GitHub Actions must not be given a path or credentials to reach the private lab network. Private-lab execution belongs in AAP execution environments and instance groups.
