# Security Policy

## Reporting a vulnerability

Do **not** disclose suspected vulnerabilities, credentials, tokens, private keys, or sensitive infrastructure details in a public issue.

For sensitive security reports, use GitHub's private vulnerability reporting/security advisory workflow for this repository when available, or contact the Tech Little Brawta repository owner privately through an approved organizational channel.

## Secrets

Never commit:
- passwords
- API keys or tokens
- private keys
- cloud credentials
- device credentials
- production configuration containing secrets
- license keys or vendor entitlement files

If a secret is committed, treat it as compromised and rotate/revoke it immediately.

## Automation credentials

- Use the dedicated `tlb-automation` identity for every TLB-managed endpoint and protocol.
- Never attach root, admin, or personal accounts to TLB job templates, workflows, or schedules.
- Prefer asymmetric authentication for SSH and keep protocol credentials in separate AAP credential objects.
- Scope the AAP platform account to the TLB organization; it must not be a platform superuser.
- Preserve a separately controlled break-glass path and validate new credentials before retiring old AAP bindings.
- Never declare live credential `inputs` in this public repository.
- Never grant routine automation unrestricted sudo, Junos `super-user`, or ESXi `Administrator`; use the reviewed platform-specific roles in this repository.
- Require a pull request, CODEOWNERS review, passing automation-quality checks, and an approval-gated AAP workflow for changes.

The full standard is documented in [automation identity](automation/docs/automation-identity.md).
